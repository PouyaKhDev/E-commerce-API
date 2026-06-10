from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserViewSetTests(APITestCase):
    def setUp(self):
        self.list_create_url = reverse("user-list")

        self.admin = User.objects.create_superuser(
            username="admin", password="admin-pass"
        )
        self.user1 = User.objects.create_user(username="user1", password="user1-pass")
        self.user2 = User.objects.create_user(username="user2", password="user2-pass")

    def detail_url(self, pk):
        return reverse("user-detail", kwargs={"pk": pk})

    # -------------------------
    # CREATE
    # -------------------------
    def test_create_user_is_allowed_without_auth(self):
        payload = {"username": "newuser", "password": "new-pass-123"}
        res = self.client.post(self.list_create_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

        created = User.objects.get(username="newuser")
        self.assertTrue(created.check_password("new-pass-123"))
        self.assertNotIn("password", res.data)

    # -------------------------
    # LIST
    # -------------------------
    def test_list_users_requires_admin(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(self.list_create_url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_admin_can_list(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self.list_create_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_usernames = {item["username"] for item in res.data}
        self.assertTrue({"admin", "user1", "user2"}.issubset(returned_usernames))

        for item in res.data:
            self.assertNotIn("password", item)

    # -------------------------
    # RETRIEVE
    # -------------------------
    def test_retrieve_requires_auth(self):
        res = self.client.get(self.detail_url(self.user1.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_returns_only_authenticated_users_own_record(self):
        self.client.force_authenticate(user=self.user1)

        res_ok = self.client.get(self.detail_url(self.user1.pk))
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data["username"], "user1")
        self.assertNotIn("password", res_ok.data)

        res_other = self.client.get(self.detail_url(self.user2.pk))
        self.assertEqual(res_other.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # UPDATE / PARTIAL UPDATE
    # -------------------------
    def test_update_user_can_only_update_self_and_password_is_hashed(self):
        self.client.force_authenticate(user=self.user1)

        payload = {"username": "user1-renamed", "password": "new-secret"}
        res = self.client.put(self.detail_url(self.user1.pk), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, "user1-renamed")
        self.assertTrue(self.user1.check_password("new-secret"))
        self.assertNotIn("password", res.data)

    def test_partial_update_user_can_change_password(self):
        self.client.force_authenticate(user=self.user1)

        payload = {"password": "partial-new-secret"}
        res = self.client.patch(self.detail_url(self.user1.pk), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password("partial-new-secret"))
        self.assertNotIn("password", res.data)

    def test_update_other_user_is_not_found(self):
        self.client.force_authenticate(user=self.user1)

        payload = {"username": "hacked"}
        res = self.client.patch(self.detail_url(self.user2.pk), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # DELETE
    # -------------------------
    def test_delete_self_allowed_and_deletes_user(self):
        self.client.force_authenticate(user=self.user2)

        res = self.client.delete(self.detail_url(self.user2.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user2.pk).exists())

    def test_delete_other_user_not_found(self):
        self.client.force_authenticate(user=self.user1)

        res = self.client.delete(self.detail_url(self.user2.pk))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
