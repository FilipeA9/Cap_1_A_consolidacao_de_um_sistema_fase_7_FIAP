"""
FarmTech Solutions - Sistema de Recomendações
Este módulo gera recomendações inteligentes de manejo agrícola
baseadas nas previsões dos modelos de IA.
"""

import sys
import os
from typing import Dict, List, Tuple
import numpy as np

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.fase3_banco.db_manager import DatabaseManager
from services.core.config import MODELS_DIR


class SistemaRecomendacao:
    """
    Sistema inteligente para recomendar ações de manejo agrícola
    baseadas em previsões de IA e regras agronômicas.
    """
    
    # Faixas ideais para diferentes variáveis (exemplo: cultura de milho)
    FAIXAS_IDEAIS = {
        'umidade_solo': {'min': 35, 'max': 50, 'ideal': 40},
        'ph_solo': {'min': 6.0, 'max': 7.0, 'ideal': 6.5},
        'temperatura_solo': {'min': 20, 'max': 30, 'ideal': 25},
        'rendimento_esperado': {'min': 7.0, 'max': 12.0, 'ideal': 9.0}
    }
    
    # Limiares de criticidade
    LIMIAR_ALERTA = 0.7  # 70% da faixa ideal
    LIMIAR_CRITICO = 0.5  # 50% da faixa ideal
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa o sistema de recomendações.
        
        Args:
            db_manager: Instância do gerenciador de banco de dados
        """
        self.db = db_manager
    
    def calcular_criticidade(self, valor: float, variavel: str) -> Tuple[str, float]:
        """
        Calcula o nível de criticidade de uma variável.
        
        Args:
            valor: Valor medido ou previsto
            variavel: Nome da variável
            
        Returns:
            Tupla (nível, score) onde nível é 'ideal', 'alerta' ou 'crítico'
        """
        faixa = self.FAIXAS_IDEAIS.get(variavel)
        if not faixa:
            return 'desconhecido', 0.0
        
        ideal = faixa['ideal']
        minimo = faixa['min']
        maximo = faixa['max']
        
        # Calcula desvio do ideal (normalizado 0-1)
        if valor < ideal:
            desvio = (ideal - valor) / (ideal - minimo) if ideal != minimo else 0
        else:
            desvio = (valor - ideal) / (maximo - ideal) if maximo != ideal else 0
        
        # Score de adequação (1 = ideal, 0 = crítico)
        score = 1 - min(desvio, 1.0)
        
        # Determina nível
        if score >= self.LIMIAR_ALERTA:
            nivel = 'ideal'
        elif score >= self.LIMIAR_CRITICO:
            nivel = 'alerta'
        else:
            nivel = 'crítico'
        
        return nivel, score
    
    def recomendar_irrigacao(self, umidade_atual: float, 
                            umidade_prevista: float,
                            dias_sem_chuva: int = 0) -> Dict:
        """
        Recomenda ações de irrigação baseadas na umidade.
        
        Args:
            umidade_atual: Umidade do solo atual (%)
            umidade_prevista: Umidade prevista pelo modelo (%)
            dias_sem_chuva: Dias consecutivos sem chuva
            
        Returns:
            Dicionário com recomendação de irrigação
        """
        nivel_atual, score_atual = self.calcular_criticidade(umidade_atual, 'umidade_solo')
        nivel_previsto, score_previsto = self.calcular_criticidade(umidade_prevista, 'umidade_solo')
        
        recomendacao = {
            'tipo_acao': 'irrigacao',
            'prioridade': 'baixa',
            'necessaria': False,
            'quantidade_mm': 0,
            'urgencia_horas': 48,
            'justificativa': ''
        }
        
        # Umidade crítica - irrigação urgente
        if nivel_atual == 'crítico':
            recomendacao['necessaria'] = True
            recomendacao['prioridade'] = 'alta'
            recomendacao['quantidade_mm'] = 30 + (dias_sem_chuva * 2)
            recomendacao['urgencia_horas'] = 6
            recomendacao['justificativa'] = (
                f"Umidade do solo crítica ({umidade_atual:.1f}%). "
                f"Irrigação urgente necessária para evitar estresse hídrico."
            )
        
        # Umidade em alerta
        elif nivel_atual == 'alerta':
            recomendacao['necessaria'] = True
            recomendacao['prioridade'] = 'média'
            recomendacao['quantidade_mm'] = 20 + (dias_sem_chuva * 1)
            recomendacao['urgencia_horas'] = 24
            recomendacao['justificativa'] = (
                f"Umidade do solo em nível de alerta ({umidade_atual:.1f}%). "
                f"Irrigação recomendada nas próximas 24 horas."
            )
        
        # Previsão indica queda para nível crítico
        elif nivel_previsto == 'crítico' and score_previsto < score_atual:
            recomendacao['necessaria'] = True
            recomendacao['prioridade'] = 'média'
            recomendacao['quantidade_mm'] = 25
            recomendacao['urgencia_horas'] = 36
            recomendacao['justificativa'] = (
                f"Modelo prevê queda de umidade para {umidade_prevista:.1f}%. "
                f"Irrigação preventiva recomendada."
            )
        
        # Umidade ideal
        else:
            recomendacao['justificativa'] = (
                f"Umidade do solo em nível adequado ({umidade_atual:.1f}%). "
                f"Irrigação não necessária no momento."
            )
        
        return recomendacao
    
    def recomendar_correcao_ph(self, ph_atual: float, 
                               ph_previsto: float) -> Dict:
        """
        Recomenda correção de pH do solo.
        
        Args:
            ph_atual: pH atual do solo
            ph_previsto: pH previsto pelo modelo
            
        Returns:
            Dicionário com recomendação de correção
        """
        nivel_atual, score_atual = self.calcular_criticidade(ph_atual, 'ph_solo')
        nivel_previsto, _ = self.calcular_criticidade(ph_previsto, 'ph_solo')
        
        recomendacao = {
            'tipo_acao': 'correcao_ph',
            'prioridade': 'baixa',
            'necessaria': False,
            'produto': '',
            'quantidade_kg_hectare': 0,
            'urgencia_dias': 14,
            'justificativa': ''
        }
        
        ideal = self.FAIXAS_IDEAIS['ph_solo']['ideal']
        
        # pH muito baixo (solo ácido)
        if ph_atual < self.FAIXAS_IDEAIS['ph_solo']['min']:
            recomendacao['necessaria'] = True
            recomendacao['prioridade'] = 'alta' if nivel_atual == 'crítico' else 'média'
            recomendacao['produto'] = 'Calcário dolomítico'
            # Quanto mais ácido, mais calcário necessário
            recomendacao['quantidade_kg_hectare'] = (ideal - ph_atual) * 500
            recomendacao['urgencia_dias'] = 7 if nivel_atual == 'crítico' else 14
            recomendacao['justificativa'] = (
                f"pH do solo baixo ({ph_atual:.2f}), indicando acidez. "
                f"Aplicação de calcário recomendada para elevar pH."
            )
        
        # pH muito alto (solo alcalino)
        elif ph_atual > self.FAIXAS_IDEAIS['ph_solo']['max']:
            recomendacao['necessaria'] = True
            recomendacao['prioridade'] = 'média'
            recomendacao['produto'] = 'Enxofre elementar'
            recomendacao['quantidade_kg_hectare'] = (ph_atual - ideal) * 300
            recomendacao['urgencia_dias'] = 14
            recomendacao['justificativa'] = (
                f"pH do solo alto ({ph_atual:.2f}), indicando alcalinidade. "
                f"Aplicação de enxofre recomendada para reduzir pH."
            )
        
        # pH ideal
        else:
            recomendacao['justificativa'] = (
                f"pH do solo em nível adequado ({ph_atual:.2f}). "
                f"Correção não necessária no momento."
            )
        
        return recomendacao
    
    def recomendar_fertilizacao(self, rendimento_previsto: float,
                               ph_atual: float,
                               umidade_atual: float) -> Dict:
        """
        Recomenda fertilização baseada no rendimento esperado.
        
        Args:
            rendimento_previsto: Rendimento previsto pelo modelo (ton/ha)
            ph_atual: pH atual do solo
            umidade_atual: Umidade atual do solo
            
        Returns:
            Dicionário com recomendação de fertilização
        """
        nivel_rendimento, score_rendimento = self.calcular_criticidade(
            rendimento_previsto, 'rendimento_esperado'
        )
        
        recomendacao = {
            'tipo_acao': 'fertilizacao',
            'prioridade': 'baixa',
            'necessaria': False,
            'npk_formula': '',
            'quantidade_kg_hectare': 0,
            'urgencia_dias': 7,
            'justificativa': ''
        }
        
        # Condições para absorção de nutrientes
        ph_ok = self.FAIXAS_IDEAIS['ph_solo']['min'] <= ph_atual <= self.FAIXAS_IDEAIS['ph_solo']['max']
        umidade_ok = umidade_atual >= self.FAIXAS_IDEAIS['umidade_solo']['min']
        
        # Rendimento previsto baixo
        if rendimento_previsto < self.FAIXAS_IDEAIS['rendimento_esperado']['min']:
            recomendacao['necessaria'] = True
            recomendacao['prioridade'] = 'alta'
            
            # Se pH ou umidade não estão ideais, ajustar primeiro
            if not ph_ok or not umidade_ok:
                recomendacao['prioridade'] = 'média'
                recomendacao['urgencia_dias'] = 14
                recomendacao['justificativa'] = (
                    f"Rendimento previsto baixo ({rendimento_previsto:.2f} ton/ha). "
                    f"Porém, antes da fertilização, ajustar "
                    f"{'pH' if not ph_ok else ''}"
                    f"{' e ' if not ph_ok and not umidade_ok else ''}"
                    f"{'umidade' if not umidade_ok else ''} do solo."
                )
            else:
                recomendacao['npk_formula'] = '20-10-10'  # Maior N para crescimento
                recomendacao['quantidade_kg_hectare'] = 400
                recomendacao['urgencia_dias'] = 7
                recomendacao['justificativa'] = (
                    f"Rendimento previsto abaixo do esperado ({rendimento_previsto:.2f} ton/ha). "
                    f"Fertilização nitrogenada recomendada para estimular crescimento."
                )
        
        # Rendimento moderado - fertilização de manutenção
        elif self.FAIXAS_IDEAIS['rendimento_esperado']['min'] <= rendimento_previsto < self.FAIXAS_IDEAIS['rendimento_esperado']['ideal']:
            recomendacao['necessaria'] = True
            recomendacao['prioridade'] = 'média'
            recomendacao['npk_formula'] = '10-10-10'  # Balanceado
            recomendacao['quantidade_kg_hectare'] = 250
            recomendacao['urgencia_dias'] = 14
            recomendacao['justificativa'] = (
                f"Rendimento previsto moderado ({rendimento_previsto:.2f} ton/ha). "
                f"Fertilização balanceada recomendada para otimizar produção."
            )
        
        # Rendimento ideal
        else:
            recomendacao['justificativa'] = (
                f"Rendimento previsto excelente ({rendimento_previsto:.2f} ton/ha). "
                f"Manter práticas atuais de manejo."
            )
        
        return recomendacao
    
    def gerar_plano_manejo_completo(self, dados_atuais: Dict, 
                                   previsoes: Dict) -> List[Dict]:
        """
        Gera um plano completo de manejo agrícola.
        
        Args:
            dados_atuais: Dicionário com dados atuais dos sensores
            previsoes: Dicionário com previsões dos modelos
            
        Returns:
            Lista de recomendações ordenadas por prioridade
        """
        recomendacoes = []
        
        # Recomendação de irrigação
        rec_irrigacao = self.recomendar_irrigacao(
            dados_atuais.get('umidade_solo', 0),
            previsoes.get('umidade_prevista', 0)
        )
        if rec_irrigacao['necessaria']:
            recomendacoes.append(rec_irrigacao)
        
        # Recomendação de correção de pH
        rec_ph = self.recomendar_correcao_ph(
            dados_atuais.get('ph_solo', 0),
            previsoes.get('ph_previsto', 0)
        )
        if rec_ph['necessaria']:
            recomendacoes.append(rec_ph)
        
        # Recomendação de fertilização
        rec_fertilizacao = self.recomendar_fertilizacao(
            previsoes.get('rendimento_previsto', 0),
            dados_atuais.get('ph_solo', 0),
            dados_atuais.get('umidade_solo', 0)
        )
        if rec_fertilizacao['necessaria']:
            recomendacoes.append(rec_fertilizacao)
        
        # Ordena por prioridade
        ordem_prioridade = {'alta': 0, 'média': 1, 'baixa': 2}
        recomendacoes.sort(key=lambda x: ordem_prioridade[x['prioridade']])
        
        return recomendacoes
    
    def salvar_recomendacoes_bd(self, cultura_id: int, recomendacoes: List[Dict]):
        """
        Salva as recomendações no banco de dados.
        
        Args:
            cultura_id: ID da cultura
            recomendacoes: Lista de recomendações
        """
        for rec in recomendacoes:
            # Prepara descrição detalhada
            descricao = rec['justificativa']
            
            if rec['tipo_acao'] == 'irrigacao':
                quantidade = rec['quantidade_mm']
                unidade = 'mm'
            elif rec['tipo_acao'] == 'correcao_ph':
                quantidade = rec['quantidade_kg_hectare']
                unidade = 'kg/ha'
                descricao += f" Produto: {rec['produto']}"
            elif rec['tipo_acao'] == 'fertilizacao':
                quantidade = rec['quantidade_kg_hectare']
                unidade = 'kg/ha'
                descricao += f" Fórmula: {rec['npk_formula']}"
            else:
                quantidade = 0
                unidade = ''
            
            # Insere no banco
            self.db.inserir_acao_manejo(
                cultura_id=cultura_id,
                tipo_acao=rec['tipo_acao'],
                descricao=descricao,
                quantidade=quantidade,
                unidade=unidade
            )


if __name__ == "__main__":
    # Teste do sistema
    db = DatabaseManager()
    sistema = SistemaRecomendacao(db)
    
    # Dados de exemplo
    dados_teste = {
        'umidade_solo': 25.0,
        'ph_solo': 5.8,
        'temperatura_solo': 24.0
    }
    
    previsoes_teste = {
        'umidade_prevista': 22.0,
        'ph_previsto': 5.7,
        'rendimento_previsto': 6.5
    }
    
    print("\nTESTE DO SISTEMA DE RECOMENDAÇÕES\n")
    print("Dados atuais:")
    for k, v in dados_teste.items():
        print(f"  {k}: {v}")
    
    print("\nPrevisões:")
    for k, v in previsoes_teste.items():
        print(f"  {k}: {v}")
    
    print("\n" + "="*60)
    print("RECOMENDAÇÕES GERADAS:")
    print("="*60)
    
    recomendacoes = sistema.gerar_plano_manejo_completo(dados_teste, previsoes_teste)
    
    for i, rec in enumerate(recomendacoes, 1):
        print(f"\n{i}. {rec['tipo_acao'].upper()} - Prioridade: {rec['prioridade'].upper()}")
        print(f"   {rec['justificativa']}")
        
        if rec['tipo_acao'] == 'irrigacao':
            print(f"   Quantidade: {rec['quantidade_mm']} mm")
            print(f"   Urgência: {rec['urgencia_horas']} horas")
        elif 'quantidade_kg_hectare' in rec:
            print(f"   Quantidade: {rec['quantidade_kg_hectare']:.0f} kg/ha")

