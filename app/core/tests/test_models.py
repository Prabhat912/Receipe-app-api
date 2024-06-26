"""
Tests for Model
"""
from unittest.mock import patch
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


@patch('core.models.uuid.uuid4')
def test_receipe_filename_uuid(self, mock_uuid):
    """
    Test Generating image path
    """
    uuid = 'test-uuid'
    mock_uuid.return_value = uuid
    file_path = models.receipe_image_file_path(None, 'example.jpg')
    self.assertEqual(file_path, f'uploads/receipe/{uuid}.jpg')


def create_user(email='user@example.com', password='test123'):
    """
    Create and return a new user
    """
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """
    Test Model Class
    """

    def test_create_user_with_email_successful(self):
        """
        Test Creating a user with an email is successful
        """
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """
        Test Email is Normalize for new users
        """
        sampleEmails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['test2@EXAMPLE.COM', 'test2@example.com'],
            ['Test3@example.COM', 'Test3@example.com'],
            ['test4@Example.COM', 'test4@example.com'],
            ]
        for email, expectedEmail in sampleEmails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expectedEmail)

    def test_new_user_without_email_raise_error(self):
        """
        Test that creating a user without an email will raise a Value Error
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """
        Test for creating a super user
        """
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test1123',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_receipe(self):
        """
        Test Creating a receipe is successful.
        """
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        receipe = models.Receipe.objects.create(
            user=user,
            title='Sample Receipe Name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample Receipe Description',
        )

        self.assertEqual(str(receipe), receipe.title)

    def test_create_tag(self):
        """
        Test creating a tag is successful
        """
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """
        Test creating an ingredient is successful
        """
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Ingredient1'
        )

        self.assertEqual(str(ingredient), ingredient.name)
