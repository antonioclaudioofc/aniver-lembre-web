# Estilo visual

## Tailwind via CDN e tokens

```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="{% static 'js/tailwind.config.js' %}"></script>
```

Sem processo de build: o CDN gera o CSS em runtime a partir das classes do
DOM. Os tokens do redesign (cores, fontes, raios, sombras) ficam em
`base_static/js/tailwind.config.js` (`night`, `brand`, `ink`, `muted`,
`soft`, `contact-*`...) e como variáveis CSS em `base_static/css/style.css`
(`--bg`, `--surface`, `--ink`, `--muted`, `--brand`...). As variáveis mudam
sozinhas no modo escuro (classe `dark` no `<html>`), por isso as telas usam
`bg-[var(--surface)]`, `text-[var(--ink)]` etc. em vez de pares `dark:`.

## Cor de marca

`brand` (`#5B5BD6`) é a cor de ação; `night` (`#262163`) destaca o próximo
aniversário e os cabeçalhos de modal, sempre com a textura `.al-dots`. O
logo (`#6875F5`) só aparece no símbolo. Os e-mails continuam em
`indigo-600`.

## Tipografia e ícones

- **Geist** — interface e corpo (`font-sans`).
- **Bricolage Grotesque** — títulos, datas e wordmark (`font-display`).
- **Lucide** — ícones, via `<i data-lucide="nome" class="w-5 h-5"></i>`;
  `lucide.createIcons()` roda em `base_static/js/app.js`.

## Componentes compartilhados

Includes em `base_templates/components/`: `_date_stamp.html` (carimbo de
data), `_avatar.html` (tom por `id % 8`), `_empty_state.html` e
`_pagination.html`. A barra do topo e a barra móvel ficam em
`base_templates/partials/_topbar.html`.

## Tema escuro (dark mode)

Manual, não só "segue o sistema" — o usuário troca pelo botão flutuante
(`#themeToggle`, sol/lua, canto inferior direito) definido uma única vez
em `base_templates/global/base.html`, fora do `{% block content %}`, por
isso aparece em **toda** página sem precisar repetir nada.

Como funciona:

1. Tailwind CDN é configurado com `tailwind.config = { darkMode: 'class'
   }` em `_head.html` — sem isso, o CDN só reagiria a
   `prefers-color-scheme` do sistema, e não teria como o botão "vencer" a
   preferência do usuário manualmente.
2. Um `<script>` no topo do `<head>` (antes de qualquer outra coisa
   carregar) lê `localStorage.getItem('theme')`; se não tiver nada salvo
   ainda, usa `prefers-color-scheme: dark` do sistema como padrão. Se for
   escuro, adiciona a classe `dark` no `<html>` **antes da primeira
   pintura** — é isso que evita o "flash" de claro→escuro ao carregar a
   página.
3. Clicar no botão faz `document.documentElement.classList.toggle('dark')`
   e salva a escolha em `localStorage.setItem('theme', ...)` — a partir
   daí a escolha do usuário sempre vence a preferência do sistema.
4. Todo o resto é só a variante `dark:` do Tailwind espalhada nas classes
   de cada elemento (`bg-white dark:bg-gray-900`, etc.) — não tem CSS
   customizado envolvido, exceto os elementos que já eram CSS puro antes
   (`.ambient-panel`, `@keyframes`), que não precisam de tratamento de
   tema porque são decorativos e funcionam igual nos dois.

Onde tem `dark:` aplicado: layout raiz, todas as telas de auth
(login/registro/verificação/redefinição de senha), dashboard inteiro
(navbar, cards, diálogo) e perfil. Os campos do diálogo de
criar/editar lembrete vêm de **widgets Python** (`contacts/forms.py`,
`reminders/forms.py`), não do template — o `dark:` desses campos está
nas classes `attrs={'class': '...'}` desses arquivos, não em HTML.

**E-mails não usam esse mecanismo** — não rodam JavaScript, então não têm
o botão de trocar tema. Eles seguem `prefers-color-scheme` do cliente de
e-mail automaticamente (ver seção de e-mails abaixo). É a única forma
possível de dark mode em e-mail.

## Toasts

Um helper único e global, `showAppToast(message, type)`, definido em
`_head.html` logo depois do `<script>` do Toastify (pra já existir antes
de qualquer script de página rodar). `type` é `'success' | 'danger' |
'warning' | 'info'` (padrão `'info'`) e define a cor:

| `type` | Cor |
|---|---|
| `success` | `emerald-600` |
| `danger` | `red-600` |
| `warning` | `amber-500` |
| `info` | `indigo-600` (cor de marca) |

Nunca chamar `Toastify({...})` direto numa página — sempre
`showAppToast(...)`. O helper resolve três coisas que já causaram bug
antes:

1. **Cor não aparecia**: o Toastify aplica seu próprio gradiente via
   `background-image` inline em JS por padrão; uma classe Tailwind
   `bg-emerald-600` (só `background-color`) não é suficiente pra
   sobrescrever isso, mesmo com `!important` — o gradiente fica por cima.
   O helper sempre inclui `!bg-none` pra derrubar essa imagem de fundo
   antes de aplicar a cor.
2. **Duração**: fixa em 3.5s (curto, de propósito — antes um toast ficava
   5-6s na tela).
3. **Acúmulo**: guarda a instância atual em `window.__appToast` e chama
   `.hideToast()` nela antes de mostrar a próxima — nunca mais de um
   toast na tela ao mesmo tempo.

Exemplo de uso (visto em `login/index.html` e `dashboard/index.html`):
```js
showAppToast('Senha redefinida com sucesso!', 'success');
```

## Logo

Ver [`front/templates.md`](templates.md#duas-logos-dois-propósitos) para a
diferença entre `logo.svg` (usada no site) e `logo-email.png` (gerada
especificamente para os e-mails, por limitação de suporte a SVG dos
clientes de e-mail).

## E-mails: por que o CSS é diferente do site

Os templates em `*/templates/emails/*.html` **não** usam Tailwind nem
qualquer CSS externo — clientes de e-mail (Gmail, Outlook, Apple Mail)
não carregam `<script>` nem, em muitos casos, `<link rel="stylesheet">`
externo de forma confiável. Por isso esses templates usam:

- Layout com `<table role="presentation">` (compatibilidade com o motor de
  renderização do Outlook, que ignora `display: flex`/`grid`);
- Estilos **inline** (`style="..."`) em cada elemento, não classes;
- Um único `<style>` no `<head>` só para media queries (`max-width` para
  mobile, `prefers-color-scheme: dark`), que a maioria dos clientes
  modernos respeita mesmo sem suportar CSS externo;
- Imagem da logo em PNG absoluto (`{{ site_url }}/static/...`), nunca SVG
  nem caminho relativo (e-mail não tem uma "página atual" para resolver
  URL relativa contra).

## `style.css`

Contém os tokens como variáveis CSS, o carimbo de data (`.al-stamp`), o
calendário (`.al-day`), o seletor segmentado (`.al-segment`), o interruptor
(`.al-switch`), o toast (`.al-toast`) e as animações. O restante vem de
classes do Tailwind no HTML.
