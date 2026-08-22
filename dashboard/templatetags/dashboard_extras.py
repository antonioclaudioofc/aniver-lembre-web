from django import template

register = template.Library()

AVATAR_PALETTE = [
    'indigo', 'sky', 'violet', 'rose',
    'teal', 'fuchsia', 'cyan', 'orange',
]


@register.filter
def avatar_color(value):
    try:
        key = int(value)
    except (TypeError, ValueError):
        key = sum(ord(c) for c in str(value))
    return AVATAR_PALETTE[key % len(AVATAR_PALETTE)]
