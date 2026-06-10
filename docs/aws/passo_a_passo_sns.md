# Serviço de Mensageria AWS (SNS) — Passo a Passo

Este documento descreve a criação da infraestrutura de alertas exigida na
Fase 7. Após executar os passos, capture os prints indicados e cole-os nas
seções marcadas (eles são exigidos no README do GitHub).

## Arquitetura

```
[eventos_irrigacao / leituras_sensores / deteccoes_visao]  (SQLite)
                      │
                      ▼
        alert_engine.py (regras do grupo)
                      │ boto3 sns:Publish
                      ▼
   Tópico SNS "farmtech-alertas"  (sa-east-1, São Paulo)
        │                         │
   Subscription e-mail       Subscription SMS (opcional)
        ▼                         ▼
  funcionários da fazenda recebem a ação corretiva
```

A região **sa-east-1 (São Paulo)** foi escolhida em coerência com a análise
da Fase 5: menor latência para os sensores no Brasil e soberania de dados
(restrições legais ao armazenamento no exterior).

## Passo 1 — Criar o tópico SNS

1. Console AWS → serviço **Simple Notification Service (SNS)**.
2. Confirme a região **América do Sul (São Paulo) sa-east-1** no canto superior direito.
3. *Topics* → *Create topic* → tipo **Standard**.
4. Nome: `farmtech-alertas` → *Create topic*.
5. Copie o **ARN** gerado (formato `arn:aws:sns:sa-east-1:<id-da-conta>:farmtech-alertas`).

> 📸 **PRINT 1:** tela do tópico criado mostrando nome e ARN.

## Passo 2 — Assinar e-mail (e SMS opcional)

1. Dentro do tópico → *Create subscription*.
2. Protocol: **Email** → Endpoint: e-mail dos integrantes → *Create subscription*.
3. Cada integrante abre o e-mail "AWS Notification - Subscription Confirmation"
   e clica em **Confirm subscription**.
4. (Opcional) Repita com Protocol **SMS** e o celular no formato `+55DDDNÚMERO`.
   SMS exige configurar *Text messaging preferences* (spending limit).

> 📸 **PRINT 2:** lista de subscriptions com status **Confirmed**.

## Passo 3 — Usuário IAM com permissão mínima

1. Console AWS → **IAM** → *Users* → *Create user* → nome `farmtech-app`
   (sem acesso ao console).
2. *Attach policies directly* → *Create policy* (JSON):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sns:Publish",
    "Resource": "arn:aws:sns:sa-east-1:<id-da-conta>:farmtech-alertas"
  }]
}
```

3. Após criar o usuário: *Security credentials* → *Create access key*
   (caso de uso: aplicação executada fora da AWS).

> 📸 **PRINT 3:** policy anexada ao usuário `farmtech-app`.

## Passo 4 — Configurar o projeto

```bash
cp .env.example .env
# editar .env:
#   AWS_REGION=sa-east-1
#   SNS_TOPIC_ARN=arn:aws:sns:sa-east-1:<id-da-conta>:farmtech-alertas
#   AWS_ACCESS_KEY_ID=...
#   AWS_SECRET_ACCESS_KEY=...
```

## Passo 5 — Testar

```bash
python main.py alertas                      # roda as regras sobre os dados
python -m services.alertas.sns_publisher    # envia mensagem de teste
```

Ou pela dashboard: página **Alertas AWS** → botão *Enviar alerta de TESTE*.

> 📸 **PRINT 4:** e-mail recebido com o alerta FarmTech (assunto
> `[FarmTech][...]`) e/ou SMS no celular.
> 📸 **PRINT 5:** terminal mostrando o `MessageId` retornado pelo publish.

## Custos

SNS possui free tier de 1.000 notificações de e-mail/mês — suficiente para
o projeto. SMS no Brasil é cobrado por mensagem (por isso o e-mail é o canal
principal demonstrado).
