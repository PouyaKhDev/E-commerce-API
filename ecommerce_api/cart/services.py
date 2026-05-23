from django.db import IntegrityError, transaction


from cart.models import Cart, CartItem

from cart import selectors
from cart.exceptions import UserCartNotFound, CartItemNotFound, DuplicateCartItem


@transaction.atomic()
def get_or_create_cart(*, user):
    """Retrieve or create cart for provided user"""
    try:
        cart = selectors.get_cart(user=user)
    except UserCartNotFound:
        cart = Cart.objects.create(user=user)
    return cart


@transaction.atomic()
def create_item(*, cart, product, quantity):
    """Create a cart item"""
    try:
        item = selectors.get_item(cart=cart, product=product)
        if item:
            raise IntegrityError()
    except IntegrityError:
        raise DuplicateCartItem("The product is already in the cart")
    except CartItemNotFound:
        item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)

    return item
