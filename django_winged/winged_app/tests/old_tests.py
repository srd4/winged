from django.test import TestCase
from ..models import Container, Item, StatementVersion
from django.utils import timezone
from django.test import tag

from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status




class ContainerTestCase(TestCase):
    fixtures = ['data']
    
    """def test_delete(self):
        parent = Container.objects.get(pk=12)
        child = Container.objects.get(pk=13)

        parent_initial_values = [e for e in parent.item_set.all()]
        child_initial_values = [i for i in child.item_set.all()]

        self.assertEqual(child.parent_container, parent)

        child.delete()

        self.assertQuerysetEqual(qs=parent.item_set.all(), values=parent_initial_values + child_initial_values, ordered=False)
        self.assertRaises(Container.DoesNotExist, Container.objects.get, pk=13)"""


    def test_update_last_opened_at(self):
        # inbox.
        container = Container.objects.get(pk=1)

        # save last time opened.
        old_time = container.last_opened_at

        # update last time opened to timezone.now()
        container.update_last_opened_at()

        new_time = container.last_opened_at

        #assert there's more time from old_time to present than from new time.
        self.assertEqual(timezone.now() - old_time > timezone.now() - new_time , True)

        #assert that new_time was changed to timezone.now less than a second ago.
        self.assertLess(timezone.now() - new_time, timezone.timedelta(seconds=1))


    """def test_toggle_collapsed(self):
        containers = Container.objects.all()

        for container in containers:
            state_before = container.is_collapsed

            container.toggle_collapsed()

            state_after = container.is_collapsed

            self.assertEqual(state_after, not state_before)"""


    def test_toggle_tab(self):
        containers = Container.objects.all()

        for container in containers:
            state_before = container.is_on_actionables_tab

            container.toggle_tab()

            state_after = container.is_on_actionables_tab

            self.assertEqual(state_after, not state_before, msg=f"{container}, {state_before}, {state_after}")
    

    """def test_count_items_tree(self):
        expect = {
            'inbox':46,
            'notebook 2.0':19+150+41+33+33+104,
            'notebook 2.0 features':150+41+33+33,
            'myself':49+163+41+38+3+67+60+6+22+14,
        }

        for i in expect:
            # assert count_items_tree equal to expected above item count for its tree.
            self.assertEqual(Container.objects.get(name=i).count_items_tree(), expect[i], msg=f"{i}")"""


@tag('item')
class ItemTestCase(TestCase):

    fixtures = ['data']

    def test_save(self):
        item = Item.objects.get(pk=202)
        last_statement_version_saved = StatementVersion.objects.last()

        item.save()

        self.assertEqual(last_statement_version_saved, StatementVersion.objects.last())

        item.statement = "new statement"

        item.save()

        self.assertNotEqual(last_statement_version_saved, StatementVersion.objects.last())

        self.assertEqual(StatementVersion.objects.last().statement, "gotta see other website builds and other people's portfolio websites for basically copying like artists do.")

@tag('token')
class TokenAuthenticationTestCase(TestCase):
    fixtures = ['data']

    def test_obtain_token(self):
        client = APIClient()
        response = client.post(reverse('api_token_auth'), {'username': 'flac', 'password': 'pepito56'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data