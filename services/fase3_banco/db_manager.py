"""
FarmTech Solutions - Fase 7 - Gerenciador de Banco de Dados unificado.

Evolucao do db_manager da Fase 4 (SQLite), agora com:
- Tabelas originais: sensores, leituras_sensores, culturas, acoes_manejo,
  producao, previsoes;
- Novas tabelas da Fase 7: eventos_irrigacao (Fase 2/IoT), deteccoes_visao
  (Fase 6/YOLO) e alertas (mensageria AWS SNS).

O MER/DER esta documentado em docs/mer_der/modelo_dados.md e o DDL
equivalente para Oracle em services/fase3_banco/ddl_oracle.sql (recuperacao
da entrega da Fase 3).
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import DB_PATH


class DatabaseManager:
    """Gerencia todas as operacoes do banco de dados agricola."""

    def __init__(self, db_path: str = None):
        self.db_path = str(db_path or DB_PATH)
        self._ensure_database_directory()
        self._create_tables()

    def _ensure_database_directory(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """Cria as tabelas do banco de dados se nao existirem."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL,
                localizacao TEXT,
                ativo BOOLEAN DEFAULT 1,
                data_instalacao TIMESTAMP DEFAULT (datetime('now', 'localtime'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leituras_sensores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                umidade_solo REAL,
                temperatura_solo REAL,
                ph_solo REAL,
                temperatura_ar REAL,
                umidade_ar REAL,
                luminosidade REAL,
                rendimento_kg_hectare REAL,
                FOREIGN KEY (sensor_id) REFERENCES sensores (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS culturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL,
                data_plantio DATE,
                data_colheita_prevista DATE,
                area_hectares REAL,
                sensor_id INTEGER,
                FOREIGN KEY (sensor_id) REFERENCES sensores (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acoes_manejo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cultura_id INTEGER NOT NULL,
                tipo_acao TEXT NOT NULL,
                descricao TEXT,
                quantidade REAL,
                unidade TEXT,
                data_acao TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                executada BOOLEAN DEFAULT 0,
                FOREIGN KEY (cultura_id) REFERENCES culturas (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS producao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cultura_id INTEGER NOT NULL,
                data_colheita DATE,
                rendimento_kg_hectare REAL,
                qualidade TEXT,
                observacoes TEXT,
                FOREIGN KEY (cultura_id) REFERENCES culturas (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS previsoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                umidade_prevista REAL,
                ph_previsto REAL,
                rendimento_previsto REAL,
                confianca REAL,
                FOREIGN KEY (sensor_id) REFERENCES sensores (id)
            )
        """)

        # ---- NOVAS TABELAS DA FASE 7 ----

        # Eventos do sistema de irrigacao (Fase 2/IoT): espelha o que o
        # firmware do ESP32 decide a cada ciclo (NPK, pH via LDR, DHT22, rele)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eventos_irrigacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                umidade REAL,
                ph_ldr INTEGER,
                nivel_n BOOLEAN,
                nivel_p BOOLEAN,
                nivel_k BOOLEAN,
                previsao_chuva BOOLEAN,
                bomba_ligada BOOLEAN,
                motivo TEXT,
                fonte TEXT DEFAULT 'simulador'
            )
        """)

        # Deteccoes da visao computacional (Fase 6/YOLO)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deteccoes_visao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                imagem TEXT NOT NULL,
                classe TEXT NOT NULL,
                confianca REAL,
                modelo TEXT
            )
        """)

        # Alertas enviados/registrados pelo servico de mensageria (Fase 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                origem TEXT NOT NULL,
                tipo TEXT NOT NULL,
                severidade TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                acao_corretiva TEXT,
                enviado_sns BOOLEAN DEFAULT 0,
                sns_message_id TEXT
            )
        """)

        conn.commit()
        conn.close()

    # ------------------- INSERCOES (Fase 4) -------------------

    def inserir_sensor(self, nome: str, tipo: str, localizacao: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensores (nome, tipo, localizacao) VALUES (?, ?, ?)",
            (nome, tipo, localizacao),
        )
        sensor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return sensor_id

    def inserir_leitura(self, sensor_id: int, dados: Dict) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leituras_sensores
            (sensor_id, umidade_solo, temperatura_solo, ph_solo,
             temperatura_ar, umidade_ar, luminosidade, rendimento_kg_hectare)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sensor_id,
            dados.get('umidade_solo'),
            dados.get('temperatura_solo'),
            dados.get('ph_solo'),
            dados.get('temperatura_ar'),
            dados.get('umidade_ar'),
            dados.get('luminosidade'),
            dados.get('rendimento_kg_hectare'),
        ))
        leitura_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return leitura_id

    def inserir_cultura(self, nome: str, tipo: str, data_plantio: str,
                        data_colheita_prevista: str, area_hectares: float,
                        sensor_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO culturas
            (nome, tipo, data_plantio, data_colheita_prevista, area_hectares, sensor_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, tipo, data_plantio, data_colheita_prevista, area_hectares, sensor_id))
        cultura_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return cultura_id

    def inserir_acao_manejo(self, cultura_id: int, tipo_acao: str,
                            descricao: str, quantidade: float, unidade: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO acoes_manejo (cultura_id, tipo_acao, descricao, quantidade, unidade)
            VALUES (?, ?, ?, ?, ?)
        """, (cultura_id, tipo_acao, descricao, quantidade, unidade))
        acao_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return acao_id

    def inserir_previsao(self, sensor_id: int, umidade_prevista: float,
                         ph_previsto: float, rendimento_previsto: float,
                         confianca: float) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO previsoes
            (sensor_id, umidade_prevista, ph_previsto, rendimento_previsto, confianca)
            VALUES (?, ?, ?, ?, ?)
        """, (sensor_id, umidade_prevista, ph_previsto, rendimento_previsto, confianca))
        previsao_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return previsao_id

    # ------------------- INSERCOES (Fase 7) -------------------

    def inserir_evento_irrigacao(self, evento: Dict) -> int:
        """Registra um ciclo de decisao do sistema de irrigacao (Fase 2)."""
        def como_bool(valor):
            # Preserva NULL para dados desconhecidos (ex.: log da Fase 2
            # nao registra NPK) - 0 significaria "nutriente ausente".
            return None if valor is None else int(bool(valor))

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO eventos_irrigacao
            (umidade, ph_ldr, nivel_n, nivel_p, nivel_k, previsao_chuva,
             bomba_ligada, motivo, fonte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evento.get('umidade'),
            evento.get('ph_ldr'),
            como_bool(evento.get('nivel_n')),
            como_bool(evento.get('nivel_p')),
            como_bool(evento.get('nivel_k')),
            como_bool(evento.get('previsao_chuva')),
            como_bool(evento.get('bomba_ligada')),
            evento.get('motivo', ''),
            evento.get('fonte', 'simulador'),
        ))
        evento_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return evento_id

    def inserir_deteccao_visao(self, imagem: str, classe: str,
                               confianca: float, modelo: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO deteccoes_visao (imagem, classe, confianca, modelo)
            VALUES (?, ?, ?, ?)
        """, (imagem, classe, confianca, modelo))
        deteccao_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return deteccao_id

    def inserir_alerta(self, origem: str, tipo: str, severidade: str,
                       mensagem: str, acao_corretiva: str,
                       enviado_sns: bool = False,
                       sns_message_id: str = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alertas
            (origem, tipo, severidade, mensagem, acao_corretiva, enviado_sns, sns_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (origem, tipo, severidade, mensagem, acao_corretiva,
              int(enviado_sns), sns_message_id))
        alerta_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alerta_id

    def existe_alerta_recente(self, tipo: str, janela_minutos: int = 30) -> bool:
        """Evita alertas duplicados: verifica se ja existe alerta do mesmo
        tipo dentro da janela de tempo informada (idempotencia)."""
        limite = (datetime.now() - timedelta(minutes=janela_minutos)) \
            .strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM alertas WHERE tipo = ? AND timestamp >= ?",
            (tipo, limite),
        )
        existe = cursor.fetchone()[0] > 0
        conn.close()
        return existe

    # ------------------- CONSULTAS -------------------

    def obter_leituras_recentes(self, sensor_id: Optional[int] = None,
                                limite: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        if sensor_id:
            df = pd.read_sql_query(
                "SELECT * FROM leituras_sensores WHERE sensor_id = ? "
                "ORDER BY timestamp DESC, id DESC LIMIT ?",
                conn, params=(sensor_id, limite))
        else:
            df = pd.read_sql_query(
                "SELECT * FROM leituras_sensores "
                "ORDER BY timestamp DESC, id DESC LIMIT ?",
                conn, params=(limite,))
        conn.close()
        return df

    def obter_todas_leituras(self) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM leituras_sensores ORDER BY timestamp", conn)
        conn.close()
        return df

    def obter_sensores(self) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query("SELECT * FROM sensores WHERE ativo = 1", conn)
        conn.close()
        return df

    def obter_culturas(self) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query("SELECT * FROM culturas", conn)
        conn.close()
        return df

    def obter_acoes_pendentes(self) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query("""
            SELECT a.*, c.nome as cultura_nome, c.tipo as cultura_tipo
            FROM acoes_manejo a
            JOIN culturas c ON a.cultura_id = c.id
            WHERE a.executada = 0
            ORDER BY a.data_acao DESC
        """, conn)
        conn.close()
        return df

    def obter_eventos_irrigacao(self, limite: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM eventos_irrigacao "
            "ORDER BY timestamp DESC, id DESC LIMIT ?",
            conn, params=(limite,))
        conn.close()
        return df

    def obter_deteccoes_visao(self, limite: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM deteccoes_visao "
            "ORDER BY timestamp DESC, id DESC LIMIT ?",
            conn, params=(limite,))
        conn.close()
        return df

    def obter_alertas(self, limite: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM alertas ORDER BY timestamp DESC, id DESC LIMIT ?",
            conn, params=(limite,))
        conn.close()
        return df

    def obter_tabela(self, nome_tabela: str) -> pd.DataFrame:
        """Consulta generica usada pela pagina de Banco de Dados (CRUD)."""
        if nome_tabela not in self.listar_tabelas():
            raise ValueError(f"Tabela invalida: {nome_tabela}")
        conn = self._get_connection()
        df = pd.read_sql_query(f"SELECT * FROM {nome_tabela}", conn)
        conn.close()
        return df

    def listar_tabelas(self) -> List[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tabelas = [r[0] for r in cursor.fetchall()]
        conn.close()
        return tabelas

    def executar_sql(self, query: str) -> pd.DataFrame:
        """Executa um SELECT livre (somente leitura) na pagina de BD."""
        if not query.strip().lower().startswith("select"):
            raise ValueError("Apenas consultas SELECT sao permitidas aqui.")
        conn = self._get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def deletar_registro(self, nome_tabela: str, registro_id: int):
        """Delecao pontual usada pelo CRUD da dashboard."""
        if nome_tabela not in self.listar_tabelas():
            raise ValueError(f"Tabela invalida: {nome_tabela}")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {nome_tabela} WHERE id = ?", (registro_id,))
        conn.commit()
        conn.close()

    def obter_estatisticas(self) -> Dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        stats = {}
        consultas = {
            'total_sensores': "SELECT COUNT(*) FROM sensores WHERE ativo = 1",
            'total_leituras': "SELECT COUNT(*) FROM leituras_sensores",
            'total_culturas': "SELECT COUNT(*) FROM culturas",
            'acoes_pendentes': "SELECT COUNT(*) FROM acoes_manejo WHERE executada = 0",
            'eventos_irrigacao': "SELECT COUNT(*) FROM eventos_irrigacao",
            'deteccoes_visao': "SELECT COUNT(*) FROM deteccoes_visao",
            'alertas_gerados': "SELECT COUNT(*) FROM alertas",
        }
        for chave, sql in consultas.items():
            cursor.execute(sql)
            stats[chave] = cursor.fetchone()[0]
        conn.close()
        return stats


if __name__ == "__main__":
    db = DatabaseManager()
    print("Tabelas:", db.listar_tabelas())
    print("\nEstatisticas do sistema:")
    for key, value in db.obter_estatisticas().items():
        print(f"  {key}: {value}")
