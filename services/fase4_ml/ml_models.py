"""
FarmTech Solutions - Modelos de Machine Learning
Este módulo implementa modelos de regressão para prever variáveis agrícolas críticas.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
from typing import Dict, Tuple, Optional
import sys

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.fase3_banco.db_manager import DatabaseManager
from services.core.config import MODELS_DIR


class ModeloAgricola:
    """Classe base para modelos de previsão agrícola."""
    
    def __init__(self, nome_modelo: str):
        """
        Inicializa o modelo.
        
        Args:
            nome_modelo: Nome identificador do modelo
        """
        self.nome_modelo = nome_modelo
        self.modelo = None
        self.scaler = StandardScaler()
        self.metricas = {}
        self.features = []
        self.target = ""
    
    def treinar(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            X: Features de entrada
            y: Variável alvo
            
        Returns:
            Dicionário com métricas de desempenho
        """
        # Divide dados em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Normaliza os dados
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Treina o modelo
        self.modelo.fit(X_train_scaled, y_train)
        
        # Faz previsões
        y_pred_train = self.modelo.predict(X_train_scaled)
        y_pred_test = self.modelo.predict(X_test_scaled)
        
        # Calcula métricas
        self.metricas = {
            'r2_train': r2_score(y_train, y_pred_train),
            'r2_test': r2_score(y_test, y_pred_test),
            'rmse_train': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'rmse_test': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'mae_train': mean_absolute_error(y_train, y_pred_train),
            'mae_test': mean_absolute_error(y_test, y_pred_test)
        }
        
        return self.metricas
    
    def prever(self, X: pd.DataFrame) -> np.ndarray:
        """
        Faz previsões com o modelo treinado.
        
        Args:
            X: Features de entrada
            
        Returns:
            Array com as previsões
        """
        if self.modelo is None:
            raise ValueError("Modelo não foi treinado ainda!")
        
        X_scaled = self.scaler.transform(X)
        return self.modelo.predict(X_scaled)
    
    def salvar_modelo(self, caminho: str = None):
        """Salva o modelo treinado em disco."""
        caminho = str(caminho or MODELS_DIR)
        os.makedirs(caminho, exist_ok=True)
        
        joblib.dump(self.modelo, f"{caminho}/{self.nome_modelo}_modelo.pkl")
        joblib.dump(self.scaler, f"{caminho}/{self.nome_modelo}_scaler.pkl")
        joblib.dump({
            'features': self.features,
            'target': self.target,
            'metricas': self.metricas
        }, f"{caminho}/{self.nome_modelo}_info.pkl")
        
        print(f"[OK] Modelo {self.nome_modelo} salvo em {caminho}")
    
    def carregar_modelo(self, caminho: str = None):
        """Carrega um modelo previamente treinado."""
        caminho = str(caminho or MODELS_DIR)
        self.modelo = joblib.load(f"{caminho}/{self.nome_modelo}_modelo.pkl")
        self.scaler = joblib.load(f"{caminho}/{self.nome_modelo}_scaler.pkl")
        info = joblib.load(f"{caminho}/{self.nome_modelo}_info.pkl")
        
        self.features = info['features']
        self.target = info['target']
        self.metricas = info['metricas']
        
        print(f"[OK] Modelo {self.nome_modelo} carregado de {caminho}")


class ModeloUmidade(ModeloAgricola):
    """Modelo para prever umidade futura do solo."""
    
    def __init__(self):
        super().__init__("umidade_solo")
        self.modelo = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.features = ['temperatura_solo', 'temperatura_ar', 'umidade_ar', 
                        'luminosidade', 'hora_dia', 'dias_desde_irrigacao']
        self.target = 'umidade_solo'


class ModeloPH(ModeloAgricola):
    """Modelo para prever pH futuro do solo."""
    
    def __init__(self):
        super().__init__("ph_solo")
        self.modelo = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.features = ['umidade_solo', 'temperatura_solo', 'temperatura_ar',
                        'dias_desde_fertilizacao']
        self.target = 'ph_solo'


class ModeloRendimento(ModeloAgricola):
    """Modelo para prever rendimento da cultura."""
    
    def __init__(self):
        super().__init__("rendimento")
        self.modelo = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            random_state=42
        )
        self.features = ['umidade_solo', 'temperatura_solo', 'ph_solo',
                        'temperatura_ar', 'umidade_ar', 'luminosidade']
        self.target = 'rendimento_kg_hectare'


