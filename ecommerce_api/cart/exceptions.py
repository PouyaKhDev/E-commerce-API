from rest_framework import status
from rest_framework.exceptions import APIException


class CartError(APIException):
    """Base cart error"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Cart error"
    default_code = "cart_error"


class UserCartNotFound(CartError):
    """A cart is not found"""

    default_detail = "Cart is not found"
    default_code = "cart_not_found"


class CartItemNotFound(CartError):
    """A cart item is not found"""

    default_detail = "Item not found"
    default_code = "item_not_found"


class DuplicateCart(CartError):
    """There is already a cart"""

    default_detail = "Cart already exists"
    default_code = "duplicate_cart"


class DuplicateCartItem(CartError):
    """The product is already in the cart"""

    default_detail = "Item already exists"
    default_code = "duplicate_item"
