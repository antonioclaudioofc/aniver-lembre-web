# Motor de lembretes de aniversário

Núcleo em `reminders/services.py`. Não existe worker/agendador embutido no
Django — o "motor" só roda quando algo chama `send_due_reminders()`, seja
via HTTP (produção) ou via management command (manual/local).

## Como é disparado

```
cron-job.org (externo, grátis)
   │  GET a cada N minutos
   ▼
GET /reminders/run-check/?token=CRON_SECRET
   │
   ▼
reminders.views.run_due_reminders
   │  valida o token (hmac.compare_digest) → 403 se inválido/ausente
   ▼
reminders.services.send_due_reminders()
```

Não há `vercel.json`, `build_files.sh` nem `Procfile` configurando isso —
o agendamento inteiro depende de um serviço externo. Ver
[`environment.md`](environment.md) para a variável `CRON_SECRET` e o passo
a passo de configuração do cron-job.org.

Também dá pra rodar manualmente:

```bash
python manage.py send_due_reminders
```
(`reminders/management/commands/send_due_reminders.py`, um wrapper fino
sobre o mesmo `send_due_reminders()`.)

## Algoritmo (`send_due_reminders()`)

Para cada `Reminder` com `active=True`:

1. **Guarda de idempotência**: se `last_notified_year == ano atual`, pula
   — já foi enviado esse ano, não importa quantas vezes o endpoint seja
   chamado no mesmo dia.
2. **`_matching_occurrence(birthday, days_before, today)`**: calcula, para
   a ocorrência do aniversário **deste ano** e **do ano seguinte**, a data
   alvo (`ocorrência - days_before dias`). Se `today` bater com uma delas,
   retorna essa ocorrência; senão `None`.
   - Checar os dois anos (não só o atual) é o que resolve o caso de um
     aniversário em janeiro com `days_before` grande — a data-alvo pode
     cair em dezembro do ano anterior.
   - Aniversário em 29/fev: o `.replace(year=...)` levanta `ValueError`
     em anos não bissextos — capturado e ignorado (o lembrete simplesmente
     não dispara em anos não bissextos).
3. **Horário**: se `now.time() < reminder.notify_at`, pula — ainda não
   chegou a hora hoje. `now` é calculado explicitamente em
   `America/Sao_Paulo` (`ZoneInfo(settings.TIME_ZONE)`), não depende de
   nenhuma timezone "ativa" do request.
4. **E-mail do dono**: se `contact.owner.user.email` estiver vazio, pula
   (loga um warning) — pode acontecer com contas antigas que nunca tiveram
   e-mail obrigatório.
5. **Envia o e-mail** (`EmailMultiAlternatives`, texto + HTML) usando os
   templates em `reminders/templates/emails/`, calcula `turning` (quantos
   anos a pessoa fará) a partir do ano da ocorrência batida no passo 2.
6. Marca `last_notified_year = ano atual` e salva.

Retorna quantos e-mails foram enviados nessa chamada.

## Por que rodar a cada 1 minuto é seguro

O guard do passo 1 é por **ano**, não por chamada — chamar o endpoint com
qualquer frequência não duplica envios. Rodar mais frequentemente só deixa
o horário (`notify_at`) mais preciso (o e-mail sai em até 1 minuto do
horário configurado, em vez de esperar o próximo ciclo de um agendamento
mais espaçado).

## Templates de e-mail

`reminders/templates/emails/birthday_reminder.html` e `.txt` — HTML em
tabelas (compatibilidade com Outlook), estilos inline, `prefers-color-scheme`
para dark mode nos clientes que suportam. A logo usa uma imagem PNG
hospedada em `base_static/images/logo-email.png` (servida via
`{{ site_url }}` + `{% static %}` resolvido em Python, não SVG — ver
[`front/styling.md`](../front/styling.md) para o porquê).

## Endpoint (`reminders.views.run_due_reminders`)

```python
def run_due_reminders(request):
    token = request.GET.get('token', '')
    if not settings.CRON_SECRET or not hmac.compare_digest(token, settings.CRON_SECRET):
        return JsonResponse({'detail': 'Forbidden'}, status=403)
    sent = send_due_reminders()
    return JsonResponse({'sent': sent})
```

- Sem autenticação de sessão — de propósito, já que quem chama é um
  serviço externo sem cookies. A segurança é inteiramente o token.
- `hmac.compare_digest` evita timing attack na comparação do token.
- Sem `CRON_SECRET` configurado, o endpoint fica permanentemente
  inacessível (`403`), nunca "aberto por acidente".
