from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from quote_requests.models import QuoteRequest
from unittest.mock import patch
import uuid
from decimal import Decimal
import json
from django.http import JsonResponse
from quote_requests.models import QuoteItem


User = get_user_model()


class AcceptQuoteViewTest(TestCase):
    """
    Tests for the accept_quote view in the quote_requests app.
    """

    def setUp(self):
        """
        Set up a superuser and a valid quote in REVIEWED status.
        """
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )

        self.quote = QuoteRequest.objects.create(
            name="Test User",
            email="customer@example.com",
            status="REVIEWED",
            response_token=uuid.uuid4()
        )

        self.url = reverse('accept_quote', args=[self.quote.pk])

    @patch('quote_requests.views.render_quote_pdf_bytes',
           return_value=b'%PDF-mock')
    @patch('quote_requests.views.EmailMultiAlternatives.send',
           return_value=1)
    def test_accept_quote_success_as_superuser(
        self, mock_send, mock_pdf
    ):
        """
        Superuser should be able to accept a reviewed quote.
        Sends PDF to customer and redirects.
        """
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(self.url)

        self.assertRedirects(
            response, reverse('quote_detail', args=[self.quote.pk])
        )

        self.quote.refresh_from_db()

        mock_pdf.assert_called_once()
        mock_send.assert_called()

    def test_access_denied_for_non_superuser(self):
        """
        Regular users should be redirected to login when accessing view.
        """
        user = User.objects.create_user(
            username='notadmin',
            email='user@example.com',
            password='userpass'
        )
        self.client.login(username='notadmin', password='userpass')
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class CreatePaymentIntentTest(TestCase):
    """
    Tests for the create_payment_intent view.
    """

    def setUp(self):
        """
        Set up a test quote with valid items and tax to ensure
        Stripe receives a non-zero amount.
        """
        self.quote = QuoteRequest.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            status="REVIEWED",
            response_token=uuid.uuid4(),
            tax_percent=Decimal("20.0")
        )

        QuoteItem.objects.create(
            quote=self.quote,
            description="Example Service",
            quantity=2,
            unit_price=Decimal("125.00")
        )

        self.quote.calculate_totals()

        self.url = reverse(
            'create_payment_intent', args=[self.quote.pk]
        )

    @patch('quote_requests.views.stripe.PaymentIntent.create')
    def test_successful_payment_intent_creation(self, mock_create):
        """
        Should return clientSecret when quote is valid.
        """
        mock_create.return_value.client_secret = 'fake_client_secret'

        response = self.client.post(self.url, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('clientSecret', data)
        self.assertEqual(data['clientSecret'], 'fake_client_secret')

        mock_create.assert_called_once_with(
            amount=30000,
            currency='usd',
            metadata={'quote_id': str(self.quote.id)},
            description=f"Payment for Quote #{self.quote.id}",
        )

    def test_rejects_get_requests(self):
        """
        Should return 400 for GET requests.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('POST required', response.content.decode())

    def test_quote_not_found(self):
        """
        Should return 404 if quote ID is invalid.
        """
        url = reverse('create_payment_intent', args=[9999])
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Quote not found', response.content.decode())
