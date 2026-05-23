from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import F
from django.db.models.query import QuerySet

from cart.models import Cart
from shop.exceptions import (
    CartEmptyError,
    InsufficientStockError,
    InvalidOrderStateError,
)
from shop.models import Order, OrderItem, Product


def _coerce_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}
    return default


@transaction.atomic
def create_order_from_cart(*, user) -> Order:
    cart, _ = Cart.objects.get_or_create(user=user)
    cart_items = cart.items.select_related("product")  # type: ignore

    if not cart_items.exists():
        raise CartEmptyError()

    product_ids = list(cart_items.values_list("product_id", flat=True))
    products_qs: QuerySet[Product] = Product.objects.select_for_update().filter(
        id__in=product_ids
    )
    products_by_id = {p.pk: p for p in products_qs}

    for item in cart_items:
        product = products_by_id[item.product_id]
        if item.quantity > product.stock:
            raise InsufficientStockError(product.name, product.stock)

    order = Order.objects.create(
        user=user, status=Order.STATUS_PENDING, total_amount=Decimal("0")
    )

    total = Decimal("0")
    order_items_to_create: list[OrderItem] = []

    for item in cart_items:
        product = products_by_id[item.product_id]

        order_items_to_create.append(
            OrderItem(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price,
            )
        )

        Product.objects.filter(pk=product.pk).update(stock=F("stock") - item.quantity)
        total += product.price * item.quantity

    OrderItem.objects.bulk_create(order_items_to_create)

    order.total_amount = total
    order.save(update_fields=["total_amount"])

    cart_items.delete()
    return order


@transaction.atomic
def pay_order(*, order: Order, success: Any = True) -> Order:
    if order.status != Order.STATUS_PENDING:
        raise InvalidOrderStateError()

    success_bool = _coerce_bool(success, default=True)

    if success_bool:
        order.status = Order.STATUS_PAID
    else:
        order.status = Order.STATUS_CANCELLED

    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def staff_update_order_status(*, order: Order, status_value: str) -> Order:
    valid = {c[0] for c in Order.STATUS_CHOICES}
    if status_value not in valid:
        raise InvalidOrderStateError(detail="Invalid status value.")

    order.status = status_value
    order.save(update_fields=["status", "updated_at"])
    return order
