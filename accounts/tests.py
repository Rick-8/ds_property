from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress


class UserRegistrationTest(TestCase):
    def test_user_can_register(self):
        registration_url = reverse('account_signup')
        response = self.client.post(registration_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'email2': 'testuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        print(response.content.decode())
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)
        self.assertIn(response.status_code, [302, 200])


class UserLoginTest(TestCase):
    def setUp(self):
        self.test_email = 'testlogin@example.com'
        self.test_username = 'testlogin'
        self.test_password = 'TestLogin123!'
        user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password
        )
        EmailAddress.objects.create(
            user=user,
            email=self.test_email,
            verified=True,
            primary=True
        )

    def test_user_can_login(self):
        login_url = reverse('account_login')
        response = self.client.post(login_url, {
            'login': self.test_username,
            'password': self.test_password,
        })
        print(response.content.decode())
        self.assertEqual(response.status_code, 302)

        user_id = self.client.session.get('_auth_user_id')
        self.assertIsNotNone(user_id)
