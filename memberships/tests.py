from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from memberships.models import ServicePackage, ServiceAgreement
from accounts.models import Profile, Property
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test.client import RequestFactory
from memberships.views import update_package_property
import json


User = get_user_model()


class BasicPackageCreationTest(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='pass1234'
        )
        self.profile = self.superuser.profile
        self.profile.profile_completed = True
        self.profile.save()

        self.client.login(username='admin', password='pass1234')

        self.url = reverse('servicepackage_create')

    def test_can_create_package_with_valid_data(self):
        data = {
            'name': 'Basic Package',
            'description': 'Test description',
            'price_usd': 50.00,
            'is_active': True,
            'category': 'B2B',
            'tier': 'SINGLE',
        }

        response = self.client.post(self.url, data)

        print(response.content)

        self.assertEqual(response.status_code, 302)

        self.assertTrue(ServicePackage.objects.filter(name='Basic Package').exists())


class UpdatePackagePropertyTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass1234'
        )
        self.profile = self.user.profile
        self.profile.profile_completed = True
        self.profile.save()

        self.property = Property.objects.create(
            profile=self.profile,
            label="Home",
            address_line_1="123 Main St",
            city="Orlando",
            postcode="32801",
            country="USA",
        )

        self.package = ServicePackage.objects.create(
            name="Test Package",
            category="B2B",
            tier="SINGLE",
            description="Description",
            price_usd=50.00,
        )

        self.url = reverse('update_package_property', args=[self.package.id])

    def test_update_package_property_success(self):
        request = self.factory.post(
            self.url,
            data=json.dumps({'property_id': self.property.id}),
            content_type='application/json'
        )
        request.user = self.user

        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()

        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        request.session['selected_packages'] = {
            'B2B': {
                'id': self.package.id,
                'name': self.package.name,
                'property_id': None,
                'property_label': None,
                'property_address_summary': None,
            }
        }

        response = update_package_property(request, self.package.id)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['package']['property_id'], self.property.id)
