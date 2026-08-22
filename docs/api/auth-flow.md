# Autenticação e verificação de e-mail

Implementado em `accounts/forms.py`, `accounts/views.py` e
`accounts/services.py`. Não usa `django.contrib.messages` — os avisos
(erro de código, aviso de reenvio) são passados direto pelo contexto do
template, seguindo o padrão do resto do projeto.

## Por que existe verificação de e-mail

O app manda lembretes de aniversário por e-mail (ver
[`reminders-engine.md`](reminders-engine.md)). Sem confirmar que o e-mail
cadastrado é real, o usuário nunca recebe nada — daí a conta ficar
**inativa** (`User.is_active = False`) até o código ser confirmado.

## 1. Cadastro (`accounts:register`)

1. `ProfileRegisterForm` valida `first_name`, `username`, `email` (agora
   **obrigatório**, diferente do `User` padrão do Django onde `email` é
   opcional) e a senha (com confirmação).
2. `form.save()` cria o `User` com `is_active=False` e o `Profile`
   associado (`email_verified=False` por padrão do model).
3. A view chama `send_verification_code(user.profile)`, que:
   - gera um código numérico de 6 dígitos (`secrets.randbelow`, não
     `random` — criptograficamente seguro);
   - grava `verification_code` e `verification_sent_at` no `Profile`,
     zera `verification_attempts`;
   - renderiza e envia `accounts/templates/emails/verification_code.html`
     (+ fallback `.txt`) por e-mail.
4. A view guarda `request.session['pending_verification_user_id'] = user.id`
   e redireciona para `accounts:verify_email`.

## 2. Confirmação do código (`accounts:verify_email`)

A view não usa `@login_required` — o usuário ainda não está logado (a
conta está inativa). A identificação de "quem está confirmando" vem
inteiramente da sessão (`pending_verification_user_id`).

- **POST com `action=resend`**: reenvia um código novo, respeitando um
  cooldown de 60s (`can_resend_code`) para evitar spam de e-mail.
- **POST com o código**: `verify_code(profile, code)` checa, nessa ordem:
  1. já verificado? retorna sucesso direto;
  2. existe código pendente?
  3. não excedeu `MAX_ATTEMPTS = 5` tentativas erradas?
  4. não expirou (`CODE_TTL_MINUTES = 15`)?
  5. o código bate?

  Se tudo passar: `email_verified=True`, `user.is_active=True`, código
  limpo, e a view loga o usuário (`auth_login`) e redireciona para `/`.
  Qualquer falha nas checagens acima incrementa `verification_attempts`
  (exceto nos casos "sem código pendente"/"expirado", que pedem reenvio)
  e devolve uma mensagem específica (`service_error` no contexto).

## 3. Login (`accounts:login`)

`LoginForm` aceita um único campo `identifier` (usuário **ou** e-mail):

```python
user = User.objects.filter(
    Q(username__iexact=identifier) | Q(email__iexact=identifier)
).first()
```

Note que isso **não** usa `django.contrib.auth.authenticate()` — de
propósito. `authenticate()` com o backend padrão já rejeita usuários
`is_active=False` sem distinguir "senha errada" de "conta não verificada".
Aqui a senha é checada manualmente (`user.check_password(password)`), e a
view decide o que fazer com o resultado:

- Credenciais inválidas → erro genérico "Usuário ou senha inválidos."
  (não revela se o e-mail existe).
- Credenciais válidas mas `is_active=False` → reenvia um código novo e
  redireciona para `verify-email`, **sem** mostrar erro — o usuário só
  precisa terminar a verificação que não concluiu.
