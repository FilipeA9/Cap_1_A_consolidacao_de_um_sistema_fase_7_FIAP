# Mapeamento Serviço ↔ Fase de Origem

O recap do enunciado da Fase 7 usa uma numeração ligeiramente diferente da
ordem em que as entregas foram feitas (chama "Fase 2" o banco de dados e
"Fase 3" o IoT). Para evitar ambiguidade, este projeto se organiza por
**serviço**, e a tabela abaixo faz o duplo mapeamento.

| Serviço na Fase 7 | Pasta | Entrega de origem | Nome no recap da F7 |
|---|---|---|---|
| Área de plantio e insumos + R | `services/fase1_calculos/` | Fase 1 (`farmtech_app.py`, `streamlit_app.py`, `Calculo de dados e tempo.R`) | Fase 1 — Base de Dados Inicial |
| IoT / irrigação inteligente ESP32 | `services/fase2_iot/` | Fase 2 (`sketch.ino`, `diagram.json`, `integracao_clima.py`, `log_irrigacao.txt`) | Fase 3 — IoT e Automação |
| Banco de dados estruturado (MER/DER, Oracle) | `services/fase3_banco/` | Fase 3 — **não entregue, recuperada na Fase 7** | Fase 2 — Banco de Dados Estruturado |
| Dashboard + ML + recomendações | `services/fase4_ml/` e `dashboard/` | Fase 4 (`app.py`, `db_manager.py`, `ml_models.py`, `recommendation_system.py`, `sensor_simulator.py`) | Fase 4 — Dashboard com Data Science |
| Análise de rendimento (5 modelos, clusters) | `services/fase5_rendimento/` | Fase 5 (notebook `crop_yield`) | Fase 5 — Cloud & Segurança (parte ML) |
| Custos/infra AWS | README (seção AWS) + `docs/aws/` | Fase 5 (análise calculadora AWS) | Fase 5 — Cloud Computing |
| Visão computacional YOLO | `services/fase6_visao/` | Fase 6 (notebooks + dataset 80 imagens) | Fase 6 — Visão Computacional |
| Mensageria de alertas AWS SNS | `services/alertas/` | **Nova na Fase 7** | Fase 7 — Consolidação |

## Ajustes de consistência feitos na integração

1. **Narrativa de culturas unificada:** café e cana-de-açúcar são as culturas
   principais da fazenda (Fases 1 e 2); o `crop_yield.csv` atua como base
   histórica regional para o módulo de rendimento (Fase 5); a Fase 6 foi
   reposicionada como monitoramento visual da lavoura — detecção de frutos
   (maçãs do pomar experimental) e de objetos estranhos/descarte irregular
   (garrafas), que alimenta o serviço de alertas.
2. **Segredos removidos do código:** a chave OpenWeather (exposta na entrega
   da Fase 2) e o token Ubidots (Fase 5) saíram do código-fonte; tudo via
   `.env`. **As chaves antigas devem ser revogadas.**
3. **Nomenclatura:** o notebook da Fase 5 (nomeado `..._pbl_fase4.ipynb` na
   entrega original) foi renomeado para `..._pbl_fase5.ipynb` em `notebooks/`.
4. **Banco único:** o schema SQLite da Fase 4 foi estendido (eventos de
   irrigação, detecções de visão e alertas) e ganhou DDL Oracle equivalente,
   recuperando a Fase 3.
5. **`venv/` e artefatos gerados não são versionados** (`.gitignore`).

## Links das entregas originais

- Fase 1: https://github.com/diogoopereira/FarmTech-Solutions---FIAP
- Fase 2: https://github.com/diogoopereira/Cap-1---Um-Mapa-do-Tesouro
- (Adicionar os links dos repositórios das Fases 4, 5 e 6 do grupo)
