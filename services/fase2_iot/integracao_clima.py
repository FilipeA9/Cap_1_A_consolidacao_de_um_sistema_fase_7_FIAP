"""
FarmTech Solutions - Fase 2 - Integracao com a API OpenWeather (refatorada).

Mudancas em relacao a entrega original:
- A chave da API saiu do codigo e agora vem do .env (OPENWEATHER_API_KEY);
- As funcoes retornam dicionarios (reutilizaveis pela dashboard, pelo
  alert_engine e pela CLI) em vez de apenas imprimir;
- Mantida a mesma logica de decisao: suspende irrigacao se probabilidade
  de chuva >= 30% ou volume previsto >= 2 mm nas proximas 24h.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Optional

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import (
    OPENWEATHER_API_KEY, OPENWEATHER_CIDADE, OPENWEATHER_PAIS,
    PROBABILIDADE_CHUVA_MINIMA, QUANTIDADE_CHUVA_MINIMA,
)

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"


def obter_previsao(cidade: str = None, pais: str = None) -> Optional[Dict]:
    """Consulta a previsao das proximas 24h. Retorna None se falhar."""
    if not OPENWEATHER_API_KEY:
        return None
    cidade = cidade or OPENWEATHER_CIDADE
    pais = pais or OPENWEATHER_PAIS
    url = (f"{BASE_URL}?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}"
           "&units=metric&lang=pt_br")
    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.RequestException:
        return None


def analisar_previsao(dados: Dict) -> Optional[Dict]:
    """Consolida as proximas 24h (8 blocos de 3h) em um resumo de chuva."""
    if not dados or 'list' not in dados:
        return None

    blocos = []
    chuva_total = 0.0
    prob_maxima = 0.0
    descricao = "Sem dados"

    for prev in dados['list'][:8]:
        prob = prev.get('pop', 0) * 100
        chuva_mm = prev.get('rain', {}).get('3h', 0.0)
        clima = (prev.get('weather') or [{}])[0].get('description', 'Sem dados')
        blocos.append({
            'data_hora': datetime.fromtimestamp(prev.get('dt', 0)).strftime('%d/%m %H:%M'),
            'temperatura': prev.get('main', {}).get('temp', 0),
            'probabilidade_chuva': round(prob),
            'chuva_mm': chuva_mm,
            'descricao': clima,
        })
        chuva_total += chuva_mm
        if prob > prob_maxima:
            prob_maxima = prob
            descricao = clima

    return {
        'cidade': dados.get('city', {}).get('name', OPENWEATHER_CIDADE),
        'blocos': blocos,
        'probabilidade_maxima': prob_maxima,
        'quantidade_total_mm': round(chuva_total, 1),
        'descricao_clima': descricao,
        'chuva_detectada': chuva_total > 0,
    }


def gerar_recomendacao(analise: Dict) -> Dict:
    """Decide se a irrigacao deve ser suspensa (mesma logica da Fase 2)."""
    suspender = False
    motivo = "Baixa probabilidade de chuva"

    if analise['probabilidade_maxima'] >= PROBABILIDADE_CHUVA_MINIMA:
        suspender = True
        motivo = f"Alta probabilidade de chuva ({analise['probabilidade_maxima']:.0f}%)"
    elif analise['quantidade_total_mm'] >= QUANTIDADE_CHUVA_MINIMA:
        suspender = True
        motivo = f"Chuva prevista de {analise['quantidade_total_mm']:.1f} mm"

    return {
        'suspender_irrigacao': suspender,
        'motivo': motivo,
        # Codigo a digitar no Monitor Serial do Wokwi (compatibilidade Fase 2)
        'codigo_esp32': '0' if suspender else '1',
        'analise': analise,
    }


def executar() -> Optional[Dict]:
    """Fluxo completo: consulta -> analise -> recomendacao."""
    dados = obter_previsao()
    if dados is None:
        return None
    analise = analisar_previsao(dados)
    if analise is None:
        return None
    return gerar_recomendacao(analise)


def executar_cli():
    """Versao para terminal (python main.py clima)."""
    print("=" * 60)
    print("INTEGRACAO CLIMATICA - FarmTech Solutions (Fase 2)")
    print("=" * 60)
    rec = executar()
    if rec is None:
        print("Sem acesso a API OpenWeather.")
        print("Configure OPENWEATHER_API_KEY no arquivo .env "
              "(https://openweathermap.org/api).")
        return
    a = rec['analise']
    print(f"Local: {a['cidade']}")
    for b in a['blocos']:
        print(f"  {b['data_hora']} | {b['temperatura']:.1f}C | "
              f"chuva {b['probabilidade_chuva']}% | {b['descricao']}")
    print("-" * 60)
    acao = "SUSPENDER IRRIGACAO" if rec['suspender_irrigacao'] else "IRRIGACAO PERMITIDA"
    print(f"RECOMENDACAO: {acao} (motivo: {rec['motivo']})")
    print(f"Codigo para o Monitor Serial do ESP32/Wokwi: {rec['codigo_esp32']}")


if __name__ == "__main__":
    executar_cli()
