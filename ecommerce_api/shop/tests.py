from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from shop.models import Category, Product, Order
from shop.services import _coerce_bool

User = get_user_model()


class ShopAPITests(APITestCase):
    """
    Tests for shop endpoints + order/cart integration.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="pass12345")
        cls.other_user = User.objects.create_user(username="bob", password="pass12345")
        cls.staff = User.objects.create_user(
            username="admin", password="pass12345", is_staff=True
        )

        cls.category = Category.objects.create(name="Books", slug="books")

        cls.p1 = Product.objects.create(
            category=cls.category,
            name="Django for APIs",
            description="...",
            price=Decimal("10.00"),
            stock=5,
            is_active=True,
        )
        cls.p2 = Product.objects.create(
            category=cls.category,
            name="Inactive product",
            description="...",
            price=Decimal("20.00"),
            stock=5,
            is_active=False,
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # -----------------------------
    # Categories
    # -----------------------------
    def test_category_list_anonymous_allowed(self):
        res = self.client.get(reverse("category-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_category_create_anonymous_denied(self):
        res = self.client.post(
            reverse("category-list"),
            data={"name": "Games", "slug": "games"},
            format="json",
        )
        self.assertIn(
            res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )

    def test_category_create_staff_allowed(self):
        self.auth(self.staff)
        res = self.client.post(
            reverse("category-list"),
            data={"name": "Games", "slug": "games"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["slug"], "games")

    def test_category_retrieve_by_slug(self):
        res = self.client.get(
            reverse("category-detail", kwargs={"slug": self.category.slug})
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["slug"], self.category.slug)

    # -----------------------------
    # Products
    # -----------------------------
    def test_product_list_only_active(self):
        res = self.client.get(reverse("product-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        names = [p["name"] for p in res.data]
        self.assertIn(self.p1.name, names)
        self.assertNotIn(self.p2.name, names)

    def test_product_create_staff_only(self):
        payload = {
            "name": "New product",
            "description": "desc",
            "price": "9.99",
            "stock": 3,
            "is_active": True,
            "category_id": self.category.id,
        }

        res = self.client.post(reverse("product-list"), data=payload, format="json")
        self.assertIn(
            res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )

        self.auth(self.staff)
        res = self.client.post(reverse("product-list"), data=payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["name"], "New product")
        self.assertEqual(res.data["category"]["id"], self.category.id)

    def test_product_filter_by_category_exact(self):
        other_cat = Category.objects.create(name="Electronics", slug="electronics")
        Product.objects.create(
            category=other_cat,
            name="Headphones",
            description="",
            price=Decimal("50.00"),
            stock=2,
            is_active=True,
        )

        res = self.client.get(reverse("product-list"), data={"category": other_cat.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "Headphones")

    def test_product_search_by_name(self):
        res = self.client.get(reverse("product-list"), data={"search": "Django"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], self.p1.name)

    # -----------------------------
    # Orders / cart integration
    # -----------------------------
    def test_orders_require_authentication(self):
        res = self.client.get(reverse("order-list"))
        self.assertIn(
            res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )

    def test_create_order_from_empty_cart_returns_400(self):
        self.auth(self.user)
        res = self.client.post(reverse("order-list"), data={}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

    def test_create_order_success_decrements_stock_and_clears_cart(self):

        self.auth(self.user)

        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.p1, quantity=2)

        res = self.client.post(reverse("order-list"), data={}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.assertEqual(res.data["status"], Order.STATUS_PENDING)
        self.assertEqual(Decimal(res.data["total_amount"]), Decimal("20.00"))
        self.assertEqual(len(res.data["items"]), 1)
        self.assertEqual(res.data["items"][0]["quantity"], 2)

        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 3)

        cart.refresh_from_db()
        self.assertFalse(cart.items.exists())

    def test_create_order_insufficient_stock_returns_400_and_does_not_change_stock(
        self,
    ):
        self.auth(self.user)

        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.p1, quantity=999)

        before = self.p1.stock

        res = self.client.post(reverse("order-list"), data={}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, before)
        self.assertTrue(cart.items.exists())

    def test_user_sees_only_own_orders_in_list(self):
        o1 = Order.objects.create(
            user=self.user, status=Order.STATUS_PENDING, total_amount=Decimal("0")
        )
        o2 = Order.objects.create(
            user=self.other_user, status=Order.STATUS_PENDING, total_amount=Decimal("0")
        )

        self.auth(self.user)
        res = self.client.get(reverse("order-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ids = [o["id"] for o in res.data]
        self.assertIn(o1.id, ids)
        self.assertNotIn(o2.id, ids)

    def test_user_cannot_access_other_users_order_detail_returns_404(self):
        """
        Strict expected behavior in your codebase:

        - OrderViewSet.get_queryset() uses order_list_for_user(user=request.user)
          which filters to only that user's orders for non-staff.
        - Therefore another user's order is not in queryset => get_object() => 404.
        """
        order = Order.objects.create(
            user=self.other_user,
            status=Order.STATUS_PENDING,
            total_amount=Decimal("10.00"),
        )

        self.auth(self.user)
        res = self.client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_pay_other_users_order_returns_404(self):
        order = Order.objects.create(
            user=self.other_user,
            status=Order.STATUS_PENDING,
            total_amount=Decimal("10.00"),
        )

        self.auth(self.user)
        res = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            data={"success": True},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_access_other_users_order_detail(self):
        order = Order.objects.create(
            user=self.other_user,
            status=Order.STATUS_PENDING,
            total_amount=Decimal("10.00"),
        )

        self.auth(self.staff)
        res = self.client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], order.id)

    # -----------------------------
    # Order actions
    # -----------------------------
    def test_pay_order_success_true_marks_paid(self):
        self.auth(self.user)
        order = Order.objects.create(
            user=self.user, status=Order.STATUS_PENDING, total_amount=Decimal("10.00")
        )

        res = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            data={"success": True},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Order.STATUS_PAID)

    def test_pay_order_success_false_marks_cancelled(self):
        self.auth(self.user)
        order = Order.objects.create(
            user=self.user, status=Order.STATUS_PENDING, total_amount=Decimal("10.00")
        )

        res = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            data={"success": False},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Order.STATUS_CANCELLED)

    def test_pay_order_non_pending_returns_400(self):
        self.auth(self.user)
        order = Order.objects.create(
            user=self.user, status=Order.STATUS_PAID, total_amount=Decimal("10.00")
        )

        res = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            data={"success": True},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

    def test_pay_order_coerces_truthy_and_falsy_strings(self):
        self.assertTrue(_coerce_bool("true"))
        self.assertTrue(_coerce_bool("1"))
        self.assertTrue(_coerce_bool("Yes"))
        self.assertTrue(_coerce_bool("on"))
        self.assertFalse(_coerce_bool("false"))
        self.assertFalse(_coerce_bool("0"))
        self.assertFalse(_coerce_bool("off"))

        self.auth(self.user)
        order = Order.objects.create(
            user=self.user, status=Order.STATUS_PENDING, total_amount=Decimal("10.00")
        )
        res = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            data={"success": "false"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Order.STATUS_CANCELLED)

    def test_update_status_admin_only(self):
        order = Order.objects.create(
            user=self.user, status=Order.STATUS_PENDING, total_amount=Decimal("10.00")
        )
        url = reverse("order-update-status", kwargs={"pk": order.pk})

        self.auth(self.user)
        res = self.client.patch(
            url, data={"status": Order.STATUS_SHIPPED}, format="json"
        )
        self.assertIn(
            res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )

        self.auth(self.staff)
        res = self.client.patch(
            url, data={"status": Order.STATUS_SHIPPED}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Order.STATUS_SHIPPED)

    def test_update_status_invalid_value_returns_400(self):
        self.auth(self.staff)
        order = Order.objects.create(
            user=self.user, status=Order.STATUS_PENDING, total_amount=Decimal("10.00")
        )

        res = self.client.patch(
            reverse("order-update-status", kwargs={"pk": order.pk}),
            data={"status": "not-a-real-status"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)