- Credenciais válidas e conta ativa → login normal, e o destino depende de
  `user.is_superuser`: superusuário vai direto para `panel:overview`
  (ver [`routes.md`](routes.md#panel-prefixo-panel-app_namepanel)), qualquer
  outro usuário vai para `/` (dashboard). O mesmo destino é usado para quem
  já está autenticado e revisita `/accounts/login/` ou `/accounts/`.

## 4. Esqueci a senha (`accounts:password_reset_*`)

Três passos, cada um sua própria página — de propósito, depois de uma
primeira versão em página única ter sido considerada confusa (código e
senha nova no mesmo formulário misturavam duas decisões diferentes).

1. **`password_reset_request`** — usuário informa usuário ou e-mail
   (`PasswordResetRequestForm`). A view busca o `User` por
   `username__iexact` ou `email__iexact`; se achar (e tiver e-mail
   cadastrado), chama `send_password_reset_code(profile)` e guarda
   `request.session['pending_reset_user_id']`. **Redireciona para o passo
   2 independentemente de ter encontrado o usuário ou não** — não dá pra
   descobrir por essa tela se um e-mail está cadastrado.
2. **`password_reset_confirm`** — reaproveita `VerifyEmailForm` (o mesmo
   form do fluxo de verificação de cadastro, só o campo `code`). Sem
   `pending_reset_user_id` na sessão, redireciona direto pro passo 1 (não
   existe uma versão "vazia" dessa tela). `verify_reset_code(profile,
   code)` faz as mesmas checagens de `verify_code` (tentativas, expiração,
   código certo), mas em cima dos campos `reset_*`. Se o código bate, a
   view grava `request.session['reset_code_verified_user_id'] =
   profile.user.id` — é essa segunda chave de sessão que libera o passo 3.
3. **`password_reset_new_password`** — só renderiza se
   `pending_reset_user_id == reset_code_verified_user_id` na sessão (ambas
   têm que bater com o mesmo usuário); qualquer coisa fora disso
   redireciona pro passo 1. `SetNewPasswordForm`:
   - roda `validate_password(senha, user=self.user)` — o `user` é passado
     de propósito, pra ativar direito o `UserAttributeSimilarityValidator`
     já configurado em `AUTH_PASSWORD_VALIDATORS` (sem isso, o validador
     não tem como comparar a senha com o username/e-mail do usuário);
   - bloqueia se a nova senha for **igual a senha atual**
     (`user.check_password(password)`);
   - confere se as duas senhas digitadas batem.

   Dando tudo certo: `set_password`, `clear_reset_code(profile)` (zera os
   3 campos `reset_*`), limpa as duas chaves de sessão, e redireciona pro
   login com `?password_reset=1` — que dispara um toast de sucesso lá
   (ver [`front/styling.md`](../front/styling.md#toasts)).

Os campos de senha nesses formulários **não** preservam o valor digitado
se a validação falhar (sem `value="..."` no HTML) — é proposital: os dois
campos da tela 3 são senha, então "limpar tudo" ali é o comportamento
padrão e mais seguro (evita eco de senha no HTML da página). Login e
cadastro seguem a mesma convenção: só os campos de senha limpam, os
campos de texto (usuário/e-mail/nome) continuam preenchidos porque o
Django reconstrói o form a partir do POST enviado.

## Onde isso pode falhar (pontos de atenção)

- Não há rota para o usuário **trocar** o e-mail cadastrado antes de
  verificar — se ele digitar um e-mail errado no cadastro, fica preso
  (só resta registrar de novo com um `username` diferente, já que
  `username`/`email` são únicos).
- `verification_attempts` é resetado a cada reenvio, então o limite de 5
  tentativas é por-código, não vitalício — um usuário pode pedir reenvio
  repetidamente para tentar mais códigos (mitigado pelo cooldown de 60s,
  mas não elimina o vetor).
- Contas antigas (criadas antes dessa feature) já estão com
  `is_active=True` e `email_verified=False` — nunca serão obrigadas a
  verificar, pois só o fluxo de cadastro/login-com-conta-inativa aciona a
  checagem.
- Todo `<input>` nesses formulários usa `autocomplete` semântico
  (`username`, `current-password`, `new-password`, etc.), nunca
  `autocomplete="off"` — de propósito. Chrome/Firefox ignoram
  `autocomplete="off"` em formulários com campo de senha (por causa de
  gerenciador de senha) e, na prática, isso já causou o formulário inteiro
  parecer "limpar" depois de um erro. Se algum formulário novo for
  adicionado aqui, replicar o `autocomplete` correto por campo.
