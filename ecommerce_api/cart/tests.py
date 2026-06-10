from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from cart import selectors, services
from cart.exceptions import (
    UserCartNotFound,
    CartItemNotFound,
    DuplicateCartItem,
)

from shop.models import Product

User = get_user_model()


# ---------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------
class CartSelectorsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")

        self.product1 = Product.objects.create(
            name="P1",
            description="D1",
            price=Decimal("10.00"),
            is_active=True,
        )
        self.product2 = Product.objects.create(
            name="P2",
            description="D2",
            price=Decimal("7.50"),
            is_active=True,
        )

    def test_get_cart_raises_when_missing(self):
        with self.assertRaises(UserCartNotFound):
            selectors.get_cart(user=self.user)

    def test_get_cart_returns_cart(self):
        cart = Cart.objects.create(user=self.user)

        got = selectors.get_cart(user=self.user)
        self.assertEqual(got.id, cart.id)
        self.assertEqual(got.user, self.user)

    def test_get_item_raises_when_missing(self):
        cart = Cart.objects.create(user=self.user)

        with self.assertRaises(CartItemNotFound):
            selectors.get_item(cart=cart, product=self.product1)

    def test_get_item_returns_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=2)

        got = selectors.get_item(cart=cart, product=self.product1)
        self.assertEqual(got.id, item.id)
        self.assertEqual(got.quantity, 2)

    def test_get_total_item_price(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=3)

        self.assertEqual(selectors.get_total_item_price(item=item), Decimal("30.00"))

    def test_get_total_cart_price(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=4)

        self.assertEqual(selectors.get_total_cart_price(cart=cart), Decimal("50.00"))

    def test_get_total_cart_items(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=4)

        self.assertEqual(selectors.get_total_cart_items(cart=cart), 6)


# ---------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------
class CartServicesTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.product1 = Product.objects.create(
            name="P1",
            description="D1",
            price=Decimal("10.00"),
            is_active=True,
        )

    def test_get_or_create_cart_creates_when_missing(self):
        self.assertEqual(Cart.objects.count(), 0)

        cart = services.get_or_create_cart(user=self.user)

        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(cart.user, self.user)

    def test_get_or_create_cart_returns_existing(self):
        cart1 = services.get_or_create_cart(user=self.user)
        cart2 = services.get_or_create_cart(user=self.user)

        self.assertEqual(cart1.id, cart2.id)
        self.assertEqual(Cart.objects.count(), 1)

    def test_create_item_creates_when_missing(self):
        cart = Cart.objects.create(user=self.user)

        item = services.create_item(cart=cart, product=self.product1, quantity=2)

        self.assertEqual(item.cart, cart)
        self.assertEqual(item.product, self.product1)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_create_item_raises_duplicate_when_exists(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)

        with self.assertRaises(DuplicateCartItem):
            services.create_item(cart=cart, product=self.product1, quantity=2)


# ---------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------
class CartAPITests(APITestCase):
    """
    Uses your router configuration:

        router.register("cart", CartViewSet, basename="cart")
        router.register("cart/items", CartItemViewSet, basename="cart-item")

    So route names are:
        - cart-list
        - cart-item-list
        - cart-item-detail
    """

    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.client.force_authenticate(user=self.user)

        self.other = User.objects.create_user(username="u2", password="pass12345")

        self.product1 = Product.objects.create(
            name="P1",
            description="D1",
            price=Decimal("10.00"),
            is_active=True,
        )
        self.product2 = Product.objects.create(
            name="P2",
            description="D2",
            price=Decimal("7.50"),
            is_active=True,
        )

        self.cart_list_url = reverse("cart-list")
        self.cart_item_list_url = reverse("cart-item-list")

    def test_cart_list_requires_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(self.cart_list_url)
        self.assertIn(
            res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )

    def test_cart_list_creates_cart_and_returns_empty_list(self):
        self.assertEqual(Cart.objects.count(), 0)

        res = self.client.get(self.cart_list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data, list)
        self.assertEqual(len(res.data), 0)

        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(Cart.objects.get().user, self.user)

    def test_create_cart_item_success(self):
        cart = services.get_or_create_cart(user=self.user)

        payload = {"product_id": self.product1.id, "quantity": 3}
        res = self.client.post(self.cart_item_list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)

        item = CartItem.objects.get(cart=cart, product=self.product1)
        self.assertEqual(item.quantity, 3)

        self.assertIn("id", res.data)
        self.assertIn("product", res.data)
        self.assertIn("unit_price", res.data)
        self.assertIn("total_price", res.data)
        self.assertNotIn("product_id", res.data)

        self.assertEqual(res.data["product"]["id"], self.product1.id)
        self.assertEqual(Decimal(res.data["unit_price"]), Decimal("10.00"))
        self.assertEqual(Decimal(res.data["total_price"]), Decimal("30.00"))

    def test_create_cart_item_when_cart_missing_returns_400(self):
        """
        Current serializer.create calls selectors.get_cart (not get_or_create),
        so if the cart doesn't exist this should raise UserCartNotFound (APIException => 400).
        """
        payload = {"product_id": self.product1.id, "quantity": 1}
        res = self.client.post(self.cart_item_list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("detail", res.data)

    def test_create_cart_item_rejects_quantity_zero(self):
        services.get_or_create_cart(user=self.user)

        payload = {"product_id": self.product1.id, "quantity": 0}
        res = self.client.post(self.cart_item_list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", res.data)

    def test_create_cart_item_rejects_duplicate(self):
        cart = services.get_or_create_cart(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)

        payload = {"product_id": self.product1.id, "quantity": 2}
        res = self.client.post(self.cart_item_list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

    def test_update_cart_item_quantity_success(self):
        cart = services.get_or_create_cart(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)

        url = reverse("cart-item-detail", args=[item.id])
        res = self.client.patch(url, {"quantity": 5}, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

        self.assertEqual(Decimal(res.data["total_price"]), Decimal("50.00"))

    def test_update_cart_item_cannot_change_product(self):
        cart = services.get_or_create_cart(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)

        url = reverse("cart-item-detail", args=[item.id])

        res = self.client.patch(url, {"product_id": self.product2.id}, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("product_id" in res.data or "product" in res.data)

    def test_delete_cart_item_success(self):
        cart = services.get_or_create_cart(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)

        url = reverse("cart-item-detail", args=[item.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_cart_item_queryset_is_user_scoped(self):
        other_cart = services.get_or_create_cart(user=self.other)
        other_item = CartItem.objects.create(
            cart=other_cart, product=self.product1, quantity=2
        )

        my_cart = services.get_or_create_cart(user=self.user)
        my_item = CartItem.objects.create(
            cart=my_cart, product=self.product2, quantity=1
        )

        url = reverse("cart-item-detail", args=[other_item.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        my_url = reverse("cart-item-detail", args=[my_item.id])
        res2 = self.client.patch(my_url, {"quantity": 3}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        my_item.refresh_from_db()
        self.assertEqual(my_item.quantity, 3)
