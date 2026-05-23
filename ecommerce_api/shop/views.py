from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from shop.models import Category, Order
from shop.serializers import CategorySerializer, ProductSerializer, OrderSerializer
from shop.selectors import product_list, order_list_for_user
from shop.services import create_order_from_cart, pay_order, staff_update_order_status
from core.permissions import IsStaffOrReadOnly, IsOwnerOrStaff


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "slug"


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "category": ["exact"],
        "price": ["gte", "lte"],
    }
    search_fields = ["name"]
    ordering_fields = ["name", "price", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return product_list(active_only=True)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        return order_list_for_user(user=self.request.user)

    def create(self, request, *args, **kwargs):
        order = create_order_from_cart(user=request.user)
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        order: Order = self.get_object()
        order = pay_order(order=order, success=request.data.get("success", True))
        return Response(self.get_serializer(order).data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsAdminUser],
        url_path="status",
    )
    def update_status(self, request, pk=None):
        order: Order = self.get_object()
        status_value = request.data.get("status")
        order = staff_update_order_status(order=order, status_value=status_value)
        return Response(OrderSerializer(order).data)
