"""
Tests for receipe APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Receipe, Tag

from receipe.serializers import ReceipeSerializer, ReceipeDetailSerializer


RECEIPES_URL = reverse('receipe:receipe-list')


def detail_url(receipe_id):
    """
    Create and return a receipe detail url
    """
    return reverse('receipe:receipe-detail', args=[receipe_id])


def create_receipe(user, **params):
    """Create and return a sample receipe."""
    defaults = {
        'title': 'Sample receipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/receipe.pdf',
    }
    defaults.update(params)

    receipe = Receipe.objects.create(user=user, **defaults)
    return receipe


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicReceipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECEIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateReceipeApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_receipes(self):
        """Test retrieving a list of receipes."""
        create_receipe(user=self.user)
        create_receipe(user=self.user)

        res = self.client.get(RECEIPES_URL)

        receipes = Receipe.objects.all().order_by('-id')
        serializer = ReceipeSerializer(receipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_receipe_list_limited_to_user(self):
        """Test list of receipes is limited to authenticated user."""
        other_user = create_user(email='other@example.com', password='pass123')
        create_receipe(user=other_user)
        create_receipe(user=self.user)

        res = self.client.get(RECEIPES_URL)

        receipes = Receipe.objects.filter(user=self.user)
        serializer = ReceipeSerializer(receipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_receipe_detail(self):
        """
        Test get receipe details
        """
        receipe = create_receipe(user=self.user)
        url = detail_url(receipe.id)
        res = self.client.get(url)

        serializer = ReceipeDetailSerializer(receipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_receipe(self):
        """Test creating a receipe."""
        payload = {
            'title': 'Sample receipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }
        res = self.client.post(RECEIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        receipe = Receipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(receipe, k), v)
        self.assertEqual(receipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a receipe."""
        original_link = 'https://example.com/receipe.pdf'
        receipe = create_receipe(
            user=self.user,
            title='Sample receipe title',
            link=original_link,
        )

        payload = {'title': 'New receipe title'}
        url = detail_url(receipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        receipe.refresh_from_db()
        self.assertEqual(receipe.title, payload['title'])
        self.assertEqual(receipe.link, original_link)
        self.assertEqual(receipe.user, self.user)

    def test_full_update(self):
        """Test full update of receipe."""
        receipe = create_receipe(
            user=self.user,
            title='Sample receipe title',
            link='https://exmaple.com/receipe.pdf',
            description='Sample receipe description.',
        )

        payload = {
            'title': 'New receipe title',
            'link': 'https://example.com/new-receipe.pdf',
            'description': 'New receipe description',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }
        url = detail_url(receipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        receipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(receipe, k), v)
        self.assertEqual(receipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the receipe user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        receipe = create_receipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(receipe.id)
        self.client.patch(url, payload)

        receipe.refresh_from_db()
        self.assertEqual(receipe.user, self.user)

    def test_delete_receipe(self):
        """Test deleting a receipe successful."""
        receipe = create_receipe(user=self.user)

        url = detail_url(receipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Receipe.objects.filter(id=receipe.id).exists())

    def test_receipe_other_users_receipe_error(self):
        """Test trying to delete another users receipe gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        receipe = create_receipe(user=new_user)

        url = detail_url(receipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Receipe.objects.filter(id=receipe.id).exists())

    def test_create_receipe_with_new_tags(self):
        """Test creating a receipe with new tags."""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECEIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        receipes = Receipe.objects.filter(user=self.user)
        self.assertEqual(receipes.count(), 1)
        receipe = receipes[0]
        self.assertEqual(receipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = receipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_receipe_with_existing_tags(self):
        """Test creating a receipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECEIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        receipes = Receipe.objects.filter(user=self.user)
        self.assertEqual(receipes.count(), 1)
        receipe = receipes[0]
        self.assertEqual(receipe.tags.count(), 2)
        self.assertIn(tag_indian, receipe.tags.all())
        for tag in payload['tags']:
            exists = receipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test create tag when updating a receipe."""
        receipe = create_receipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(receipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, receipe.tags.all())

    def test_update_receipe_assign_tag(self):
        """Test assigning an existing tag when updating a receipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        receipe = create_receipe(user=self.user)
        receipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(receipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, receipe.tags.all())
        self.assertNotIn(tag_breakfast, receipe.tags.all())

    def test_clear_receipe_tags(self):
        """Test clearing a receipes tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        receipe = create_receipe(user=self.user)
        receipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(receipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(receipe.tags.count(), 0)
