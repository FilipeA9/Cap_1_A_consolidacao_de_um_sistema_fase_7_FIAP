"""
FarmTech Solutions - Fase 7 - Motor de alertas.

Aplica as regras definidas pelo grupo sobre os dados das Fases 1/2 (IoT),
4 (previsoes ML) e 6 (visao computacional), conforme tabela do README.
Cada alerta e gravado na tabela `alertas` e publicado no AWS SNS
(e-mail/SMS aos funcionarios) com a acao corretiva correspondente.

Idempotencia: um mesmo tipo de alerta nao e repetido dentro de uma janela
de 30 minutos (controle pela tabela `alertas`).

Execucao: python main.py alertas
"""

import sys
import os
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import (
    UMIDADE_MINIMA_ESP32, PH_LDR_MINIMO, PH_LDR_MAXIMO,
    UMIDADE_SOLO_CRITICA, PH_SOLO_MINIMO, PH_SOLO_MAXIMO,
)
from services.fase3_banco.db_manager import DatabaseManager
from services.alertas import sns_publisher

JANELA_DEDUP_MIN = 30


def _emitir(db: DatabaseManager, origem: str, tipo: str, severidade: str,
            detalhe: str, acao: str) -> Dict:
    """Grava o alerta no banco e publica no SNS (se configurado)."""
    if db.existe_alerta_recente(tipo, JANELA_DEDUP_MIN):
        return {'tipo': tipo, 'status': 'suprimido (duplicado na janela)'}

    mensagem = sns_publisher.formatar_mensagem(origem, tipo, severidade,
                                               detalhe, acao)
    enviado, info = sns_publisher.publicar(
        f"[FarmTech][{severidade.upper()}] {tipo.replace('_', ' ')}", mensagem)

    db.inserir_alerta(origem=origem, tipo=tipo, severidade=severidade,
                      mensagem=detalhe, acao_corretiva=acao,
                      enviado_sns=enviado,
                      sns_message_id=info if enviado else None)
    return {'tipo': tipo, 'severidade': severidade, 'detalhe': detalhe,
            'acao': acao, 'enviado_sns': enviado, 'info': info,
            'status': 'enviado' if enviado else 'registrado (SNS nao configurado)'}


def verificar_iot(db: DatabaseManager = None) -> List[Dict]:
    """Regras sobre o ultimo evento do sistema de irrigacao (Fase 2)."""
    db = db or DatabaseManager()
    eventos = db.obter_eventos_irrigacao(limite=1)
    alertas = []
    if eventos.empty:
        return alertas
    ev = eventos.iloc[0]

    if ev['umidade'] is not None and ev['umidade'] == ev['umidade']:  # not NaN
        if float(ev['umidade']) < UMIDADE_MINIMA_ESP32:
            alertas.append(_emitir(
                db, 'iot_fase2', 'umidade_critica', 'alta',
                f"Umidade do solo em {float(ev['umidade']):.1f}% "
                f"(minimo ideal para o cafe: {UMIDADE_MINIMA_ESP32:.0f}%).",
                "Verificar funcionamento da bomba de irrigacao e acionar "
                "irrigacao manual no talhao monitorado, se necessario."))

    if ev['ph_ldr'] is not None and ev['ph_ldr'] == ev['ph_ldr']:
        ph = int(ev['ph_ldr'])
        if not (PH_LDR_MINIMO <= ph <= PH_LDR_MAXIMO):
            corretivo = ("aplicar calcario dolomitico (corrigir acidez)"
                         if ph < PH_LDR_MINIMO
                         else "aplicar enxofre elementar (reduzir alcalinidade)")
            alertas.append(_emitir(
                db, 'iot_fase2', 'ph_fora_da_faixa', 'media',
                f"pH (escala LDR) em {ph}, fora da faixa ideal "
                f"{PH_LDR_MINIMO}-{PH_LDR_MAXIMO} para o cafe.",
                f"Coletar amostra de solo para confirmacao e {corretivo}."))

    npk = [ev['nivel_n'], ev['nivel_p'], ev['nivel_k']]
    if all(v is not None and v == v for v in npk) and not all(map(bool, map(int, npk))):
        faltando = [n for n, v in zip('NPK', npk) if not int(v)]
        alertas.append(_emitir(
            db, 'iot_fase2', 'deficiencia_nutrientes', 'media',
            f"Sensores indicam ausencia dos nutrientes: {', '.join(faltando)}.",
            "Aplicar fertilizante NPK conforme recomendacao do sistema da "
            "Fase 4 (pagina Previsoes ML da dashboard)."))

    if ev['previsao_chuva'] is not None and int(ev['previsao_chuva']):
        alertas.append(_emitir(
            db, 'clima_fase2', 'chuva_prevista', 'baixa',
            "Previsao de chuva nas proximas 24h - irrigacao suspensa "
            "automaticamente pelo sistema.",
            "Manter bombas desligadas para economia de agua e energia; "
            "reavaliar apos a chuva."))
    return alertas


