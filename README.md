# FIAP - Faculdade de Informática e Administração Paulista

![FIAP Logo](https://www.fiap.com.br/wp-content/themes/fiap2016/images/sharing/fiap.png)

# FarmTech Solutions — Sistema Integrado de Gestão Agrícola (Fase 7)

## 👨‍🎓 Integrantes:

- Diogo Ferreira Pereira
- André Victor Gonçalves Toledo
- Johnathan da Cruz Gatt
- Laisa Cristina Capodifoglio Andrade
- Filipe Augusto Lima Silva

## 👩‍🏫 Professores:

**Tutor(a)**

- Sabrina Otoni

**Coordenador(a)**

- ANDRÉ GODOI CHIOVATO

---

## 📜 Descrição

A **Fase 7** consolida tudo o que a FarmTech Solutions construiu nas Fases 1
a 6 em **uma única pasta de projeto Python**: uma dashboard central (evolução
da dashboard da Fase 4) em que cada serviço é disparado **por botão** ou,
alternativamente, **por comando no terminal** (`python main.py <serviço>`).

| Página da dashboard | Serviço integrado | Fase de origem |
|---|---|---|
| 📐 Área e Insumos | Cálculo de área (café/cana), insumos, CRUD em vetores + análise R | Fase 1 |
| 🗄️ Banco de Dados | CRUD nas tabelas, consultas SQL, MER/DER, DDL e exportação Oracle | Fases 2/3 *(recuperada)* |
| 💧 Irrigação IoT | Lógica do ESP32 (NPK/LDR/DHT22/relé), clima OpenWeather, log Wokwi | Fase 2 |
| 🤖 Previsões ML | Modelos de umidade, pH e rendimento + recomendações de manejo | Fase 4 |
| 📈 Rendimento Safra | EDA, K-Means, outliers e 5 modelos de regressão (crop_yield) | Fase 5 |
| 👁️ Visão Computacional | YOLO: maçãs (frutos) × garrafas (objetos estranhos) em imagens estáticas | Fase 6 |
| 🚨 Alertas AWS | Mensageria SNS: e-mail/SMS com ações corretivas aos funcionários | **Fase 7 (nova)** |

> A entrega da Fase 3 (banco Oracle) não havia sido realizada nas fases
> anteriores e foi **recuperada nesta Fase 7**: MER/DER documentado
> (`docs/mer_der/`), DDL Oracle (`services/fase3_banco/ddl_oracle.sql`) e
> exportação CSV pronta para o Oracle SQL Developer.
> O mapeamento completo serviço ↔ fase (incluindo as diferenças de numeração
> do enunciado) está em `docs/fases_origem/mapeamento_fases.md`.

## 📁 Estrutura de pastas

```
farmtech-fase7/
├── main.py                  # CLI: dispara qualquer serviço via terminal
├── setup_projeto.py         # bootstrap: BD + dados simulados + treino ML
├── dashboard/               # dashboard Streamlit (home + 7 páginas)
├── services/
│   ├── core/                # configuração central (.env, caminhos)
│   ├── fase1_calculos/      # área/insumos + clima.R (Fase 1)
│   ├── fase2_iot/           # sketch.ino, diagram.json, clima, simulador (Fase 2)
│   ├── fase3_banco/         # db_manager unificado, DDL Oracle, exportação
│   ├── fase4_ml/            # modelos ML, recomendação, simulador de sensores
│   ├── fase5_rendimento/    # pipeline crop_yield (5 modelos + clusters)
│   ├── fase6_visao/         # YOLO: treino, inferência, dataset (80 imagens)
│   └── alertas/             # motor de alertas + publicador AWS SNS
├── database/                # farmtech.db (gerado pelo setup)
├── docs/                    # arquitetura, MER/DER, AWS, mapeamento de fases
├── notebooks/               # notebooks originais das Fases 5 e 6
└── assets/                  # circuito Wokwi e imagens
```

## 🔧 Como executar o código

### Pré-requisitos

- Python 3.10+ · pip · Git
- (Opcional) R + Rscript — para a análise estatística original da Fase 1
- (Opcional) Conta AWS — para o envio real de alertas via SNS
- (Opcional) `pip install ultralytics` — para treino/inferência YOLO da Fase 6

### Instalação

```bash
git clone <url-do-repositorio>
cd farmtech-fase7
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env             # preencher OpenWeather e AWS (opcional)
python setup_projeto.py          # cria BD, popula dados e treina os modelos
```

### Execução

```bash
streamlit run dashboard/app.py   # dashboard integradora (botões)
python main.py --help            # todos os serviços via terminal
```

Principais comandos de terminal (equivalentes aos botões):

```bash
python main.py fase1             # menu da Fase 1 (área/insumos)
python main.py clima-r           # análise R / fallback Python (Fase 1)
python main.py clima             # OpenWeather + recomendação (Fase 2)
python main.py simular --ciclos 10   # simulador de irrigação ESP32 (Fase 2)
python main.py exportar-oracle   # CSVs para o Oracle SQL Developer (Fase 3)
python main.py treinar-ml        # treina os modelos da Fase 4
python main.py rendimento        # pipeline crop_yield (Fase 5)
python main.py treinar-yolo      # treina o YOLO local → best.pt (Fase 6)
python main.py visao             # detecção nas imagens de teste (Fase 6)
python main.py alertas           # motor de alertas + AWS SNS (Fase 7)
```

## 🚨 Serviço de Mensageria AWS (SNS)

O motor de alertas (`services/alertas/`) monitora **os sensores das Fases
1/2 e as análises de visão computacional da Fase 6** e publica no tópico SNS
`farmtech-alertas` (região **sa-east-1**, escolhida pela análise de latência
e soberania de dados da Fase 5). Os funcionários assinam o tópico por
**e-mail** (e opcionalmente SMS) e recebem a ação corretiva.

### Regras e ações corretivas definidas pelo grupo

| Origem | Condição monitorada | Ação corretiva enviada |
|---|---|---|
| IoT (Fase 2) | Umidade < 60% | Verificar bomba / acionar irrigação manual |
| IoT (Fase 2) | pH (LDR) fora de 1500–2500 | Aplicar calcário (ácido) ou enxofre (alcalino) |
| IoT (Fase 2) | N, P ou K ausentes | Aplicar fertilizante NPK (dosagem da Fase 4) |
| Clima (Fase 2) | Chuva prevista (≥30% ou ≥2 mm) | Manter bombas desligadas (economia de água) |
| Sensores (Fase 4) | Umidade do solo < 30% | Irrigação imediata de ~30 mm no talhão |
| Sensores (Fase 4) | pH fora de 5,5–7,0 | Correção do solo conforme recomendação |
| Visão (Fase 6) | Garrafa/objeto estranho detectado | Equipe de limpeza no talhão (risco à colheitadeira) |

Passo a passo completo de criação do tópico, subscriptions e usuário IAM:
[`docs/aws/passo_a_passo_sns.md`](docs/aws/passo_a_passo_sns.md).

### Prints da solução na AWS

> 📸 *[INSERIR PRINT 1: tópico `farmtech-alertas` criado (nome + ARN)]*
>
> 📸 *[INSERIR PRINT 2: subscriptions confirmadas (e-mail/SMS)]*
>
> 📸 *[INSERIR PRINT 3: policy `sns:Publish` do usuário IAM `farmtech-app`]*
>
> 📸 *[INSERIR PRINT 4: e-mail/SMS recebido com o alerta e a ação corretiva]*
>
> 📸 *[INSERIR PRINT 5: terminal com o MessageId retornado pelo publish]*

Sem credenciais AWS configuradas o sistema opera em **modo simulado**: os
alertas são registrados na tabela `alertas` e exibidos na dashboard, sem
envio — útil para desenvolvimento e correção offline.

## ☁️ Infraestrutura AWS (Fase 5)

Estimativa para a máquina de hospedagem (2 vCPUs, 1 GiB RAM, até 5 Gbps,
50 GB EBS, On-Demand 100%), via Calculadora AWS:

| Região | Custo mensal estimado |
|---|---|
| US East (N. Virginia) | US$ 8,63 |
| **South America (São Paulo)** | **US$ 15,78** |

Apesar do custo maior, **São Paulo (sa-east-1)** foi a região escolhida:
menor latência para os sensores no Brasil e conformidade com restrições
legais de armazenamento de dados no exterior — decisão herdada da Fase 5 e
aplicada ao SNS da Fase 7.

## 🎥 Vídeo de demonstração

> 🔗 *[INSERIR LINK DO YOUTUBE — vídeo de até 10 minutos, "não listado",
> apresentando as funcionalidades das Fases 1 a 6 + alertas AWS]*

Roteiro sugerido (10 min): visão geral e arquitetura (1 min) → Fase 1
área/insumos + R (1,5 min) → Fases 2/3 banco + Oracle (1,5 min) → Fase 2
IoT/Wokwi + clima (1,5 min) → Fase 4 previsões (1,5 min) → Fase 5 rendimento
(1 min) → Fase 6 visão computacional (1 min) → alerta chegando por e-mail
via SNS (1 min).

## 🗃 Histórico de lançamentos

- 1.0.0 — Fase 7: integração das Fases 1–6 + mensageria AWS SNS

## 📋 Licença

Projeto acadêmico desenvolvido para o curso de IA da FIAP — uso educacional.
