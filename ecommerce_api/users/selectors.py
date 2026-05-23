from django.contrib.auth import get_user_model

User = get_user_model()


def get_users():
    """Retrieve users as queryset"""
    return User.objects.all()


def get_user_queryset(*, user_id):
    """Retrieve user as queryset"""
    return User.objects.filter(pk=user_id)
