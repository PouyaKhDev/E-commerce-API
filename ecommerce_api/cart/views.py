from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from cart.serializers import CartItemSerializer
from cart import services, selectors
from cart.exceptions import CartItemNotFound

# Create your views here.


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Create a new item.",
        responses={200: CartItemSerializer(many=True)},
    )
    def list(self, request):
        """Return current user's cart"""
        cart = services.get_or_create_cart(user=request.user)
        serializer = CartItemSerializer(cart.items.all(), many=True)  # type: ignore
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart = selectors.get_cart(user=self.request.user)
        return cart.items  # type: ignore
