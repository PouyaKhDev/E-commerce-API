"""
Test custom Django management commands.
"""

from unittest.mock import patch, MagicMock

from psycopg2 import OperationalError as Psycopg2Error
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


class CommandTests(SimpleTestCase):
    """Test wait_for_db management command"""

    @patch("core.management.commands.wait_for_db.time.sleep")
    # Patch where it is used in your app, not where it comes from in Django
    @patch("core.management.commands.wait_for_db.connections")
    def test_wait_for_db_ready(self, mocked_connections, mocked_sleep):
        """Test waiting for database when database is ready immediately."""
        # Arrange
        mocked_conn = MagicMock()
        mocked_cursor = MagicMock()
        mocked_conn.cursor.return_value = mocked_cursor
        mocked_connections.__getitem__.return_value = mocked_conn

        # Act
        call_command("wait_for_db")

        # Assert
        mocked_connections.__getitem__.assert_called_once_with("default")
        mocked_conn.cursor.assert_called_once()
        mocked_sleep.assert_not_called()

    @patch("core.management.commands.wait_for_db.time.sleep")
    # Patch where it is used in your app, not where it comes from in Django
    @patch("core.management.commands.wait_for_db.connections")
    def test_wait_for_db_delay(self, mocked_connections, mocked_sleep):
        """Test waiting for database when getting OperationalError / Psycopg2Error."""
        # Arrange
        mocked_conn = MagicMock()
        mocked_cursor = MagicMock()

        # First 2 calls: Psycopg2Error
        # Next 3 calls: Django OperationalError
        # 6th call: success (returns mocked_cursor)
        mocked_conn.cursor.side_effect = (
            [Psycopg2Error] * 2 + [OperationalError] * 3 + [mocked_cursor]
        )
        mocked_connections.__getitem__.return_value = mocked_conn

        # Act
        call_command("wait_for_db")

        # Assert: we tried 6 times, slept 5 times
        mocked_connections.__getitem__.assert_called_with("default")
        self.assertEqual(mocked_conn.cursor.call_count, 6)
        self.assertEqual(mocked_sleep.call_count, 5)
