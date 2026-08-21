# Models

## Diagrama de relacionamento

```
User (django.contrib.auth)
  └── 1:1 ── Profile
                └── 1:N ── Contact
                              └── 1:N ── Reminder
```

Todo dado do app é escopado por dono através de `Contact.owner → Profile → User`.
Não existe compartilhamento de contatos entre usuários.

## `accounts.Profile`

Estende o `User` padrão do Django (`django.contrib.auth.models.User`) com
um perfil próprio — usado tanto para o dono dos contatos quanto para o
estado da verificação de e-mail.

| Campo | Tipo | Notas |
|---|---|---|
| `user` | `OneToOneField(User)` | `on_delete=CASCADE`. Mensagens de erro customizadas para unicidade/nulo. |
| `updated_at` | `DateTimeField(auto_now=True)` | |
| `email_verified` | `BooleanField(default=False)` | `True` só depois do código de verificação ser confirmado. |
| `verification_code` | `CharField(max_length=6, blank=True)` | Código numérico atual pendente (vazio depois de verificado). |
| `verification_sent_at` | `DateTimeField(null=True, blank=True)` | Usado para calcular expiração (15 min) e cooldown de reenvio (60s). |
| `verification_attempts` | `PositiveSmallIntegerField(default=0)` | Zera a cada novo código enviado; bloqueia após 5 tentativas erradas. |
| `reset_code` | `CharField(max_length=6, blank=True)` | Código pendente do fluxo "esqueci a senha" — campo separado de `verification_code` de propósito, pra um não pisar no outro se os dois fluxos estiverem pendentes ao mesmo tempo. |
| `reset_sent_at` | `DateTimeField(null=True, blank=True)` | Mesma lógica de expiração (15 min) e cooldown de reenvio (60s) do fluxo de verificação, mas para redefinição de senha. |
| `reset_attempts` | `PositiveSmallIntegerField(default=0)` | Bloqueia após 5 tentativas erradas, igual `verification_attempts`. |

Ver [`auth-flow.md`](auth-flow.md) para o ciclo de vida completo desses
campos.

## `contacts.Contact`

| Campo | Tipo | Notas |
|---|---|---|
| `owner` | `ForeignKey(Profile, related_name="contacts")` | `on_delete=CASCADE` |
| `name` | `CharField(max_length=100)` | |
| `birthday` | `DateField` | Só a data importa — o ano de nascimento é usado apenas para calcular "fará N anos" nos e-mails. |
| `relationship` | `CharField(max_length=30, blank=True)` | Texto livre (ex: "Amiga", "Irmão"), não é um `choices`. |
| `notes` | `TextField(blank=True)` | |
| `created_at` / `updated_at` | `DateTimeField` | `auto_now_add` / `auto_now` |

## `reminders.Reminder`

| Campo | Tipo | Notas |
|---|---|---|
| `contact` | `ForeignKey(Contact, related_name="reminders")` | `on_delete=CASCADE`. Um contato pode ter mais de um lembrete, embora a UI atual só crie um por contato. |
| `days_before` | `PositiveIntegerField` | Quantos dias antes do aniversário o e-mail deve sair. `0` = no próprio dia. |
| `notify_at` | `TimeField(default="09:00")` | Horário local (`America/Sao_Paulo`) a partir do qual o e-mail pode ser disparado. |
| `active` | `BooleanField(default=True)` | Lembretes inativos são ignorados pelo motor de disparo. |
| `last_notified_year` | `PositiveIntegerField(null=True, blank=True)` | Guarda de idempotência: impede reenvio do mesmo lembrete no mesmo ano, mesmo que o endpoint de verificação seja chamado várias vezes por dia. |
| `created_at` / `updated_at` | `DateTimeField` | `auto_now_add` / `auto_now` |

## `dashboard`

Não define nenhum model — é uma camada de views que agrega `Contact` e
`Reminder` numa única tela.

## Migrations

O `.gitignore` do projeto ignora a pasta `migrations/` de cada app — os
arquivos de migration existem no disco de cada ambiente mas **não são
versionados no Git**. Na prática isso significa que `python manage.py
migrate` precisa ser rodado manualmente contra o banco de produção sempre
que um model muda (não há passo automático de migration no deploy da
Vercel).
