"""
Tests for Tag API.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(**params):
    "Creates and return a new user"
    defaults = {
        'email': "test@example.com",
        'password': "testpass123",
        'name': "Test User"
    }

    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def create_tag(user, name="Main Dish"):
    """Create and returns a new Tag"""
    return Tag.objects.create(
        user=user,
        name=name
    )


class PublicTagAPITests(TestCase):
    """Test public tag API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call the Tag API."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITests(TestCase):
    """Test private Tag API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    # We want to test getting all tags
    def test_retrieve_tags(self):
        """Test for retrieving all the tags."""
        create_tag(user=self.user)
        create_tag(user=self.user)

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    # We want to test getting a specific tag
    def test_retrieve_tags_limited_to_the_user(self):
        """Test for retrieving tags created by the user only."""
        other_user = create_user(
            email='otheruser@example.com',
            password='otheruserpass123'
        )

        create_tag(user=other_user)
        tag = create_tag(user=self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    # We want to test updating a tag by the user
    def test_update_tag(self):
        """Test updating a tag."""
        tag = create_tag(user=self.user)
        payload = {
            'name': 'Dessert'
        }

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user, self.user)

    # We want to test deleting a tag
    def test_delete_tag(self):
        tag = create_tag(user=self.user)

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id))

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags by those assigned to recipes."""
        tag1 = create_tag(user=self.user, name="Apple")
        tag2 = create_tag(user=self.user, name="Turkey")
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )

        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list."""
        tag1 = create_tag(user=self.user, name="Apple")
        Tag.objects.create(user=self.user, name='Lentils')

        recipe1 = Recipe.objects.create(
            title='Eggs',
            time_minutes=60,
            price=Decimal('7.00'),
            user=self.user
        )

        recipe2 = Recipe.objects.create(
            title='Her eggs',
            time_minutes=20,
            price=Decimal('4.00'),
            user=self.user
        )

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
