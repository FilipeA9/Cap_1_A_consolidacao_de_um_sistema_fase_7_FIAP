# Arquitetura da Solução — Fase 7

## Visão geral

```
                        ┌──────────────────────────────────────────┐
                        │   DASHBOARD STREAMLIT (dashboard/)       │
                        │   1 página por serviço + home  ◄── botões │
                        └──────────────┬───────────────────────────┘
                                       │            ▲
            main.py (CLI) ─────────────┤            │ comandos de terminal
                                       ▼            │
┌────────────┐  ┌─────────────┐  ┌───────────────────────┐
│ ESP32/Wokwi│  │ OpenWeather │  │  SERVIÇOS (services/) │
│ sketch.ino │  │     API     │  │  fase1..fase6, alertas│
└─────┬──────┘  └──────┬──────┘  └──────────┬────────────┘
      │ log/serial     │ requests           │
      ▼                ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│        SQLite database/farmtech.db (Fases 2/3)           │
│  sensores · leituras · culturas · ações · previsões ·    │
│  eventos_irrigacao · deteccoes_visao · alertas           │
└───────────────┬──────────────────────────┬───────────────┘
                │                          │
                ▼                          ▼
   ┌────────────────────────┐   ┌────────────────────────┐
   │ ML Fase 4 (.pkl) e     │   │ alert_engine.py        │
   │ Fase 5 (crop_yield) +  │   │ (regras do grupo)      │
   │ YOLO Fase 6 (best.pt)  │   │      │ boto3           │
   └────────────────────────┘   │      ▼                 │
                                │ AWS SNS sa-east-1      │
                                │ tópico farmtech-alertas│
                                │   → e-mail / SMS       │
                                └────────────────────────┘
```

## Princípios

1. **Um serviço por pasta, duas formas de disparo** (botão na dashboard ou
   `python main.py <comando>`), atendendo literalmente o enunciado.
2. **Banco único como ponto de integração:** todas as fases leem/escrevem
   no mesmo SQLite; o Oracle é suportado via DDL + exportação CSV.
3. **Degradação graciosa:** sem chave OpenWeather → aviso; sem R → fallback
   Python; sem `best.pt` → fallback YOLO/COCO; sem SNS → modo simulado com
   registro no banco. Nenhuma página quebra por dependência externa.
4. **Segredos via `.env`** (python-dotenv), nunca versionados.
