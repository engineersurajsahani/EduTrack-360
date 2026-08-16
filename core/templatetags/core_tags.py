from django import template

register = template.Library()

@register.filter(name='dict_lookup')
def dict_lookup(dictionary, key):
    """Allows dictionary key lookup in templates."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter(name='split_string')
def split_string(value, delimiter=','):
    """Splits a string by delimiter."""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]
