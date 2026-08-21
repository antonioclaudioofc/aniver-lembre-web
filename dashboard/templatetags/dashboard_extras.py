from django import template

register = template.Library()

# Emerald/red/amber ficam de fora de propósito: já carregam significado
# semântico (sucesso/perigo/aviso) em outras partes do app — usar aqui
# criaria sinal visual confuso.
AVATAR_PALETTE = [
    'indigo', 'sky', 'violet', 'rose',
    'teal', 'fuchsia', 'cyan', 'orange',
]


@register.filter
def avatar_color(value):
    """Cor determinística (nome de cor do Tailwind) a partir de um id/nome,
    pra dar identidade visual distinta a cada card sem sortear a cada
    request."""
    try:
        key = int(value)
    except (TypeError, ValueError):
        key = sum(ord(c) for c in str(value))
    return AVATAR_PALETTE[key % len(AVATAR_PALETTE)]
