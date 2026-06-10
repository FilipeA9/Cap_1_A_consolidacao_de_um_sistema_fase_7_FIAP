readme: 

# Fase 7 - Ir Além

## Objetivo

Desenvolver uma solução de otimização agrícola utilizando Algoritmos Genéticos para selecionar os melhores insumos agrícolas considerando restrições orçamentárias.

## Contexto

A FarmTech Solutions trabalha com o monitoramento e gerenciamento de culturas agrícolas. Nas fases anteriores foram desenvolvidas soluções relacionadas ao controle de áreas cultivadas, irrigação e aplicação de insumos.

Nesta etapa foi implementado um Algoritmo Genético para otimizar a escolha dos recursos agrícolas, buscando maximizar a produtividade sem ultrapassar o orçamento disponível.

## Alterações Realizadas

Foram realizadas modificações em relação ao algoritmo apresentado em aula:

### Seleção

Substituição da seleção por roleta pela Seleção por Torneio.

### Crossover

Substituição do crossover de um ponto por crossover de dois pontos.

### Mutação

Implementação de mutação adaptativa, utilizando taxa maior nas gerações iniciais e menor nas gerações finais.

## Resultados

A solução encontrada apresentou melhor aproveitamento dos recursos disponíveis e maior diversidade genética da população ao longo das gerações.

## Conclusão

Os resultados demonstraram que pequenas alterações nos operadores genéticos podem impactar positivamente a qualidade da solução encontrada para problemas de otimização agrícola.