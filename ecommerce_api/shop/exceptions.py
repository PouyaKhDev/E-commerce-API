from rest_framework import status
from rest_framework.exceptions import APIException


class ShopError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Shop error."
    default_code = "shop_error"


class CartEmptyError(ShopError):
    default_detail = "Cart is empty."
    default_code = "cart_empty"


class InsufficientStockError(ShopError):
    default_code = "insufficient_stock"

    def __init__(self, product_name: str, available: int):
        super().__init__(
            detail=f"Not enough stock for {product_name}. Available: {available}"
        )


class InvalidOrderStateError(ShopError):
    default_code = "invalid_order_state"

    def __init__(self, detail: str = "Order is not in pending state."):
        super().__init__(detail=detail)


class OrderNotOwnedError(ShopError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to access this order."
    default_code = "order_not_owned"
