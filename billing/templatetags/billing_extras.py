from django import template

register = template.Library()

@register.filter
def getitem(obj, key):
    """Template helper: {{ mydict|getitem:'0-30' }}"""
    try:
        return obj.get(key)
    except Exception:
        try:
            return obj[key]
        except Exception:
            return None
