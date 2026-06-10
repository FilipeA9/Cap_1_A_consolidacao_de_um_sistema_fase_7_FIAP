# Modelo de Dados — MER/DER (recuperação da Fase 3)

A entrega da Fase 3 (banco relacional com os dados de sensores) não havia
sido realizada; a Fase 7 a recupera com este modelo, implementado em SQLite
(operacional, `database/farmtech.db`) e com DDL Oracle equivalente
(`services/fase3_banco/ddl_oracle.sql`) para importação no Oracle SQL
Developer conforme o passo a passo do enunciado original.

## DER (diagrama entidade-relacionamento)

```mermaid
erDiagram
    SENSORES ||--o{ LEITURAS_SENSORES : registra
    SENSORES ||--o{ CULTURAS : monitora
    SENSORES ||--o{ PREVISOES : origina
    CULTURAS ||--o{ ACOES_MANEJO : recebe
    CULTURAS ||--o{ PRODUCAO : gera

    SENSORES {
        int id PK
        text nome
        text tipo
        text localizacao
        bool ativo
        timestamp data_instalacao
    }
    LEITURAS_SENSORES {
        int id PK
        int sensor_id FK
        timestamp timestamp
        real umidade_solo
        real temperatura_solo
        real ph_solo
        real temperatura_ar
        real umidade_ar
        real luminosidade
        real rendimento_kg_hectare
    }
    CULTURAS {
        int id PK
        text nome
        text tipo
        date data_plantio
        date data_colheita_prevista
        real area_hectares
        int sensor_id FK
    }
    ACOES_MANEJO {
        int id PK
        int cultura_id FK
        text tipo_acao
        text descricao
        real quantidade
        text unidade
        bool executada
    }
    PRODUCAO {
        int id PK
        int cultura_id FK
        date data_colheita
        real rendimento_kg_hectare
        text qualidade
    }
    PREVISOES {
        int id PK
        int sensor_id FK
        real umidade_prevista
        real ph_previsto
        real rendimento_previsto
        real confianca
    }
    EVENTOS_IRRIGACAO {
        int id PK
        real umidade
        int ph_ldr
        bool nivel_n
        bool nivel_p
        bool nivel_k
        bool previsao_chuva
        bool bomba_ligada
        text motivo
        text fonte
    }
    DETECCOES_VISAO {
        int id PK
        text imagem
        text classe
        real confianca
        text modelo
    }
    ALERTAS {
        int id PK
        text origem
        text tipo
        text severidade
        text mensagem
        text acao_corretiva
        bool enviado_sns
        text sns_message_id
    }
```

## Entidades e papel por fase

| Tabela | Fase de origem | Papel |
|---|---|---|
| sensores | 4 | Cadastro dos dispositivos IoT por talhão |
| leituras_sensores | 3/4 | Telemetria (umidade, pH, temperatura, etc.) |
| culturas | 1/4 | Talhões e áreas calculadas (Fase 1 grava aqui) |
| acoes_manejo | 4 | Recomendações do sistema especialista |
| producao | 4 | Histórico de colheitas |
| previsoes | 4 | Saídas dos modelos de ML |
| eventos_irrigacao | 2 (nova na F7) | Ciclos de decisão do ESP32/simulador |
| deteccoes_visao | 6 (nova na F7) | Detecções YOLO (maçã/garrafa) |
| alertas | 7 (nova) | Histórico da mensageria AWS SNS |

## Decisões de modelagem

Relação 1:N entre `sensores` e `leituras_sensores` mantém a telemetria
normalizada; `eventos_irrigacao`, `deteccoes_visao` e `alertas` são tabelas
de eventos sem FK rígida porque suas fontes (firmware ESP32, YOLO e motor
de alertas) operam de forma independente do cadastro de sensores — decisão
que simplifica a ingestão vinda do Wokwi/log da Fase 2.
