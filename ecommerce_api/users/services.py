from django.contrib.auth import get_user_model

User = get_user_model()


def create_user(*, username, password):
    """Create and return a user"""
    return User.objects.create_user(username=username, password=password)
