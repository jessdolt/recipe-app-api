"""
Tests for the ingredients API.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return a ingredient detail url."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(**params):
    "Creates and return a new user"
    defaults = {
        'email': "test@example.com",
        'password': "testpass123",
        'name': "Test User"
    }

    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def create_ingredient(user, name="Tomato"):
    """Create and returns a new Tag"""
    return Ingredient.objects.create(
        user=user,
        name=name
    )


class PublicAPITests(TestCase):
    """Test for unauthenticated users."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateAPITests(TestCase):
    """Tests for authenticated users."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieving_ingredients(self):
        """Test for listing all the ingredients."""

        create_ingredient(user=self.user)
        create_ingredient(user=self.user)

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all()
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(serializer.data), 2)

    def test_retrieving_ingredients_limited_to_the_user(self):
        """Test for retrieving detail ingredients."""
        other_user = create_user(
            email='otheruser@example.com',
            password="otheruserpass123"
        )

        create_ingredient(user=self.user)
        create_ingredient(user=other_user)

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.filter(user=self.user)
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(serializer.data), 1)

    def test_update_ingredients(self):
        """Test for updating an ingredient."""
        ingredient = create_ingredient(user=self.user)
        payload = {'name': 'Mango'}

        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])
        self.assertEqual(ingredient.user, self.user)

    def test_delete_ingredients(self):
        """Test for deleting an ingredient."""
        ingredient = create_ingredient(user=self.user)

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id))
