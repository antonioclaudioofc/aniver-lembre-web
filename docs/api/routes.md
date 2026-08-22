# Rotas

URLconf raiz em `core/urls.py`, que inclui os `urls.py` de cada app.

```python
urlpatterns = [
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('reminders/', include('reminders.urls')),
    path('panel/', include('panel.urls')),
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
| GET | `/accounts/` | `accounts.views.index` | `accounts:index` | público | Redireciona quem já está autenticado para o painel (`panel:overview`, se superusuário) ou para `/` (senão). **⚠️ Bug conhecido:** se não autenticado, tenta renderizar `accounts/index.html`, template que não existe no projeto → `TemplateDoesNotExist` (500). Nenhum link do app aponta para essa rota hoje. |
| GET, POST | `/accounts/register/` | `accounts.views.register` | `accounts:register` | público | Cria o `User` (inativo) + `Profile`, dispara o código de verificação por e-mail e redireciona para `verify-email`. Ver [`auth-flow.md`](auth-flow.md). |
| GET, POST | `/accounts/login/` | `accounts.views.login` | `accounts:login` | público | Aceita usuário **ou** e-mail como identificador. Se a conta ainda não foi verificada, reenvia um código novo e redireciona para `verify-email` em vez de logar. Login bem-sucedido leva para `panel:overview` se o usuário for superusuário, senão para `/`. |
| GET | `/accounts/logout/` | `accounts.views.logout_view` | `accounts:logout` | `@login_required` | Efetua logout. Acionado por um `<a href>` (GET), não por um POST — aceitável para o tamanho do projeto, mas vale lembrar se algum dia entrar cache/prefetch agressivo de links. Linkado também no painel administrativo. |
| GET, POST | `/accounts/profile/` | `accounts.views.profile` | `accounts:profile` | `@login_required` | Edição de Nome e E-mail. Trocar o e-mail marca `email_verified=False` e reaproveita o fluxo de verificação por código (`verify-email`) antes de confirmar a troca. |
| GET, POST | `/accounts/verify-email/` | `accounts.views.verify_email` | `accounts:verify_email` | sessão (`pending_verification_user_id`) | Tela de confirmação do código de 6 dígitos. Também atende o reenvio de código (POST com `action=resend`). |
| GET, POST | `/accounts/password-reset/` | `accounts.views.password_reset_request` | `accounts:password_reset_request` | público | Passo 1 do "esqueci a senha": usuário informa usuário/e-mail. Sempre redireciona para o passo seguinte, exista ou não a conta (evita confirmar/negar existência de e-mail). |
| GET, POST | `/accounts/password-reset/confirm/` | `accounts.views.password_reset_confirm` | `accounts:password_reset_confirm` | sessão (`pending_reset_user_id`) | Passo 2: digitar o código de 6 dígitos. Sem sessão pendente, redireciona direto pro passo 1 (não fica "aberta" mostrando formulário à toa). Também atende reenvio (`action=resend`). |
| GET, POST | `/accounts/password-reset/new-password/` | `accounts.views.password_reset_new_password` | `accounts:password_reset_new_password` | sessão (`reset_code_verified_user_id`) | Passo 3: define a nova senha. Só acessível depois do código confirmado no passo 2 — sem isso, redireciona pro passo 1. |

## `reminders` (prefixo `/reminders/`, `app_name="reminders"`)

| Método | Path | View | Nome da rota | Auth | Descrição |
|---|---|---|---|---|---|
| GET | `/reminders/run-check/?token=...` | `reminders.views.run_due_reminders` | `reminders:run_check` | token via query param (`CRON_SECRET`) | Endpoint público (protegido por token) que roda o motor de verificação de aniversários e dispara os e-mails devidos. Feito para ser chamado por um agendador externo (cron-job.org). Retorna JSON `{"sent": N}` ou `403 {"detail": "Forbidden"}`. Detalhes: [`reminders-engine.md`](reminders-engine.md). |

## `panel` (prefixo `/panel/`, `app_name="panel"`)

Painel administrativo próprio (não é o Django Admin). Toda view passa por
`@superuser_required` (`panel/decorators.py`): combina `@login_required`
com uma checagem de `request.user.is_superuser` que levanta
`PermissionDenied` (→ 403) em vez de redirecionar — evita mandar quem já
está logado (mas sem permissão) de volta pra tela de login.

| Método | Path | View | Nome da rota | Descrição |
|---|---|---|---|---|
| GET | `/panel/` | `panel.views.overview` | `panel:overview` | Cards com números agregados da aplicação inteira: usuários (total, novos na semana, ativos/inativos), e-mails verificados/pendentes, contatos, lembretes (total/ativos), e-mails de aniversário disparados no ano corrente. |
| GET | `/panel/users/` | `panel.views.users_list` | `panel:users` | Lista todos os `User` (paginada, busca por usuário/e-mail/nome). Cada linha tem os botões de ativar/desativar e excluir. |
| GET | `/panel/users/export/` | `panel.views.export_users` | `panel:users_export` | Exporta o mesmo conjunto filtrado (respeita `?q=`) como CSV (`usuarios.csv`): usuário, nome, e-mail, e-mail verificado, status, admin, cadastro. |
| POST | `/panel/users/<int:user_id>/toggle-active/` | `panel.views.toggle_user_active` | `panel:user_toggle_active` | Alterna `is_active` do usuário alvo. Recusa (com toast de aviso) se o alvo for o próprio superusuário logado. |
| POST | `/panel/users/<int:user_id>/delete/` | `panel.views.delete_user` | `panel:user_delete` | Apaga o `User` (cascade: `Profile`, `Contact`s e `Reminder`s dele). Recusa se o alvo for o próprio usuário logado ou outro superusuário. |
| GET | `/panel/reminders/` | `panel.views.reminders_list` | `panel:reminders` | Lista somente-leitura de todos os `Reminder` de todos os usuários (paginada, busca por contato/dono). |
| GET | `/panel/reminders/export/` | `panel.views.export_reminders` | `panel:reminders_export` | Exporta o mesmo conjunto filtrado como CSV (`lembretes.csv`): contato, dono (usuário/e-mail), aniversário, horário/dias de notificação, ativo, último ano notificado. |

Layout: sidebar fixa à esquerda em telas `lg+` (`panel/templates/panel/_sidebar.html`),
com links para as 3 páginas, "Voltar ao site" e "Sair" (`accounts:logout`).
Em telas menores a sidebar vira uma barra superior com abas horizontais e os
mesmos dois links compactados no cabeçalho. Um superusuário autenticado que
acessa `/`, `/accounts/` ou faz login é redirecionado direto para
`panel:overview` em vez do dashboard comum (ver tabela de `accounts` acima).

## Admin

| Path | Descrição |
|---|---|
| `/admin/` | Django Admin padrão. Models registrados: `Profile`, `Contact`, `Reminder` (sem customização de `ModelAdmin` — apenas `admin.site.register(Model)`). |

## Páginas de erro (404 / 500)

`base_templates/404.html` e `base_templates/500.html` — descobertos
automaticamente pelo Django por convenção de nome (`base_templates` está
em `TEMPLATES[0]['DIRS']`, então resolvem como `404.html`/`500.html`
puros). Nenhuma configuração extra em `urls.py` é necessária.

**Só entram em ação com `DEBUG=False`.** Com `DEBUG=True` (padrão em
desenvolvimento local), o Django sempre mostra a página técnica de debug
(com traceback/lista de URLs), ignorando esses templates — não tem como
ver o 404/500 "de verdade" localmente sem setar `DEBUG=False` (e
`ALLOWED_HOSTS` compatível) temporariamente. Em produção (Vercel, com
`DEBUG` não definido → `False` por padrão, ver
[`environment.md`](environment.md)) eles valem normalmente.

O 404 mostra um botão que muda conforme o login: "Voltar para o início"
(`dashboard:index`) se autenticado, "Voltar para o login" se não —
possível porque a view padrão do Django (`page_not_found`) passa
`request` pro template, então os context processors (incluindo `user`)
rodam normalmente. O 500 **não** tem esse luxo: a view padrão
(`server_error`) renderiza sem `request`, então esse template evita
qualquer coisa que dependa de context processor (`{{ user }}` não
funcionaria lá) e só linka pra `/` direto.
