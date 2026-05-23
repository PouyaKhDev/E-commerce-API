from django.urls import path, include
from rest_framework.routers import DefaultRouter

from shop.views import (
    CategoryViewSet,
    ProductViewSet,
    OrderViewSet,
)
from cart.views import CartViewSet, CartItemViewSet
from users.views import UserViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("cart", CartViewSet, basename="cart")
router.register("cart/items", CartItemViewSet, basename="cart-item")
router.register("orders", OrderViewSet, basename="order")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
