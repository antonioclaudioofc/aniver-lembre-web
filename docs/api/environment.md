# Variáveis de ambiente e deploy

Carregadas via `python-dotenv` (`load_dotenv(BASE_DIR / '.env')` em
`core/settings.py`) localmente, e via variáveis de ambiente do provedor em
produção. Template completo em [`.env.example`](../../.env.example) na raiz
do projeto — **nunca** commitar o `.env` real (já está no `.gitignore`).

| Variável | Default se ausente | Descrição |
|---|---|---|
| `DATABASE_URL` | — (obrigatória) | String de conexão Postgres (Neon), lida por `dj_database_url.config()`. |
| `SECRET_KEY` | chave insegura fixa no código | **Deve** ser definida em produção. |
| `DEBUG` | `False` | Só `True` em desenvolvimento local. |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Backend "console" só imprime o e-mail no log — nada é entregue. Trocar para `django.core.mail.backends.smtp.EmailBackend` para envio real. |
| `EMAIL_HOST` | `smtp.gmail.com` | |
| `EMAIL_PORT` | `587` | |
| `EMAIL_USE_TLS` | `True` | |
| `EMAIL_HOST_USER` | vazio | Endereço Gmail completo. |
| `EMAIL_HOST_PASSWORD` | vazio | **Senha de app** do Gmail (16 caracteres), não a senha normal da conta — precisa de verificação em duas etapas ativada. |
| `DEFAULT_FROM_EMAIL` | igual a `EMAIL_HOST_USER` | Remetente dos e-mails (lembretes e verificação de cadastro). |
| `CRON_SECRET` | vazio (endpoint fica bloqueado) | Token exigido por `/reminders/run-check/?token=...`. |
| `SITE_URL` | `http://127.0.0.1:8000` | Base para montar links/imagens absolutas dentro dos e-mails (não há `request` disponível quando o endpoint de cron dispara). |

## Deploy (Vercel)

O projeto está conectado à Vercel **sem `vercel.json`** e sem build command
customizado — depende inteiramente da detecção automática de projetos
Django (via `manage.py` + `WSGI_APPLICATION` em `core/settings.py`).

Ponto que já causou bug em produção: a Vercel só roda `collectstatic` e
serve os arquivos estáticos pelo CDN automaticamente quando `STATIC_ROOT`
está definido em `settings.py`. Antes disso, imagens/CSS ficavam quebrados
em produção mesmo com o app rodando normalmente. Hoje:

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

- `staticfiles/` é gerado no build (ignorado no Git).
- WhiteNoise só é realmente ativo em desenvolvimento local (`vercel dev`
  e `runserver`) — em produção quem serve os arquivos é o CDN da Vercel.

### Migrations em produção

Como a pasta `migrations/` de cada app é ignorada pelo Git (ver
[`models.md`](models.md#migrations)), o deploy da Vercel **não** aplica
migrations automaticamente. É preciso rodar manualmente:

```bash
python manage.py migrate     # com DATABASE_URL apontando pro banco de produção
```

### Histórico de hospedagem

O repositório já teve um `Dockerfile` e um workflow de GitHub Actions
("Ping Render App") de uma tentativa anterior de deploy no Render — ambos
foram removidos no commit que migrou a configuração para Vercel + Neon.
`ALLOWED_HOSTS` ainda lista `.onrender.com` por segurança/retrocompatibilidade,
mesmo sem deploy ativo lá.