class GerenciadorModelos:
    """Gerencia treinamento e previsões de todos os modelos."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa o gerenciador de modelos.
        
        Args:
            db_manager: Instância do gerenciador de banco de dados
        """
        self.db = db_manager
        self.modelo_umidade = ModeloUmidade()
        self.modelo_ph = ModeloPH()
        self.modelo_rendimento = ModeloRendimento()
        self.dados_preparados = None
    
    def preparar_dados(self) -> pd.DataFrame:
        """
        Prepara os dados do banco para treinamento dos modelos.
        
        Returns:
            DataFrame com features engenheiradas
        """
        print("\nPreparando dados para treinamento...")
        
        # Carrega todas as leituras
        df = self.db.obter_todas_leituras()
        
        if len(df) == 0:
            raise ValueError("Não há dados no banco de dados!")
        
        print(f"   {len(df)} leituras carregadas")
        
        # Converte timestamp para datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Feature engineering
        df['hora_dia'] = df['timestamp'].dt.hour
        df['dia_ano'] = df['timestamp'].dt.dayofyear
        df['dia_semana'] = df['timestamp'].dt.dayofweek
        
        # Simula dias desde última irrigação (ciclo de 7 dias)
        df['dias_desde_irrigacao'] = df.groupby('sensor_id').cumcount() % 7
        
        # Simula dias desde última fertilização (ciclo de 14 dias)
        df['dias_desde_fertilizacao'] = df.groupby('sensor_id').cumcount() % 14
        
        # Remove valores nulos
        df = df.dropna()
        
        self.dados_preparados = df
        print(f"   - Dados preparados: {df.shape}")
        
        return df
    
    def treinar_todos_modelos(self) -> Dict:
        """
        Treina todos os modelos de previsão.
        
        Returns:
            Dicionário com métricas de todos os modelos
        """
        print("\nIniciando treinamento dos modelos de IA...\n")
        
        if self.dados_preparados is None:
            self.preparar_dados()
        
        df = self.dados_preparados
        resultados = {}
        
        # 1. Treina modelo de Umidade
        print("[1/3] Treinando Modelo de Umidade do Solo...")
        X_umidade = df[self.modelo_umidade.features]
        y_umidade = df[self.modelo_umidade.target]
        metricas_umidade = self.modelo_umidade.treinar(X_umidade, y_umidade)
        resultados['umidade'] = metricas_umidade
        print(f"   - R² Test: {metricas_umidade['r2_test']:.4f}")
        print(f"   - RMSE Test: {metricas_umidade['rmse_test']:.4f}")
        
        # 2. Treina modelo de pH
        print("\n[2/3] Treinando Modelo de pH do Solo...")
        X_ph = df[self.modelo_ph.features]
        y_ph = df[self.modelo_ph.target]
        metricas_ph = self.modelo_ph.treinar(X_ph, y_ph)
        resultados['ph'] = metricas_ph
        print(f"   - R² Test: {metricas_ph['r2_test']:.4f}")
        print(f"   - RMSE Test: {metricas_ph['rmse_test']:.4f}")
        
        # 3. Treina modelo de Rendimento
        print("\n[3/3] Treinando Modelo de Rendimento...")
        X_rendimento = df[self.modelo_rendimento.features]
        y_rendimento = df[self.modelo_rendimento.target]
        metricas_rendimento = self.modelo_rendimento.treinar(X_rendimento, y_rendimento)
        resultados['rendimento'] = metricas_rendimento
        print(f"   - R² Test: {metricas_rendimento['r2_test']:.4f}")
        print(f"   - RMSE Test: {metricas_rendimento['rmse_test']:.4f}")
        
        print("\n[OK] Todos os modelos foram treinados com sucesso!")
        
        return resultados
    
    def salvar_todos_modelos(self):
        """Salva todos os modelos treinados."""
        print("\nSalvando modelos...")
        self.modelo_umidade.salvar_modelo()
        self.modelo_ph.salvar_modelo()
        self.modelo_rendimento.salvar_modelo()
        print("[OK] Todos os modelos salvos!")
    
    def carregar_todos_modelos(self):
        """Carrega todos os modelos salvos."""
        print("\nCarregando modelos...")
        try:
            self.modelo_umidade.carregar_modelo()
            self.modelo_ph.carregar_modelo()
            self.modelo_rendimento.carregar_modelo()
            print("[OK] Todos os modelos carregados!")
            return True
        except FileNotFoundError:
            print("[AVISO] Modelos não encontrados. Execute o treinamento primeiro.")
            return False
    
    def fazer_previsao_completa(self, dados_atuais: Dict) -> Dict:
        """
        Faz previsão completa usando todos os modelos.
        
        Args:
            dados_atuais: Dicionário com os dados atuais dos sensores
            
        Returns:
            Dicionário com todas as previsões
        """
        # Prepara dados de entrada
        entrada = pd.DataFrame([dados_atuais])
        
        # Garante que todas as features necessárias existem
        for feature in ['hora_dia', 'dias_desde_irrigacao', 'dias_desde_fertilizacao']:
            if feature not in entrada.columns:
                entrada[feature] = 0
        
        previsoes = {}
        
        # Prevê umidade
        if all(f in entrada.columns for f in self.modelo_umidade.features):
            X_umidade = entrada[self.modelo_umidade.features]
            previsoes['umidade_prevista'] = float(self.modelo_umidade.prever(X_umidade)[0])
        
        # Prevê pH
        if all(f in entrada.columns for f in self.modelo_ph.features):
            X_ph = entrada[self.modelo_ph.features]
            previsoes['ph_previsto'] = float(self.modelo_ph.prever(X_ph)[0])
        
        # Prevê rendimento
        if all(f in entrada.columns for f in self.modelo_rendimento.features):
            X_rendimento = entrada[self.modelo_rendimento.features]
            previsoes['rendimento_previsto'] = float(self.modelo_rendimento.prever(X_rendimento)[0])
        
        # Calcula confiança média baseada no R²
        confianca_media = np.mean([
            self.modelo_umidade.metricas.get('r2_test', 0),
            self.modelo_ph.metricas.get('r2_test', 0),
            self.modelo_rendimento.metricas.get('r2_test', 0)
        ])
        previsoes['confianca'] = float(confianca_media)
        
        return previsoes


if __name__ == "__main__":
    # Teste do módulo
    db = DatabaseManager()
    gerenciador = GerenciadorModelos(db)
    
    # Treina modelos
    resultados = gerenciador.treinar_todos_modelos()
    
    # Salva modelos
    gerenciador.salvar_todos_modelos()
    
    print("\n" + "="*50)
    print("RESUMO DAS MÉTRICAS")
    print("="*50)
    
    for modelo, metricas in resultados.items():
        print(f"\n{modelo.upper()}:")
        print(f"  R² (treino): {metricas['r2_train']:.4f}")
        print(f"  R² (teste):  {metricas['r2_test']:.4f}")
        print(f"  RMSE (teste): {metricas['rmse_test']:.4f}")
        print(f"  MAE (teste):  {metricas['mae_test']:.4f}")

