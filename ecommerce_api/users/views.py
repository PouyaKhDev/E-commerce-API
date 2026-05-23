from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view


from users import services, selectors
from users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = selectors.get_users()
    serializer_class = UserSerializer

    def get_permissions(self):
        permission_mapping = {
            "create": [AllowAny],
            "list": [IsAdminUser],
        }

        permission_classes = permission_mapping.get(self.action, [IsAuthenticated])

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.action not in ["create", "list"]:
            return selectors.get_user_queryset(user_id=self.request.user.pk)
        return self.queryset
