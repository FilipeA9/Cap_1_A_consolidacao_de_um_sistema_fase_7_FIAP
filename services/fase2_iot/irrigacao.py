"""
FarmTech Solutions - Fase 2 - Simulador do sistema de irrigacao inteligente.

Replica em Python a MESMA logica de decisao do firmware sketch.ino do ESP32
(NPK por botoes, pH simulado por LDR 0-4095, umidade DHT22, rele da bomba),
permitindo que a dashboard e a CLI executem ciclos de leitura sem o
hardware/Wokwi, gravando cada ciclo na tabela `eventos_irrigacao`.

O firmware original permanece em services/fase2_iot/sketch.ino e pode ser
executado no Wokwi (diagram.json incluso) - o codigo '0'/'1' do clima
continua compativel com o Monitor Serial.
"""

import random
import sys
import os
from typing import Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import (
    UMIDADE_MINIMA_ESP32, PH_LDR_MINIMO, PH_LDR_MAXIMO,
)
from services.fase3_banco.db_manager import DatabaseManager


def ler_sensores_simulados(forcar: Optional[Dict] = None) -> Dict:
    """Gera uma leitura no estilo do ESP32. `forcar` permite fixar valores
    (usado pelos controles interativos da dashboard)."""
    leitura = {
        'umidade': round(random.uniform(35.0, 90.0), 1),   # DHT22 (%)
        'ph_ldr': random.randint(800, 3500),               # LDR (0-4095)
        'nivel_n': random.random() < 0.7,                  # botoes NPK
        'nivel_p': random.random() < 0.7,
        'nivel_k': random.random() < 0.7,
        'previsao_chuva': False,                           # codigo serial '0'/'1'
    }
    if forcar:
        leitura.update(forcar)
    return leitura


def decidir_irrigacao(leitura: Dict) -> Dict:
    """Mesma logica do sketch.ino: liga a bomba apenas se TODAS as condicoes
    forem favoraveis."""
    motivos = []

    umidade_baixa = leitura['umidade'] < UMIDADE_MINIMA_ESP32
    if not umidade_baixa:
        motivos.append(f"umidade adequada ({leitura['umidade']:.1f}%)")

    npk_ok = leitura['nivel_n'] and leitura['nivel_p'] and leitura['nivel_k']
    if not npk_ok:
        faltando = [n for n, v in [('N', leitura['nivel_n']),
                                   ('P', leitura['nivel_p']),
                                   ('K', leitura['nivel_k'])] if not v]
        motivos.append(f"nutrientes ausentes: {','.join(faltando)}")

    ph_ok = PH_LDR_MINIMO <= leitura['ph_ldr'] <= PH_LDR_MAXIMO
    if not ph_ok:
        motivos.append(f"pH fora da faixa ideal (LDR={leitura['ph_ldr']})")

    sem_chuva = not leitura['previsao_chuva']
    if not sem_chuva:
        motivos.append("chuva prevista (codigo 0 recebido)")

    bomba_ligada = umidade_baixa and npk_ok and ph_ok and sem_chuva
    motivo = ("condicoes ideais para irrigar" if bomba_ligada
              else "; ".join(motivos))

    return {**leitura, 'bomba_ligada': bomba_ligada, 'motivo': motivo}


def executar_ciclo(db: DatabaseManager = None,
                   forcar: Optional[Dict] = None,
                   fonte: str = 'simulador') -> Dict:
    """Executa um ciclo completo (leitura -> decisao -> persistencia)."""
    db = db or DatabaseManager()
    evento = decidir_irrigacao(ler_sensores_simulados(forcar))
    evento['fonte'] = fonte
    db.inserir_evento_irrigacao(evento)
    return evento


def executar_cli(ciclos: int = 5):
    """Versao para terminal (python main.py simular --ciclos N)."""
    print("=" * 60)
    print(f"SIMULADOR DE IRRIGACAO (ESP32) - {ciclos} ciclos")
    print("=" * 60)
    db = DatabaseManager()

    # Integra com o servico de clima da propria Fase 2, se configurado
    previsao_chuva = False
    try:
        from services.fase2_iot import integracao_clima
        rec = integracao_clima.executar()
        if rec is not None:
            previsao_chuva = rec['suspender_irrigacao']
            print(f"Clima integrado: {rec['motivo']} "
                  f"(codigo ESP32 = {rec['codigo_esp32']})")
    except Exception:
        pass

    for i in range(1, ciclos + 1):
        evento = executar_ciclo(db, forcar={'previsao_chuva': previsao_chuva})
        estado = "LIGADA" if evento['bomba_ligada'] else "desligada"
        print(f"[{i}] umidade={evento['umidade']:.1f}% "
              f"pH(LDR)={evento['ph_ldr']} "
              f"NPK={int(evento['nivel_n'])}{int(evento['nivel_p'])}{int(evento['nivel_k'])} "
              f"-> bomba {estado} | {evento['motivo']}")
    print("\nCiclos gravados na tabela eventos_irrigacao.")


if __name__ == "__main__":
    executar_cli()
