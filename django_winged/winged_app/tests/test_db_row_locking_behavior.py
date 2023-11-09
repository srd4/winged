import time
import threading

from decimal import Decimal

from django.test import TransactionTestCase
from django.db import transaction, connections, DatabaseError
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth.models import User

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from winged_app.models import Item, Container


class DataBaseItemTableRowLockTest(TransactionTestCase):
    """
    Checking the database does handle concurrency as we are expecting.
    """
    def setUp(self):
        self.user = User.objects.create_user('first_user', 'first_user@example.com', 'testpass')
        self.container = Container.objects.create(name="first_user_container", user=self.user)
        self.item = Item.objects.create(statement="Test Item", parent_container=self.container, user=self.user)

        self.user_token = Token.objects.create(user=self.user)

        self.client = APIClient()

        self.lock_duration_in_seconds = 3

    def item_locking_script(self, pk, lock_acquired_event):
        try:
            item_query_set = Item.objects.filter(pk=pk).select_for_update()
            
            with transaction.atomic():
                self.time_lock_start = timezone.now()
                lock_acquired_event.set()

                # Assert patch hasn't gone through.
                self.assertEqual(Item.objects.get(pk=pk).statement, "Test Item")

                # Update statement from here.
                item_query_set.filter(pk=pk).update(statement="here")

                # Sleep.
                time.sleep(self.lock_duration_in_seconds)

                self.time_lock_finish = timezone.now()
        except Exception as e:
            print("script_error: ", e)
        finally:
            connections.close_all()


    def test_concurrent_row_access(self):
        lock_acquired_event = threading.Event()

        t = threading.Thread(target=self.item_locking_script, args=(self.item.pk, lock_acquired_event))
        t.start()

        self.client.force_authenticate(user=self.user)
        url = reverse('items-detail', kwargs={'pk': self.item.pk})

        lock_acquired_event.wait()

        self.time_patch_attempt = timezone.now()
        response = self.client.patch(url, {'statement': 'updated'})

        t.join()
        # Assert patch didn't run before lock.
        self.assertGreaterEqual(self.time_patch_attempt, self.time_lock_start)

        # Assert patch was able to finish still.
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.statement, "updated")

        # Assert patch was actually done after lock was released.
        self.assertGreater((timezone.now() - self.item.created_at).total_seconds(), self.lock_duration_in_seconds)

    
    def test_concurrent_second_instance_creation(self):
        lock_acquired_event = threading.Event()

        t = threading.Thread(target=self.item_locking_script, args=(self.item.pk, lock_acquired_event))
        t.start()

        self.client.force_authenticate(user=self.user)

        lock_acquired_event.wait()

        self.time_put_attempt = timezone.now()
        response = self.client.post("/items/", {'statement':'second test item statement',
                                         'parent_container': self.container.pk,
                                         'user':self.user.pk,
                                         })
        t.join()

        # Assert put was attempted before lock finish
        self.assertGreater((self.time_lock_finish - self.time_put_attempt).total_seconds(), 0.0)
        # Assert put was attempted immediately or at the same time as lock_start.
        self.assertAlmostEqual((self.time_put_attempt - self.time_lock_start).total_seconds(), 0.0, places=1)

        # Assert put request success
        self.assertEqual(response.status_code, 201)
        new_item = Item.objects.last()
        self.assertEqual(new_item.statement, "second test item statement")

        # Assert post was done while other item row was locked.
        self.assertGreater(self.lock_duration_in_seconds, (new_item.created_at - self.time_put_attempt).total_seconds())