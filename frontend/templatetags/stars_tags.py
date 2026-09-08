from django import template

register = template.Library()

@register.simple_tag
def render_stars(rating, max_stars=5):
    try:
        value = float(rating or 0)
    except (TypeError, ValueError):
        value = 0
    full = int(round(value))
    full = max(0, min(full, max_stars))
    stars = ""
    for i in range(1, max_stars + 1):
        if i <= full:
            stars += '<span class="text-yellow-400">★</span>'
        else:
            stars += '<span class="text-white/20">★</span>'
    return stars

@register.filter
def star_list(rating, max_stars=5):
    try:
        value = int(round(float(rating or 0)))
    except (TypeError, ValueError):
        value = 0
    value = max(0, min(value, max_stars))
    return [i <= value for i in range(1, max_stars + 1)]