"""
FarmTech Solutions - Fase 7
Configuracao central do projeto: caminhos, variaveis de ambiente e constantes.
Todos os servicos importam daqui para garantir consistencia entre as fases.
"""

import os
from pathlib import Path

# Raiz do repositorio (farmtech-fase7/)
BASE_DIR = Path(__file__).resolve().parents[2]

# Carrega variaveis do .env (se python-dotenv estiver instalado)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass  # dotenv e opcional; variaveis podem vir do ambiente do SO

# --- Caminhos principais ---
DB_PATH = BASE_DIR / "database" / "farmtech.db"
MODELS_DIR = BASE_DIR / "services" / "fase4_ml" / "saved"
CROP_YIELD_CSV = BASE_DIR / "services" / "fase5_rendimento" / "crop_yield.csv"
VISAO_DIR = BASE_DIR / "services" / "fase6_visao"
VISAO_DATASET = VISAO_DIR / "dataset"
VISAO_BEST_PT = VISAO_DIR / "best.pt"
VISAO_SAIDA = VISAO_DIR / "saida"
LOG_IRRIGACAO_EXEMPLO = BASE_DIR / "services" / "fase2_iot" / "log_irrigacao_exemplo.txt"
EXPORTS_DIR = BASE_DIR / "exports"

# --- OpenWeather (Fases 1/2) ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_CIDADE = os.getenv("OPENWEATHER_CIDADE", "Sao Paulo")
OPENWEATHER_PAIS = os.getenv("OPENWEATHER_PAIS", "BR")

# --- AWS SNS (Fase 7) ---
AWS_REGION = os.getenv("AWS_REGION", "sa-east-1")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

# --- Parametros agronomicos (unificados a partir das Fases 2 e 4) ---
# Escala do firmware ESP32 (Fase 2): umidade DHT22 em % e pH simulado por LDR (0-4095)
UMIDADE_MINIMA_ESP32 = 60.0
PH_LDR_MINIMO = 1500
PH_LDR_MAXIMO = 2500

# Escala dos sensores simulados (Fase 4): umidade do solo em % e pH real
UMIDADE_SOLO_CRITICA = 30.0
PH_SOLO_MINIMO = 5.5
PH_SOLO_MAXIMO = 7.0

# Clima (Fase 2): limiares para suspender irrigacao
PROBABILIDADE_CHUVA_MINIMA = 30   # %
QUANTIDADE_CHUVA_MINIMA = 2.0     # mm
