"""
FarmTech Solutions - Fase 7 - Ponto de entrada unico (CLI).

Dispara qualquer servico das Fases 1 a 6 por comando de terminal, como
pede o enunciado da Fase 7 ("por meio de um botao ou de um comando no
terminal do VS Code"). Os mesmos servicos tambem podem ser disparados
por botoes na dashboard (streamlit run dashboard/app.py).

Exemplos:
    python main.py setup
    python main.py dashboard
    python main.py fase1
    python main.py clima
    python main.py simular --ciclos 10
    python main.py importar-log
    python main.py exportar-oracle
    python main.py treinar-ml
    python main.py rendimento
    python main.py treinar-yolo --epocas 60
    python main.py visao --pasta services/fase6_visao/dataset/test/images
    python main.py alertas
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Consoles Windows (cp1252/cp850) nao suportam todos os caracteres Unicode;
# substitui os nao representaveis por '?' em vez de quebrar com
# UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")


def cmd_setup(_):
    import setup_projeto
    setup_projeto.main()


def cmd_dashboard(_):
    subprocess.run([sys.executable, "-m", "streamlit", "run",
                    str(BASE_DIR / "dashboard" / "app.py")])


def cmd_fase1(_):
    from services.fase1_calculos.cli import menu_principal
    menu_principal()


def cmd_clima_r(_):
    from services.fase1_calculos import clima_r
    print(clima_r.executar())


def cmd_clima(_):
    from services.fase2_iot.integracao_clima import executar_cli
    executar_cli()


def cmd_simular(args):
    from services.fase2_iot.irrigacao import executar_cli
    executar_cli(ciclos=args.ciclos)


def cmd_importar_log(_):
    from services.fase2_iot.log_parser import importar
    qtd = importar()
    print(f"{qtd} eventos importados do log da Fase 2.")


def cmd_exportar_oracle(_):
    from services.fase3_banco import export_oracle
    for tabela, linhas, caminho in export_oracle.exportar():
        print(f"  {tabela:20s} {linhas:6d} linhas -> {caminho}")


def cmd_treinar_ml(_):
    from services.fase3_banco.db_manager import DatabaseManager
    from services.fase4_ml.ml_models import GerenciadorModelos
    g = GerenciadorModelos(DatabaseManager())
    g.treinar_todos_modelos()
    g.salvar_todos_modelos()


def cmd_rendimento(_):
    from services.fase5_rendimento.pipeline import executar_cli
    executar_cli()


def cmd_treinar_yolo(args):
    from services.fase6_visao.treino_yolo import treinar
    treinar(epocas=args.epocas)


def cmd_visao(args):
    from services.fase6_visao.inferencia import executar_cli
    executar_cli(args.pasta)


def cmd_alertas(_):
    from services.alertas.alert_engine import executar_cli
    executar_cli()


def montar_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="FarmTech Solutions - Fase 7 - dispara os servicos "
                    "das Fases 1 a 6 via terminal.")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("setup", help="Cria BD, popula dados e treina modelos") \
       .set_defaults(func=cmd_setup)
    sub.add_parser("dashboard", help="Abre a dashboard Streamlit (Fase 4/7)") \
       .set_defaults(func=cmd_dashboard)
    sub.add_parser("fase1", help="Menu de area de plantio e insumos (Fase 1)") \
       .set_defaults(func=cmd_fase1)
    sub.add_parser("clima-r", help="Analise estatistica/clima em R (Fase 1)") \
       .set_defaults(func=cmd_clima_r)
    sub.add_parser("clima", help="Previsao OpenWeather + recomendacao (Fase 2)") \
       .set_defaults(func=cmd_clima)

    p = sub.add_parser("simular", help="Ciclos do simulador de irrigacao (Fase 2)")
    p.add_argument("--ciclos", type=int, default=5)
    p.set_defaults(func=cmd_simular)

    sub.add_parser("importar-log", help="Importa log_irrigacao da Fase 2") \
       .set_defaults(func=cmd_importar_log)
    sub.add_parser("exportar-oracle", help="Exporta CSVs p/ Oracle (Fase 3)") \
       .set_defaults(func=cmd_exportar_oracle)
    sub.add_parser("treinar-ml", help="Treina modelos de previsao (Fase 4)") \
       .set_defaults(func=cmd_treinar_ml)
    sub.add_parser("rendimento", help="Pipeline crop_yield - 5 modelos (Fase 5)") \
       .set_defaults(func=cmd_rendimento)

    p = sub.add_parser("treinar-yolo", help="Treina YOLO local (Fase 6)")
    p.add_argument("--epocas", type=int, default=60)
    p.set_defaults(func=cmd_treinar_yolo)

    p = sub.add_parser("visao", help="Detecta objetos em imagens (Fase 6)")
    p.add_argument("--pasta", type=str, default=None)
    p.set_defaults(func=cmd_visao)

    sub.add_parser("alertas", help="Motor de alertas + AWS SNS (Fase 7)") \
       .set_defaults(func=cmd_alertas)
    return parser


if __name__ == "__main__":
    args = montar_parser().parse_args()
    args.func(args)
