"""
Tests for recipe APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Receipe

from receipe.serializers import ReceipeSerializer


RECEIPES_URL = reverse('receipe:receipe-list')


def create_receipe(user, **params):
    """Create and return a sample receipe."""
    defaults = {
        'title': 'Sample receipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    receipe = Receipe.objects.create(user=user, **defaults)
    return receipe


class PublicReceipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECEIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_receipe(user=self.user)
        create_receipe(user=self.user)

        res = self.client.get(RECEIPES_URL)

        receipes = Receipe.objects.all().order_by('-id')
        serializer = ReceipeSerializer(receipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_receipe_list_limited_to_user(self):
        """Test list of receipes is limited to authenticated user."""
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'password123',
        )
        create_receipe(user=other_user)
        create_receipe(user=self.user)

        res = self.client.get(RECEIPES_URL)

        receipes = Receipe.objects.filter(user=self.user)
        serializer = ReceipeSerializer(receipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
