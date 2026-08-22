from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User as AuthUser


class CommentAPITests(APITestCase):
    def setUp(self):
        self.user = AuthUser.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/comments/'

    def test_list_comments(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
