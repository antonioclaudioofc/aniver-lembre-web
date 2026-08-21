# Templates e assets estáticos

Sem build step de front-end (sem Node, sem bundler). Tailwind é carregado
via CDN (`<script src="https://cdn.tailwindcss.com">`) direto no HTML —
classes utilitárias são resolvidas no navegador, em runtime.

## Estrutura

```
base_templates/
  global/base.html          ← layout raiz, botão de tema, único {% block content %}
  partials/_head.html       ← <head> compartilhado (fonts, Tailwind, favicon, Toastify, showAppToast, config do tema)

base_static/
  css/style.css              ← .inter (font-family) + @keyframes/glow que o Tailwind CDN não expressa em classe
  images/
    logo.svg                 ← logo oficial (ícone calendário+pontos), usada na UI
    logo-email.png           ← versão PNG gerada a partir da logo, só para e-mail
    favicon.png               ← fallback do favicon para navegadores sem suporte a SVG
    moments.svg               ← ilustração do painel lateral (login/registro/verificação/reset)
    organize-photos.svg       ← ilustração do 2º slide do carrossel de login

accounts/templates/
  login/index.html            ← carrossel (3 slides, arrasta com o dedo/mouse) + toggle de tema
  register/index.html
  verify_email/index.html
  password_reset/
    request.html               ← passo 1: usuário/e-mail
    confirm.html                ← passo 2: código de 6 dígitos
    new_password.html            ← passo 3: nova senha
  profile/index.html
  emails/
    verification_code.html + .txt
    password_reset_code.html + .txt

dashboard/templates/
  dashboard/index.html       ← única tela da área logada

reminders/templates/
  emails/birthday_reminder.html + .txt
```

Cada app Django resolve seus próprios templates via `APP_DIRS=True`
(`core/settings.py`) — não existe um diretório central de templates além
de `base_templates/` (usado só para o layout raiz e o `<head>`).

## `global/base.html`

```django
{% include "partials/_head.html" %}
...
<body class="inter bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  {% block content %}{% endblock %}
  <button id="themeToggle">...</button>   {# sol/lua, fixed bottom-right #}
</body>
```

Toda página estende esse template e sobrescreve `{% block content %}`.
Não há navbar/footer globais aqui — cada página que precisa de navegação
(dashboard, profile) desenha a própria `<nav>` no início do `content`
(duplicado entre as duas, não compartilhado — ver Débitos técnicos abaixo).

O botão de tema (`#themeToggle`) fica **fora** do `{% block content %}`,
direto no `base.html` — é assim que ele aparece em toda página sem
precisar repetir HTML/JS em cada template filho. Detalhes de como o tema
funciona: [`front/styling.md`](styling.md#tema-escuro-dark-mode).

## `partials/_head.html`

Carrega, nessa ordem: script anti-flash de tema (aplica `dark` no
`<html>` antes da primeira pintura, lendo `localStorage`/preferência do
sistema), favicon, Tailwind CDN + `tailwind.config = { darkMode: 'class'
}` (sem isso o CDN só seguiria a preferência do sistema, não daria pra
ter um botão manual), fonte de ícones Material Symbols, preconnect para
Google Fonts, fonte Inter, `style.css` próprio, CSS+JS do Toastify e o
helper global `showAppToast(message, type)` (ver
[`front/styling.md`](styling.md#toasts)).

## Duas logos, dois propósitos

| Arquivo | Onde é usado | Por quê |
|---|---|---|
| `images/logo.svg` | Toda a UI do site (telas de login/registro/dashboard) e o `<link rel="icon">` | Navegadores modernos suportam SVG em `<img>` e em favicon; escala perfeitamente. |
| `images/logo-email.png` | Só dentro dos e-mails (lembrete de aniversário e código de verificação) | Clientes de e-mail (Gmail, Outlook) têm suporte muito ruim a SVG em `<img>` — a imagem simplesmente não carrega em boa parte deles. O PNG foi gerado programaticamente reproduzindo o ícone da logo (calendário com pontinhos) sobre um círculo na cor de marca `#4f46e5`, para que o e-mail continue reconhecível como AniverLembre. |

## Débitos técnicos conhecidos (para quem for mexer aqui)

- A navbar com dropdown de perfil está **duplicada** em
  `dashboard/index.html` e `accounts/templates/profile/index.html`
  (HTML e o JS do dropdown, idênticos nos dois arquivos). Um candidato
  natural para virar um `{% include %}` compartilhado.
- `global/base.html` não define `<title>` por bloco — o `<title>` fixo
  ("Aniver Lembre") vive em `_head.html` e é igual em todas as páginas.
- `.prettierignore` (raiz do projeto) ignora todo `*.html` — Prettier não
  entende `{% %}`/`{{ }}` do Django e já corrompeu uma tag colocada como
  atributo solto (`{% if %}id="x"{% endif %}`) tentando "formatar" o HTML.
  Formatar template Django com Prettier é seguro **só** quando a tag fica
  inteira dentro de um valor de atributo entre aspas (`class="{% if %}...{%
  endif %}"`), nunca solta como o atributo em si.
