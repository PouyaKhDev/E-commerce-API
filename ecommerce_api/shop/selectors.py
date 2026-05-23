from django.db.models import QuerySet

from shop.models import Category, Product, Order


def category_list(*, include_inactive: bool = True) -> QuerySet[Category]:
    qs = Category.objects.all()
    return qs


def product_list(*, active_only: bool = True) -> QuerySet[Product]:
    qs = Product.objects.all()
    if active_only:
        qs = qs.filter(is_active=True)
    return qs


def order_list_for_user(*, user) -> QuerySet[Order]:
    qs = Order.objects.all().prefetch_related("items__product")
    if getattr(user, "is_staff", False):
        return qs
    return qs.filter(user=user)


def order_get_for_user(*, user, pk: int) -> Order:
    return order_list_for_user(user=user).get(pk=pk)
