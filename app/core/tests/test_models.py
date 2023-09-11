"""
Tests for Model
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


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
