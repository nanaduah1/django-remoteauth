from django import template
from remote_auth.require import require_role
register = template.Library()

def user_in_role(role:str):
    return require_role(role)(None)
