"""
Tests for receipe APIs.
"""
import tempfile
import os

from PIL import Image
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Receipe, Tag, Ingredient

from receipe.serializers import ReceipeSerializer, ReceipeDetailSerializer


RECEIPES_URL = reverse('receipe:receipe-list')


def detail_url(receipe_id):
    """
    Create and return a receipe detail url
    """
    return reverse('receipe:receipe-detail', args=[receipe_id])


def image_upload_url(receipe_id):
    """Create and return an image upload URL."""
    return reverse('receipe:receipe-upload-image', args=[receipe_id])


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

    def test_create_receipe_with_new_ingredients(self):
        """Test creating a receipe with new ingredients."""
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }
        res = self.client.post(RECEIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        receipes = Receipe.objects.filter(user=self.user)
        self.assertEqual(receipes.count(), 1)
        receipe = receipes[0]
        self.assertEqual(receipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = receipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {
            'title': 'Vietnamese Soup',
            'time_minutes': 25,
            'price': '2.55',
            'ingredients': [{'name': 'Lemon'}, {'name': 'Fish Sauce'}],
        }
        res = self.client.post(RECEIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        receipes = Receipe.objects.filter(user=self.user)
        self.assertEqual(receipes.count(), 1)
        receipe = receipes[0]
        self.assertEqual(receipe.ingredients.count(), 2)
        self.assertIn(ingredient, receipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = receipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe."""
        receipe = create_receipe(user=self.user)

        payload = {'ingredients': [{'name': 'Limes'}]}
        url = detail_url(receipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Limes')
        self.assertIn(new_ingredient, receipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        receipe = create_receipe(user=self.user)
        receipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')
        payload = {'ingredients': [{'name': 'Chili'}]}
        url = detail_url(receipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, receipe.ingredients.all())
        self.assertNotIn(ingredient1, receipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a receipes ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name='Garlic')
        receipe = create_receipe(user=self.user)
        receipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(receipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(receipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """
        Test Filtering Receipes by tags
        """
        r1 = create_receipe(user=self.user, title='Thai Veg')
        r2 = create_receipe(user=self.user, title='Aubergine Tahini')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegeterian')

        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_receipe(user=self.user, title='Fish and Chip')

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECEIPES_URL, params)

        s1 = ReceipeSerializer(r1)
        s2 = ReceipeSerializer(r2)
        s3 = ReceipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """
        Test Filtering Receipes by ingredients
        """
        r1 = create_receipe(user=self.user, title='Posh Bean')
        r2 = create_receipe(user=self.user, title='Chicken Caccitore')
        in1 = Ingredient.objects.create(user=self.user, name='Feta Cheese')
        in2 = Ingredient.objects.create(user=self.user, name='Chicken')

        r1.ingredients.add(in1)
        r2.ingredients.add(in2)
        r3 = create_receipe(user=self.user, title='Fish and Chip')

        params = {'ingredients': f'{in1.id},{in2.id}'}
        res = self.client.get(RECEIPES_URL, params)

        s1 = ReceipeSerializer(r1)
        s2 = ReceipeSerializer(r2)
        s3 = ReceipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.receipe = create_receipe(user=self.user)

    def tearDown(self):
        self.receipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.receipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.receipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.receipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.receipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
