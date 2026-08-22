# Páginas

## `/accounts/login/` — `login/index.html`

Layout de duas colunas: painel indigo à esquerda (escondido em telas
pequenas, `max-lg:hidden`), formulário à direita. Campos do `LoginForm`
(`identifier`, `password`) são renderizados manualmente em loop (`{% for
field in form %}`), não com `{{ form }}` — todo o HTML do input é escrito
à mão no template para poder aplicar as classes Tailwind. O campo de
senha tem um botão de mostrar/ocultar (ícone `visibility`/`visibility_off`
alternado via JS) e um link "Esqueceu a senha?" ao lado do label.

O painel esquerdo é um **carrossel de 3 slides** (`moments.svg`,
`organize-photos.svg`, e um slide baseado em ícone — não em imagem):
- Troca automática a cada 2s, pausa no hover, dots clicáveis.
- **Arrasta** com mouse/touch (Pointer Events unificado): acompanha o
  dedo/cursor em tempo real, solta com mais de 40px de arraste pra trocar
  de slide.
- Respeita `prefers-reduced-motion` (desliga a troca automática).
- No mobile (`<lg`) o carrossel inteiro não aparece — só a logo normal,
  pra não empilhar banner + logo + título grande na tela pequena (foi
  tentado um carrossel compacto pro mobile e descartado por ficar
  poluído).

