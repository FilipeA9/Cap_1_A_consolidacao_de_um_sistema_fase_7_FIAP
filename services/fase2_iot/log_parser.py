"""
FarmTech Solutions - Fase 2 - Importador do log de irrigacao.

A entrega da Fase 2 gerava um arquivo log_irrigacao.txt com as decisoes
do sistema (codigo ESP32, suspensao e motivo). Este modulo importa esses
registros para a tabela `eventos_irrigacao`, integrando a entrega antiga
ao banco unificado da Fase 7.

Formato dos blocos no log:
    ============================================================
    Data/Hora: 2025-10-15 17:09:19
    Codigo ESP32: 1
    Suspender: False
    Motivo: ...
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import LOG_IRRIGACAO_EXEMPLO
from services.fase3_banco.db_manager import DatabaseManager

PADRAO_BLOCO = re.compile(
    r"Data/Hora:\s*(?P<data>[\d\-: ]+)\s*\n"
    r".*?C[oó]digo ESP32:\s*(?P<codigo>\d)\s*\n"
    r".*?Suspender:\s*(?P<suspender>True|False)\s*\n"
    r".*?Motivo:\s*(?P<motivo>.*?)\s*(?:\n|$)",
    re.DOTALL | re.IGNORECASE,
)


def parsear_log(caminho: Path = None) -> List[Dict]:
    caminho = Path(caminho or LOG_IRRIGACAO_EXEMPLO)
    if not caminho.exists():
        raise FileNotFoundError(f"Log nao encontrado: {caminho}")
    texto = caminho.read_text(encoding="utf-8", errors="ignore")
    eventos = []
    for m in PADRAO_BLOCO.finditer(texto):
        suspender = m.group("suspender").lower() == "true"
        eventos.append({
            'data_hora': m.group("data").strip(),
            'previsao_chuva': suspender,
            # O log registra a decisao climatica; a bomba so liga sem chuva
            'bomba_ligada': not suspender,
            'motivo': (m.group("motivo").strip()
                       or ("Chuva prevista" if suspender else "Sem chuva prevista")),
        })
    return eventos


def importar(caminho: Path = None, db: DatabaseManager = None) -> int:
    db = db or DatabaseManager()
    eventos = parsear_log(caminho)
    for ev in eventos:
        db.inserir_evento_irrigacao({
            'umidade': None,
            'ph_ldr': None,
            'nivel_n': None, 'nivel_p': None, 'nivel_k': None,
            'previsao_chuva': ev['previsao_chuva'],
            'bomba_ligada': ev['bomba_ligada'],
            'motivo': f"[log {ev['data_hora']}] {ev['motivo']}",
            'fonte': 'log_fase2',
        })
    return len(eventos)


if __name__ == "__main__":
    qtd = importar()
    print(f"{qtd} eventos importados do log da Fase 2.")
