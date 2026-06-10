"""
FarmTech Solutions - Fase 7 - Setup do projeto.

Prepara o ambiente do zero (os artefatos gerados nao sao versionados):
1. Cria o banco SQLite com todas as tabelas (Fases 2/3/7);
2. Popula o banco com 90 dias de leituras simuladas (Fase 4);
3. Treina e salva os 3 modelos de ML (umidade, pH, rendimento - Fase 4);
4. Importa o log de irrigacao da entrega da Fase 2;
5. Executa alguns ciclos do simulador de irrigacao (Fase 2).

Execucao: python setup_projeto.py   (ou: python main.py setup)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Consoles Windows (cp1252/cp850) nao suportam todos os caracteres Unicode;
# substitui os nao representaveis por '?' em vez de quebrar com
# UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

from services.fase3_banco.db_manager import DatabaseManager


def main():
    print("=" * 60)
    print("SETUP - FarmTech Solutions Fase 7")
    print("=" * 60)

    # 1) Banco de dados
    print("\n[1/5] Criando banco de dados...")
    db = DatabaseManager()
    print(f"      Tabelas: {', '.join(db.listar_tabelas())}")

    # 2) Populacao com dados simulados (se vazio)
    print("\n[2/5] Populando banco com leituras simuladas (Fase 4)...")
    stats = db.obter_estatisticas()
    if stats['total_leituras'] == 0:
        from services.fase4_ml.sensor_simulator import SensorSimulator
        SensorSimulator(db).popular_banco_dados(num_sensores=3, dias=90)
    else:
        print(f"      Banco ja possui {stats['total_leituras']} leituras - pulando.")

    # 3) Treinamento dos modelos da Fase 4
    print("\n[3/5] Treinando modelos de ML (Fase 4)...")
    from services.fase4_ml.ml_models import GerenciadorModelos
    gerenciador = GerenciadorModelos(db)
    gerenciador.treinar_todos_modelos()
    gerenciador.salvar_todos_modelos()

    # 4) Importacao do log da Fase 2
    print("\n[4/5] Importando log de irrigacao da entrega da Fase 2...")
    try:
        from services.fase2_iot.log_parser import importar
        qtd = importar(db=db)
        print(f"      {qtd} eventos importados.")
    except FileNotFoundError as e:
        print(f"      Aviso: {e}")

    # 5) Ciclos do simulador de irrigacao
    print("\n[5/5] Executando 5 ciclos do simulador de irrigacao (Fase 2)...")
    from services.fase2_iot.irrigacao import executar_ciclo
    for _ in range(5):
        executar_ciclo(db)
    print("      Ciclos gravados em eventos_irrigacao.")

    print("\n" + "=" * 60)
    print("SETUP CONCLUIDO!")
    print("=" * 60)
    print("Proximos passos:")
    print("  streamlit run dashboard/app.py      -> dashboard integradora")
    print("  python main.py --help               -> servicos via terminal")
    print("  cp .env.example .env                -> configurar OpenWeather/AWS")
    print("  python main.py treinar-yolo         -> gerar best.pt (Fase 6)")


if __name__ == "__main__":
    main()
