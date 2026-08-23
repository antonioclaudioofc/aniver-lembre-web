# AniverLembre — Documentação Técnica

Aplicação de lembrete de aniversário construída em **Django 6.0** (monolito
server-rendered — não há separação real de front-end/back-end como em uma
SPA + API REST). A divisão de pastas abaixo é conceitual, não arquitetural:

- **[`api/`](api/)** — a camada de servidor: rotas, models, regras de negócio,
  autenticação, o motor de envio de lembretes por e-mail e variáveis de
  ambiente. "API" aqui significa "o que roda no servidor", não um conjunto de
  endpoints JSON — o único endpoint que devolve JSON é
  `/reminders/run-check/` (ver [`api/reminders-engine.md`](api/reminders-engine.md)).
- **[`front/`](front/)** — templates Django, estrutura de páginas, assets
  estáticos e o pouco de JavaScript (vanilla, inline) usado para diálogos e
  interações.

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | Django 6.0 |
| Banco de dados | PostgreSQL (Neon) via `dj-database-url`, com fallback local em SQLite |
| Servidor WSGI | Gunicorn (local/Render) / runtime Python da Vercel (produção atual) |
| Arquivos estáticos | WhiteNoise (`CompressedManifestStaticFilesStorage`) + collectstatic automático da Vercel |
| CSS | Tailwind CSS via CDN (sem build step) |
| Ícones/fontes | Material Symbols e Inter, via Google Fonts |
| E-mail | `django.core.mail` (backend console em dev, SMTP/Gmail em produção) |
| Agendamento | Serviço externo (cron-job.org) chamando um endpoint HTTP protegido por token |
| Tema | Claro/escuro manual (Tailwind `darkMode: 'class'`), botão flutuante global, preferência salva em `localStorage` |
| Notificações in-app | Toastify, com um helper único `showAppToast(message, type)` (cores semânticas: sucesso/perigo/aviso/info) |

## Apps Django

| App | Responsabilidade |
|---|---|
| `core` | settings, URLconf raiz, wsgi/asgi |
| `accounts` | cadastro, login (usuário ou e-mail), verificação de e-mail por código, redefinição de senha em 3 passos, perfil |
| `contacts` | model `Contact` (pessoa + data de aniversário) |
| `reminders` | model `Reminder`, motor de disparo de e-mail, endpoint de cron |
| `dashboard` | tela principal (CRUD combinado de contato + lembrete) |
| `panel` | painel administrativo (visão geral, usuários, lembretes), restrito a superusuário |

## Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
cp .env.example .env           # preencha com valores reais
python manage.py migrate
python manage.py runserver
```

Variáveis de ambiente completas: [`api/environment.md`](api/environment.md).

## Documentos

- [`api/routes.md`](api/routes.md) — tabela de todas as rotas
- [`api/models.md`](api/models.md) — models e campos
- [`api/auth-flow.md`](api/auth-flow.md) — cadastro, verificação de e-mail, login e redefinição de senha
- [`api/reminders-engine.md`](api/reminders-engine.md) — como o disparo de lembretes funciona
- [`api/environment.md`](api/environment.md) — variáveis de ambiente e deploy
- [`front/templates.md`](front/templates.md) — estrutura de templates e assets
- [`front/pages.md`](front/pages.md) — página por página
- [`front/styling.md`](front/styling.md) — Tailwind, tema escuro, toasts, e-mails, cores de marca

## Painel administrativo

App `panel`, montado em `/panel/`. Todas as rotas (view por view, inclusive
as duas de exportação CSV) passam por `@superuser_required`
(`panel/decorators.py`): não-logado vai para o login, logado sem
`is_superuser` recebe `403` — nenhuma delas faz redirect silencioso para
alguém sem permissão. Ver [`api/routes.md`](api/routes.md#panel-prefixo-panel-app_namepanel)
e [`front/pages.md`](front/pages.md#painel-administrativo-panel).