Erros de login (`form.non_field_errors`) aparecem como toast
(`showAppToast(..., 'danger')`), não como caixa estática — ver
[`front/styling.md`](styling.md#toasts). Um `?password_reset=1` na URL
(vindo do passo 3 de redefinição de senha) dispara um toast de sucesso e
depois limpa o parâmetro da URL (`history.replaceState`).

Tem um segundo formulário abaixo, **"Entrar como Demo"**, com
`identifier`/`password` fixos em `<input type="hidden">` (`antonio` /
`123456`) — um atalho de login para uma conta de demonstração pré-existente,
sem tela própria. É estilizado como botão outline (borda verde), de
propósito mais discreto que o botão "Entrar" principal.

JS inline: desabilita o botão + mostra spinner no submit (evita duplo
clique).

## `/accounts/register/` — `register/index.html`

Mesmo layout de duas colunas do login. Campos do `ProfileRegisterForm`
(`first_name`, `username`, `email`, `password`, `confirm_password`),
mesmo padrão de renderização manual campo-a-campo.

Não redireciona para o dashboard depois do cadastro — vai para
`/accounts/verify-email/` (a conta criada começa inativa). Ver
[`api/auth-flow.md`](../api/auth-flow.md).

## `/accounts/verify-email/` — `verify_email/index.html`

Mesmo layout de duas colunas, texto do painel lateral trocado ("Falta
pouco!"). Um único campo de texto centralizado, fonte grande,
`letter-spacing` largo, `maxlength="6"`, `inputmode="numeric"` e
`autocomplete="one-time-code"` (permite autopreenchimento por SMS/gerenciador
de senha em navegadores que suportam). Mostra o e-mail de destino
(`{{ email }}`) para o usuário confirmar que é o endereço certo.

Dois `<form>` separados na mesma página:
1. O de confirmação do código (`POST` normal, campo `code`).
2. O de reenvio (`POST` com `action=resend` num input hidden) — reaproveita
   a mesma view (`accounts.views.verify_email`) só trocando o comportamento
   com base nesse campo.

## Redefinir senha — `password_reset/*`

Três telas, um passo por página (ver [`api/auth-flow.md`](../api/auth-flow.md#4-esqueci-a-senha-accountspassword_reset_)):

1. **`request.html`** (`/accounts/password-reset/`) — um campo,
   "Usuário ou e-mail". Sempre segue pro passo 2, ache ou não a conta.
2. **`confirm.html`** (`/accounts/password-reset/confirm/`) — mesmo
   padrão visual do código de verificação de e-mail (campo grande
   centralizado, `maxlength="6"`, `autocomplete="one-time-code"`) + botão
   de reenviar.
3. **`new_password.html`** (`/accounts/password-reset/new-password/`) —
   dois campos de senha (nova + confirmação), cada um com botão de
   mostrar/ocultar. Diferente do login, aqui **não tem nada além de senha
   na tela**, então os campos ficarem em branco depois de um erro é
   esperado (não tem texto/e-mail pra "perder").

Todos os três usam `autocomplete` semântico por campo (`username`,
`current-password`, `new-password`) em vez de `autocomplete="off"` — ver
a nota sobre isso em [`api/auth-flow.md`](../api/auth-flow.md#onde-isso-pode-falhar-pontos-de-atenção).

## `/accounts/profile/` — `profile/index.html`

Editável: `ProfileEditForm` (Nome + E-mail), além dos dados somente-leitura
(usuário, data de criação). Trocar o e-mail marca `email_verified=False` no
`Profile` e redireciona para `/accounts/verify-email/` — o motor de
lembretes depende de um e-mail confirmado, então a troca só vale depois do
novo código ser validado.

Redesenha a mesma navbar com dropdown do dashboard (ver nota de duplicação
em [`front/templates.md`](templates.md)). O nome exibido no dropdown vem de
`first_name`, não do `username`.

## `/` — `dashboard/index.html`

A tela principal, e a mais complexa do projeto. Estrutura:

1. **Navbar** com logo + dropdown de perfil (Perfil / Sair).
2. **Grid de cards**, um por lembrete (`{% for r in reminders %}`), cada
   card mostra: inicial do contato em avatar circular, nome, data
   (`d/m`), badge Ativo/Inativo, relação e notas (se existirem), horário
   configurado, `X dia(s) antes`, e os botões **Editar**/**Excluir**.
   - **Editar** não é um link — é um `data-edit-reminder` com vários
     `data-*` atributos (nome, aniversário, relação, notas, dias antes,
     horário, ativo). Um listener JS lê esses atributos e **repopula o
     mesmo formulário de criação**, reaproveitando o diálogo único para
     criar e editar (ver `api/routes.md#create_reminder--upsert-combinado`).
   - **Excluir** é um `<form method="post">` de verdade (com `confirm()`
     no `onsubmit`), não um botão JS — funciona mesmo sem JS habilitado.
3. **`<dialog>` nativo do HTML** (`showModal()`/`close()`, não é um modal
   custom) com o formulário combinado de `ContactForm` + `ReminderForm`,
   dividido visualmente em duas seções ("Informações do Contato" /
   "Configurações do Lembrete").

JS inline nessa página (sem framework, DOM API pura):
- Abrir/fechar o `<dialog>`.
- Resetar o form para o modo "criar" (`resetFormToCreate`).
- Reabrir o diálogo automaticamente se a submissão voltou com erro
  (`{% if show_dialog %}` seta um `setTimeout` que chama `openCreate()`).
- Preencher o form a partir dos `data-*` do card ao clicar em Editar.
- Desabilitar botão + spinner no submit.
- Dropdown de perfil (mesmo padrão do profile).

Um `?email_verified=1` na URL (vindo da confirmação de código no
cadastro) dispara um toast de sucesso (`showAppToast(..., 'success')`) e
limpa o parâmetro da URL, mesmo padrão usado no login para
`?password_reset=1`.

## Painel administrativo (`/panel/`)

Três páginas, só para superusuário (ver
[`api/routes.md`](../api/routes.md#panel-prefixo-panel-app_namepanel)),
todas compartilhando `panel/templates/panel/_sidebar.html`:

- **Desktop (`lg+`)**: sidebar fixa à esquerda (`w-64`, `sticky`), com logo,
  os 3 links de navegação (destacado o ativo via `active_tab` no contexto),
  e no rodapé "Voltar ao site" + "Sair".
- **Mobile**: a sidebar vira uma barra superior compacta (logo + link "Site"
  + link "Sair") com abas horizontais roláveis abaixo, mesmo padrão visual
  do resto do app.

### `/panel/` — `overview.html`

Cards com números agregados (usuários, e-mails verificados, contatos,
lembretes, envios do ano, contas inativas). Cada card tem uma borda
colorida à esquerda (`border-l-4`) combinando com o ícone, e levanta
levemente no hover (`hover:-translate-y-0.5`). O card de "Contas inativas"
é um link direto para `/panel/users/`.

### `/panel/users/` — `users.html`

Tabela paginada de todos os `User` (avatar colorido via `avatar_color`,
e-mail, verificado, status, cadastro). Barra de busca (`?q=`) + botão
**Exportar CSV** (preserva o filtro ativo). Por linha:

- Alternar ativo/inativo (`panel:user_toggle_active`) — ícone
  `block`/`check_circle`.
- Excluir (`panel:user_delete`) — some se o alvo for superusuário.
- Ambas as ações somem (trocadas por "você") na própria linha do usuário
  logado, para impedir autossabotagem.

Toasts de status (`user_activated`, `user_deactivated`, `user_deleted`,
`cannot_change_self`) chegam via query string e são lidos/limpos por um
script inline, mesmo padrão de `?email_verified=1` no dashboard.

### `/panel/reminders/` — `reminders.html`

Tabela paginada e somente-leitura de todos os `Reminder` de todos os
usuários (contato, dono, aniversário, horário/dias de aviso, status, último
ano notificado). Mesma busca (`?q=`) e botão **Exportar CSV** dos usuários.
