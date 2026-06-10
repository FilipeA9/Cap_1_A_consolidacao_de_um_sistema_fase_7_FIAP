"""
FarmTech Solutions - Fase 3 (recuperada) - Exportacao para Oracle.

Gera, na pasta exports/, um CSV por tabela do banco SQLite, prontos para
importacao no Oracle SQL Developer (botao direito em "Tabelas" ->
"Importar Dados"), seguindo exatamente o passo a passo do enunciado da
Fase 3. O DDL Oracle equivalente esta em ddl_oracle.sql.

Execucao: python main.py exportar-oracle
"""

import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import EXPORTS_DIR
from services.fase3_banco.db_manager import DatabaseManager


def exportar(destino: Path = None) -> list:
    destino = Path(destino or EXPORTS_DIR)
    destino.mkdir(parents=True, exist_ok=True)
    db = DatabaseManager()
    gerados = []
    for tabela in db.listar_tabelas():
        df = db.obter_tabela(tabela)
        caminho = destino / f"{tabela}.csv"
        df.to_csv(caminho, index=False, encoding="utf-8")
        gerados.append((tabela, len(df), str(caminho)))
    return gerados


if __name__ == "__main__":
    print("Exportando tabelas para CSV (importacao no Oracle SQL Developer)...")
    for tabela, linhas, caminho in exportar():
        print(f"  {tabela:20s} {linhas:6d} linhas -> {caminho}")
    print("\nPassos no SQL Developer: conectar em oracle.fiap.com.br:1521/ORCL")
    print("com usuario RMxxxxx, criar tabelas via ddl_oracle.sql e importar os CSVs.")
