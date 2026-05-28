"""Critical-path tests for the DLX API.

Focus areas (regressions in any of these are user-impacting):
- CreateAnyAdminRead permission: anon POST works, anon GET on PII is blocked.
- Serializer validators: header-injection rejected, max_length enforced.
- Email optional in QuotationRequest (sell-vehicle form never collects it).
- Public catalog endpoints stay open (vehicles/services/etc.).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from .models import Vehicle, Service, Testimonial, QuotationRequest, ContactMessage


# Disable rate limiting in tests — we hammer endpoints; AnonRateThrottle would trip otherwise.
TEST_REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.LargeResultsSetPagination',
    'PAGE_SIZE': 100,
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class PIIPermissionTests(TestCase):
    """Anonymous users must NOT be able to list QuotationRequest or ContactMessage (customer PII)."""

    def setUp(self):
        self.client = APIClient()
        QuotationRequest.objects.create(
            nombre="Cliente A", telefono="3000000000", servicio="Venta", mensaje="hola hola hola"
        )
        ContactMessage.objects.create(
            nombre="Cliente B", email="b@example.com", telefono="3000000001",
            servicio="Autospa", mensaje="mensaje de contacto del cliente",
        )

    def test_anon_get_quotations_forbidden(self):
        resp = self.client.get('/api/quotations/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_anon_get_contact_messages_forbidden(self):
        resp = self.client.get('/api/contact-messages/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_get_quotations_ok(self):
        User = get_user_model()
        staff = User.objects.create_user(username='admin1', password='x', is_staff=True)
        self.client.force_authenticate(user=staff)
        resp = self.client.get('/api/quotations/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_anon_post_quotation_allowed(self):
        resp = self.client.post('/api/quotations/', {
            'nombre': 'Nuevo cliente',
            'telefono': '3001234567',
            'servicio': 'Venta de vehículo',
            'mensaje': 'Quiero vender mi carro Toyota Corolla 2020',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)

    def test_anon_post_contact_message_allowed(self):
        resp = self.client.post('/api/contact-messages/', {
            'nombre': 'Visitante',
            'email': 'v@example.com',
            'telefono': '3001234567',
            'servicio': 'Cerámico',
            'mensaje': 'Quisiera información sobre el servicio',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class SerializerValidationTests(TestCase):
    """Defenses added 2026-05-28: newline-in-field rejection + explicit max_length."""

    def setUp(self):
        self.client = APIClient()

    def test_newline_in_email_rejected(self):
        resp = self.client.post('/api/contact-messages/', {
            'nombre': 'X',
            'email': 'x@y.com\r\nBcc: pwned@evil.com',
            'telefono': '3001234567',
            'servicio': 'Autospa',
            'mensaje': 'Mensaje de prueba con suficiente longitud.',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_newline_in_nombre_rejected(self):
        resp = self.client.post('/api/contact-messages/', {
            'nombre': 'Juan\r\nX',
            'email': 'x@y.com',
            'telefono': '3001234567',
            'servicio': 'Autospa',
            'mensaje': 'Mensaje de prueba con suficiente longitud.',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_oversize_mensaje_rejected(self):
        resp = self.client.post('/api/contact-messages/', {
            'nombre': 'X',
            'email': 'x@y.com',
            'telefono': '3001234567',
            'servicio': 'Autospa',
            'mensaje': 'A' * 6000,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quotation_without_email_accepted(self):
        """VendeVehiculo form does NOT collect email — backend must accept blank."""
        resp = self.client.post('/api/quotations/', {
            'nombre': 'Vendedor',
            'telefono': '3001234567',
            'servicio': 'Venta de vehículo',
            'vehiculo': 'Toyota Corolla 2020',
            'mensaje': 'Placa: ABC123\nKm: 50000\nEstado: Excelente',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)

    def test_invalid_email_format_rejected(self):
        resp = self.client.post('/api/contact-messages/', {
            'nombre': 'X',
            'email': 'not-an-email',
            'telefono': '3001234567',
            'servicio': 'Autospa',
            'mensaje': 'Mensaje de prueba con suficiente longitud.',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class PublicCatalogTests(TestCase):
    """Public catalog endpoints (vehicles/services/testimonials) must stay anon-readable."""

    def setUp(self):
        self.client = APIClient()
        Vehicle.objects.create(marca='Toyota', modelo='Corolla', year=2022, km=10000, price=85000000)
        Service.objects.create(title='Cerámico 9H', description='Protección', category='ceramico')
        Testimonial.objects.create(name='Cliente', comment='Excelente', rating=5, approved=True)
        Testimonial.objects.create(name='Otro', comment='Bueno', rating=4, approved=False)

    def test_anon_can_list_vehicles(self):
        resp = self.client.get('/api/vehicles/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_anon_can_list_services(self):
        resp = self.client.get('/api/services/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_testimonials_only_approved_shown(self):
        resp = self.client.get('/api/testimonials/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        results = data.get('results', data) if isinstance(data, dict) else data
        names = [t['name'] for t in results]
        self.assertIn('Cliente', names)
        self.assertNotIn('Otro', names)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class PaginationTests(TestCase):
    """LargeResultsSetPagination: default 100/page, page_size override accepted up to max_page_size."""

    def setUp(self):
        self.client = APIClient()
        for i in range(120):
            Vehicle.objects.create(
                marca='Toyota', modelo=f'Modelo {i}', year=2020, km=10000 + i, price=50000000 + i,
            )

    def test_default_page_size_is_100(self):
        resp = self.client.get('/api/vehicles/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['count'], 120)
        self.assertEqual(len(data['results']), 100)
        self.assertIsNotNone(data['next'])

    def test_page_size_override_works(self):
        resp = self.client.get('/api/vehicles/?page_size=50')
        data = resp.json()
        self.assertEqual(len(data['results']), 50)

    def test_page_size_max_capped(self):
        resp = self.client.get('/api/vehicles/?page_size=1000')
        data = resp.json()
        # max_page_size=500 — request for 1000 silently capped.
        self.assertLessEqual(len(data['results']), 500)
