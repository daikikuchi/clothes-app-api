from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Material

from clothes.serializers import MaterialSerializer

MATERIALS_URL = reverse('clothes:material-list')


class PublicMaterialsApiTests(TestCase):
    """Test the publicly available Materials API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(MATERIALS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMaterialApiTests(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'kikuchi.dai@gmail.com',
            'password',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_material_list(self):
        """Test retrieving a list of materials"""
        Material.objects.create(user=self.user, name='Cotton')
        Material.objects.create(user=self.user, name='Wool')

        res = self.client.get(MATERIALS_URL)

        materials = Material.objects.all().order_by('-name')
        serializer = MaterialSerializer(materials, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_materials_limited_to_user(self):
        """Test that materials for the authenticated user are returned"""
        user2 = get_user_model().objects.create_user(
            'hana@gmail.com',
            'password2',
        )
        Material.objects.create(user=user2, name='Linen')
        material = Material.objects.create(user=self.user, name='Wool')

        res = self.client.get(MATERIALS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], material.name)

    def test_create_material_successful(self):
        """Test creating a new material"""
        payload = {'name': 'Cotton'}
        self.client.post(MATERIALS_URL, payload)

        exists = Material.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test Creating invalid ingredient fails"""
        payload = {'name': ''}
        res = self.client.post(MATERIALS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
