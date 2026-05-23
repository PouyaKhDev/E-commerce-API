from django.core.exceptions import ValidationError

from cart.models import Cart, CartItem

from cart.exceptions import UserCartNotFound, CartItemNotFound


def get_cart(*, user):
    """Retrieve the cart for provided user"""
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        raise UserCartNotFound("User does not have a cart")

    return cart


def get_item(*, cart, product):
    """Retrieve an item with provided cart and product"""
    try:
        item = CartItem.objects.get(cart=cart, product=product)
    except CartItem.DoesNotExist:
        raise CartItemNotFound("There is no such product in the cart")

    return item


def get_total_item_price(*, item):
    """Retrieve total price for an item"""
    return item.product.price * item.quantity


def get_total_cart_price(*, cart):
    """Retrieve total price of cart"""
    items = cart.items.select_related("product").all()  # type: ignore

    cart_total_price = 0
    for item in items:
        cart_total_price += item.product.price * item.quantity
    return cart_total_price


def get_total_cart_items(*, cart):
    """Retrieve total items' quantity"""
    return sum(cart.items.values_list("quantity", flat=True))
