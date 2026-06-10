"""
FarmTech Solutions - Servico da Fase 1
Calculo de area de plantio e manejo de insumos (cafe e cana-de-acucar).

Funcoes puras portadas do farmtech_app.py original, agora reutilizaveis
pela CLI (terminal) e pela dashboard (Streamlit). Os dados continuam
organizados em vetores (lista de dicionarios), como exigia o enunciado
da Fase 1, com persistencia opcional na tabela `culturas` do banco.
"""

import math
from typing import Dict, List

# Dados tecnicos das culturas (mesmos valores da entrega da Fase 1)
CAFE_INSUMOS = {
    'fungicida': 1.5,     # L/hectare
    'fertilizante': 400,  # kg/hectare
    'herbicida': 2.0,     # L/hectare
}

CANA_INSUMOS = {
    'herbicida': 3.0,     # L/hectare
    'fertilizante': 500,  # kg/hectare
    'inseticida': 0.5,    # L/hectare
}

INSUMOS_POR_CULTURA = {'cafe': CAFE_INSUMOS, 'cana': CANA_INSUMOS}
NOMES_CULTURAS = {'cafe': 'Cafe', 'cana': 'Cana-de-acucar'}


def calcular_area_retangulo(comprimento: float, largura: float) -> float:
    """Area de talhao retangular (cafe) em hectares."""
    if comprimento <= 0 or largura <= 0:
        raise ValueError("Comprimento e largura devem ser positivos.")
    return (comprimento * largura) / 10_000


def calcular_area_circulo(raio: float) -> float:
    """Area de pivo central circular (cana) em hectares."""
    if raio <= 0:
        raise ValueError("O raio deve ser positivo.")
    return (math.pi * raio ** 2) / 10_000


def calcular_insumos(cultura: str, area_hectares: float) -> Dict[str, Dict]:
    """Calcula todos os insumos necessarios para a cultura e area dadas.

    Returns:
        {'fungicida': {'quantidade': 15.0, 'unidade': 'L'}, ...}
    """
    tabela = INSUMOS_POR_CULTURA.get(cultura.lower())
    if not tabela:
        raise ValueError(f"Cultura desconhecida: {cultura}")
    resultado = {}
    for insumo, taxa in tabela.items():
        unidade = 'kg' if insumo == 'fertilizante' else 'L'
        resultado[insumo] = {
            'quantidade': round(taxa * area_hectares, 2),
            'unidade': unidade,
            'taxa_por_hectare': taxa,
        }
    return resultado


def montar_registro(cultura: str, geometria: str, **dimensoes) -> Dict:
    """Cria um registro do vetor de culturas a partir das dimensoes.

    geometria: 'retangulo' (comprimento, largura) ou 'circulo' (raio).
    """
    cultura = cultura.lower()
    if geometria == 'retangulo':
        area = calcular_area_retangulo(dimensoes['comprimento'], dimensoes['largura'])
    elif geometria == 'circulo':
        area = calcular_area_circulo(dimensoes['raio'])
    else:
        raise ValueError(f"Geometria desconhecida: {geometria}")

    return {
        'cultura': cultura,
        'nome_cultura': NOMES_CULTURAS[cultura],
        'geometria': geometria,
        **dimensoes,
        'area_hectares': round(area, 4),
        'insumos': calcular_insumos(cultura, area),
    }


# ----- Operacoes de vetor (entrada, saida, atualizacao, delecao) -----

def adicionar(vetor: List[Dict], registro: Dict) -> List[Dict]:
    vetor.append(registro)
    return vetor


def atualizar(vetor: List[Dict], posicao: int, registro: Dict) -> List[Dict]:
    if not 0 <= posicao < len(vetor):
        raise IndexError("Posicao invalida no vetor de culturas.")
    vetor[posicao] = registro
    return vetor


def deletar(vetor: List[Dict], posicao: int) -> Dict:
    if not 0 <= posicao < len(vetor):
        raise IndexError("Posicao invalida no vetor de culturas.")
    return vetor.pop(posicao)


def persistir_no_banco(registro: Dict, db=None) -> int:
    """Grava o registro na tabela `culturas` (integracao Fase 1 -> Fase 2/3)."""
    if db is None:
        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from services.fase3_banco.db_manager import DatabaseManager
        db = DatabaseManager()
    return db.inserir_cultura(
        nome=registro['nome_cultura'],
        tipo='Perene' if registro['cultura'] == 'cafe' else 'Semiperene',
        data_plantio=None,
        data_colheita_prevista=None,
        area_hectares=registro['area_hectares'],
        sensor_id=None,
    )
