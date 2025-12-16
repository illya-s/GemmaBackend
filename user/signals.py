from .models import Role

def create_default_roles(sender, **kwargs):
    roles = ["admin", "user", "moderator"]
    for role in roles:
        Role.objects.get_or_create(name=role)