def verificar_sensores_fase4(db: DatabaseManager = None) -> List[Dict]:
    """Regras sobre a ultima leitura dos sensores simulados (Fases 1/4)."""
    db = db or DatabaseManager()
    leituras = db.obter_leituras_recentes(limite=1)
    alertas = []
    if leituras.empty:
        return alertas
    lt = leituras.iloc[0]

    if float(lt['umidade_solo']) < UMIDADE_SOLO_CRITICA:
        alertas.append(_emitir(
            db, 'sensores_fase4', 'estresse_hidrico', 'alta',
            f"Umidade do solo em {float(lt['umidade_solo']):.1f}% "
            f"(limite critico: {UMIDADE_SOLO_CRITICA:.0f}%) no sensor "
            f"{int(lt['sensor_id'])}.",
            "Programar irrigacao imediata de ~30mm no talhao do sensor."))

    ph = float(lt['ph_solo'])
    if not (PH_SOLO_MINIMO <= ph <= PH_SOLO_MAXIMO):
        corretivo = ("calcario dolomitico" if ph < PH_SOLO_MINIMO
                     else "enxofre elementar")
        alertas.append(_emitir(
            db, 'sensores_fase4', 'ph_solo_inadequado', 'media',
            f"pH do solo em {ph:.2f}, fora da faixa ideal "
            f"{PH_SOLO_MINIMO}-{PH_SOLO_MAXIMO}.",
            f"Aplicar {corretivo} conforme dosagem sugerida na pagina "
            "Previsoes ML."))
    return alertas


def verificar_visao(db: DatabaseManager = None) -> List[Dict]:
    """Regras sobre as deteccoes recentes da visao computacional (Fase 6)."""
    db = db or DatabaseManager()
    det = db.obter_deteccoes_visao(limite=20)
    alertas = []
    if det.empty:
        return alertas

    garrafas = det[det['classe'] == 'garrafa']
    if not garrafas.empty:
        imgs = ", ".join(sorted(garrafas['imagem'].unique())[:5])
        alertas.append(_emitir(
            db, 'visao_fase6', 'objeto_estranho_lavoura', 'media',
            f"{len(garrafas)} objeto(s) estranho(s) (garrafas/descarte "
            f"irregular) detectados pela visao computacional. Imagens: {imgs}.",
            "Enviar equipe de limpeza ao talhao para remocao dos residuos "
            "(risco de contaminacao e dano a colheitadeira)."))
    return alertas


def executar_todas_verificacoes(db: DatabaseManager = None) -> List[Dict]:
    db = db or DatabaseManager()
    resultados = []
    resultados += verificar_iot(db)
    resultados += verificar_sensores_fase4(db)
    resultados += verificar_visao(db)
    return resultados


def executar_cli():
    print("=" * 60)
    print("MOTOR DE ALERTAS (Fase 7) - regras sobre Fases 2, 4 e 6")
    print("=" * 60)
    if not sns_publisher.sns_configurado():
        print("AVISO: SNS nao configurado - alertas serao apenas registrados "
              "no banco.\nConfigure SNS_TOPIC_ARN no .env "
              "(ver docs/aws/passo_a_passo_sns.md).\n")
    resultados = executar_todas_verificacoes()
    if not resultados:
        print("Nenhuma condicao de alerta encontrada. Tudo dentro do esperado.")
        return
    for r in resultados:
        print(f"- [{r.get('severidade', '-')}] {r['tipo']}: {r['status']}")
    print(f"\n{len(resultados)} alerta(s) processado(s). "
          "Historico na pagina 'Alertas AWS' da dashboard.")


if __name__ == "__main__":
    executar_cli()
