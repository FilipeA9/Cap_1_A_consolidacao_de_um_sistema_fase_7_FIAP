"""
FarmTech Solutions - Simulador de Sensores Agrícolas
Este módulo gera dados simulados de sensores para treinar os modelos de IA.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# Adiciona o diretório pai ao path para importar o DatabaseManager
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.fase3_banco.db_manager import DatabaseManager
from services.core.config import MODELS_DIR


class SensorSimulator:
    """Simula leituras de sensores agrícolas com padrões realistas."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa o simulador de sensores.
        
        Args:
            db_manager: Instância do gerenciador de banco de dados
        """
        self.db = db_manager
        np.random.seed(42)  # Para reprodutibilidade
    
    def gerar_serie_temporal(self, dias: int = 90, 
                            frequencia_horas: int = 6) -> pd.DataFrame:
        """
        Gera uma série temporal de dados de sensores.
        
        Args:
            dias: Número de dias para simular
            frequencia_horas: Intervalo entre leituras em horas
            
        Returns:
            DataFrame com os dados simulados
        """
        # Calcula número de leituras
        num_leituras = (dias * 24) // frequencia_horas
        
        # Data inicial
        data_inicial = datetime.now() - timedelta(days=dias)
        
        # Gera timestamps
        timestamps = [data_inicial + timedelta(hours=i*frequencia_horas) 
                     for i in range(num_leituras)]
        
        # Simula padrões sazonais e diários
        dados = []
        
        for i, ts in enumerate(timestamps):
            # Hora do dia (0-23)
            hora = ts.hour
            
            # Dia do ciclo (0-dias)
            dia_ciclo = i * frequencia_horas / 24
            
            # UMIDADE DO SOLO (15% - 60%)
            # Decresce ao longo do dia, aumenta com irrigação simulada
            umidade_base = 35
            variacao_diaria = -10 * np.sin(2 * np.pi * hora / 24)
            tendencia = -0.1 * dia_ciclo  # Decresce ao longo do tempo
            irrigacao = 15 if (dia_ciclo % 7 < 1) else 0  # Irrigação semanal
            ruido = np.random.normal(0, 2)
            
            umidade_solo = umidade_base + variacao_diaria + tendencia + irrigacao + ruido
            umidade_solo = np.clip(umidade_solo, 15, 60)
            
            # TEMPERATURA DO SOLO (15°C - 35°C)
            temp_base = 25
            variacao_diaria = 5 * np.sin(2 * np.pi * (hora - 6) / 24)
            variacao_sazonal = 3 * np.sin(2 * np.pi * dia_ciclo / 365)
            ruido = np.random.normal(0, 1)
            
            temperatura_solo = temp_base + variacao_diaria + variacao_sazonal + ruido
            temperatura_solo = np.clip(temperatura_solo, 15, 35)
            
            # pH DO SOLO (5.5 - 7.5)
            # Varia lentamente ao longo do tempo
            ph_base = 6.5
            tendencia_ph = 0.002 * dia_ciclo
            fertilizacao = 0.3 if (dia_ciclo % 14 < 1) else 0
            ruido = np.random.normal(0, 0.1)
            
            ph_solo = ph_base + tendencia_ph + fertilizacao + ruido
            ph_solo = np.clip(ph_solo, 5.5, 7.5)
            
            # TEMPERATURA DO AR (10°C - 40°C)
            temp_ar_base = 28
            variacao_diaria = 8 * np.sin(2 * np.pi * (hora - 6) / 24)
            variacao_sazonal = 5 * np.sin(2 * np.pi * dia_ciclo / 365)
            ruido = np.random.normal(0, 1.5)
            
            temperatura_ar = temp_ar_base + variacao_diaria + variacao_sazonal + ruido
            temperatura_ar = np.clip(temperatura_ar, 10, 40)
            
            # UMIDADE DO AR (30% - 95%)
            umidade_ar_base = 65
            variacao_diaria = -15 * np.sin(2 * np.pi * (hora - 6) / 24)
            ruido = np.random.normal(0, 3)
            
            umidade_ar = umidade_ar_base + variacao_diaria + ruido
            umidade_ar = np.clip(umidade_ar, 30, 95)
            
            # LUMINOSIDADE (0 - 1000 lux)
            # Zero durante a noite, máxima ao meio-dia
            if 6 <= hora <= 18:
                luminosidade_base = 500 * np.sin(np.pi * (hora - 6) / 12)
                ruido = np.random.normal(0, 50)
                luminosidade = luminosidade_base + ruido
            else:
                luminosidade = np.random.normal(0, 10)
            
            luminosidade = np.clip(luminosidade, 0, 1000)
            
            dados.append({
                'timestamp': ts,
                'umidade_solo': round(umidade_solo, 2),
                'temperatura_solo': round(temperatura_solo, 2),
                'ph_solo': round(ph_solo, 2),
                'temperatura_ar': round(temperatura_ar, 2),
                'umidade_ar': round(umidade_ar, 2),
                'luminosidade': round(luminosidade, 2)
            })
        
        return pd.DataFrame(dados)
    
    def calcular_rendimento(self, dados: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula o rendimento esperado baseado nas condições do solo.
        Esta é a variável alvo para o modelo de regressão.
        
        Args:
            dados: DataFrame com dados dos sensores
            
        Returns:
            DataFrame com coluna de rendimento adicionada
        """
        # Condições ideais para a cultura (exemplo: milho)
        umidade_ideal = 40
        ph_ideal = 6.5
        temp_ideal = 25
        
        rendimentos = []
        
        for _, row in dados.iterrows():
            # Penalidade por desvio das condições ideais
            penalidade_umidade = abs(row['umidade_solo'] - umidade_ideal) / umidade_ideal
            penalidade_ph = abs(row['ph_solo'] - ph_ideal) / ph_ideal
            penalidade_temp = abs(row['temperatura_solo'] - temp_ideal) / temp_ideal
            
            # Rendimento base (ton/hectare)
            rendimento_base = 8.0
            
            # Redução por condições não ideais
            reducao = (penalidade_umidade * 0.4 + 
                      penalidade_ph * 0.3 + 
                      penalidade_temp * 0.3)
            
            # Adiciona variação aleatória
            ruido = np.random.normal(0, 0.3)
            
            rendimento = rendimento_base * (1 - reducao) + ruido
            rendimento = np.clip(rendimento, 2, 10)
            
            rendimentos.append(round(rendimento, 2))
        
        dados['rendimento_kg_hectare'] = rendimentos
        return dados
    
    def popular_banco_dados(self, num_sensores: int = 3, dias: int = 90):
        """
        Popula o banco de dados com sensores e leituras simuladas.
        
        Args:
            num_sensores: Número de sensores a criar
            dias: Dias de histórico a gerar
        """
        print(f"\nIniciando simulação de {num_sensores} sensores por {dias} dias...")
        
        # Localidades exemplo
        localizacoes = [
            "Talhão A - Norte",
            "Talhão B - Sul",
            "Talhão C - Leste",
            "Talhão D - Oeste",
            "Talhão E - Centro"
        ]
        
        culturas_info = [
            ("Milho", "Cereal"),
            ("Soja", "Leguminosa"),
            ("Trigo", "Cereal"),
            ("Algodão", "Fibra"),
            ("Café", "Perene")
        ]
        
        total_leituras = 0
        
        for i in range(num_sensores):
            # Cria sensor
            sensor_id = self.db.inserir_sensor(
                nome=f"Sensor {i+1}",
                tipo="Multiparâmetro",
                localizacao=localizacoes[i % len(localizacoes)]
            )
            
            print(f"  - Sensor {sensor_id} criado: {localizacoes[i % len(localizacoes)]}")
            
            # Gera dados do sensor
            dados = self.gerar_serie_temporal(dias=dias, frequencia_horas=6)
            dados = self.calcular_rendimento(dados)
            
            # Insere leituras no banco
            for _, row in dados.iterrows():
                self.db.inserir_leitura(sensor_id, row.to_dict())
                total_leituras += 1
            
            # Cria cultura associada
            cultura_nome, cultura_tipo = culturas_info[i % len(culturas_info)]
            data_plantio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
            data_colheita = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            self.db.inserir_cultura(
                nome=f"{cultura_nome} - Talhão {chr(65+i)}",
                tipo=cultura_tipo,
                data_plantio=data_plantio,
                data_colheita_prevista=data_colheita,
                area_hectares=round(np.random.uniform(5, 20), 2),
                sensor_id=sensor_id
            )
            
            print(f"      {total_leituras} leituras geradas")
        
        print(f"\n[OK] Simulação concluída!")
        print(f"   Total de leituras: {total_leituras}")
        print(f"   Total de sensores: {num_sensores}")
        
        # Exibe estatísticas
        stats = self.db.obter_estatisticas()
        print(f"\nEstatísticas do banco de dados:")
        for key, value in stats.items():
            print(f"   {key}: {value}")


if __name__ == "__main__":
    # Cria e popula banco de dados
    db = DatabaseManager()
    simulator = SensorSimulator(db)
    simulator.popular_banco_dados(num_sensores=3, dias=90)

