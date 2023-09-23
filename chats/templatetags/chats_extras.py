from django import template

register = template.Library()


@register.filter
def simplified_ru_pluralize(value, variants):
    variants = variants.split(',')
    value = abs(int(value))
    if value == 1:
        return variants[0]
    elif value in [2, 3, 4]:
        return variants[1]
    else:
        return variants[2]

