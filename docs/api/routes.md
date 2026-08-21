# Rotas

URLconf raiz em `core/urls.py`, que inclui os `urls.py` de cada app.

```python
urlpatterns = [
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('reminders/', include('reminders.urls')),
    path('admin/', admin.site.urls),
]
```

`contacts` não tem `urls.py` próprio — o CRUD de contato acontece sempre
combinado com o de lembrete, através das rotas de `dashboard` (ver
[`api/models.md`](models.md) e [`front/pages.md`](../front/pages.md)).

## `dashboard` (prefixo `/`, `app_name="dashboard"`)

| Método | Path | View | Nome da rota | Auth | Descrição |
|---|---|---|---|---|---|
| GET | `/` | `dashboard.views.index` | `dashboard:index` | `@login_required` | Lista os contatos e lembretes do usuário logado; renderiza também os forms vazios usados no diálogo de criação. |
| POST | `/create-reminder/` | `dashboard.views.create_reminder` | `dashboard:create_reminder` | `@login_required` | Cria **ou** edita um par Contact+Reminder em uma única submissão (upsert combinado — ver detalhes abaixo). |
| POST | `/reminder/<int:reminder_id>/delete/` | `dashboard.views.delete_reminder` | `dashboard:delete_reminder` | `@login_required` | Apaga o lembrete (e, por cascade, não o contato — só o `Reminder`). Escopado ao dono via `contact__owner=profile`. |

### `create_reminder` — upsert combinado

Não existem rotas separadas para "criar contato" e "criar lembrete": o
diálogo do dashboard sempre envia os dois formulários juntos
(`ContactForm` + `ReminderForm`) em um único POST.

- Se `reminder_id` vier no POST, busca o `Reminder` (escopado ao dono) e usa
  a instância existente — vira uma edição do contato + lembrete associados.
- Se não vier, cria um `Contact` novo (`owner = profile atual`) e um
  `Reminder` novo apontando para ele.
- Em caso de erro de validação, a view re-renderiza `dashboard/index.html`
  com `show_dialog=True` para o diálogo reabrir automaticamente já com os
  erros.

## `accounts` (prefixo `/accounts/`, `app_name="accounts"`)

| Método | Path | View | Nome da rota | Auth | Descrição |
|---|---|---|---|---|---|
| GET | `/accounts/` | `accounts.views.index` | `accounts:index` | público | Redireciona para `/` se autenticado. **⚠️ Bug conhecido:** se não autenticado, tenta renderizar `accounts/index.html`, template que não existe no projeto → `TemplateDoesNotExist` (500). Nenhum link do app aponta para essa rota hoje. |
| GET, POST | `/accounts/register/` | `accounts.views.register` | `accounts:register` | público | Cria o `User` (inativo) + `Profile`, dispara o código de verificação por e-mail e redireciona para `verify-email`. Ver [`auth-flow.md`](auth-flow.md). |
| GET, POST | `/accounts/login/` | `accounts.views.login` | `accounts:login` | público | Aceita usuário **ou** e-mail como identificador. Se a conta ainda não foi verificada, reenvia um código novo e redireciona para `verify-email` em vez de logar. |
| GET | `/accounts/logout/` | `accounts.views.logout_view` | `accounts:logout` | `@login_required` | Efetua logout. Acionado por um `<a href>` (GET), não por um POST — aceitável para o tamanho do projeto, mas vale lembrar se algum dia entrar cache/prefetch agressivo de links. |
| GET | `/accounts/profile/` | `accounts.views.profile` | `accounts:profile` | `@login_required` | Tela somente leitura com dados da conta (usuário, e-mail, nome, data de criação). |
| GET, POST | `/accounts/verify-email/` | `accounts.views.verify_email` | `accounts:verify_email` | sessão (`pending_verification_user_id`) | Tela de confirmação do código de 6 dígitos. Também atende o reenvio de código (POST com `action=resend`). |
| GET, POST | `/accounts/password-reset/` | `accounts.views.password_reset_request` | `accounts:password_reset_request` | público | Passo 1 do "esqueci a senha": usuário informa usuário/e-mail. Sempre redireciona para o passo seguinte, exista ou não a conta (evita confirmar/negar existência de e-mail). |
| GET, POST | `/accounts/password-reset/confirm/` | `accounts.views.password_reset_confirm` | `accounts:password_reset_confirm` | sessão (`pending_reset_user_id`) | Passo 2: digitar o código de 6 dígitos. Sem sessão pendente, redireciona direto pro passo 1 (não fica "aberta" mostrando formulário à toa). Também atende reenvio (`action=resend`). |
| GET, POST | `/accounts/password-reset/new-password/` | `accounts.views.password_reset_new_password` | `accounts:password_reset_new_password` | sessão (`reset_code_verified_user_id`) | Passo 3: define a nova senha. Só acessível depois do código confirmado no passo 2 — sem isso, redireciona pro passo 1. |

## `reminders` (prefixo `/reminders/`, `app_name="reminders"`)

| Método | Path | View | Nome da rota | Auth | Descrição |
|---|---|---|---|---|---|
| GET | `/reminders/run-check/?token=...` | `reminders.views.run_due_reminders` | `reminders:run_check` | token via query param (`CRON_SECRET`) | Endpoint público (protegido por token) que roda o motor de verificação de aniversários e dispara os e-mails devidos. Feito para ser chamado por um agendador externo (cron-job.org). Retorna JSON `{"sent": N}` ou `403 {"detail": "Forbidden"}`. Detalhes: [`reminders-engine.md`](reminders-engine.md). |

## Admin

| Path | Descrição |
|---|---|
| `/admin/` | Django Admin padrão. Models registrados: `Profile`, `Contact`, `Reminder` (sem customização de `ModelAdmin` — apenas `admin.site.register(Model)`). |
