"""
Django command to wait for the database to be available
"""

import time

from psycopg2 import OperationalError as Psycopg2Error

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    """Django command to wait for database"""

    def handle(self, *args, **options):
        """Entry point for command"""

        self.stdout.write("Waiting for the database...")
        db_up = False

        while not db_up:
            try:
                conn = connections["default"]
                conn.cursor()
            except (Psycopg2Error, OperationalError):
                self.stdout.write("Database is unavailable, waiting for 1 second...")
                time.sleep(1)
            else:
                db_up = True

        self.stdout.write(self.style.SUCCESS("Database available!"))
