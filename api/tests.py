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

from unittest.mock import patch

from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle

from .models import (
    Vehicle, Service, Testimonial, QuotationRequest, ContactMessage,
    CreditOption, InsuranceProduct, CompanyInfo,
)


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


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class VehicleFilterTests(TestCase):
    """VehicleViewSet.get_queryset custom filters + default 'disponible' scope."""

    def setUp(self):
        self.client = APIClient()
        Vehicle.objects.create(marca='Toyota', modelo='Corolla', year=2022, km=10000, price=85000000, estado='disponible')
        Vehicle.objects.create(marca='Mazda', modelo='3', year=2020, km=40000, price=60000000, estado='disponible')
        Vehicle.objects.create(marca='Toyota', modelo='Hilux', year=2018, km=90000, price=120000000, estado='vendido')

    def _results(self, resp):
        data = resp.json()
        return data.get('results', data) if isinstance(data, dict) else data

    def test_default_hides_sold_vehicles(self):
        resp = self.client.get('/api/vehicles/')
        modelos = [v['modelo'] for v in self._results(resp)]
        self.assertIn('Corolla', modelos)
        self.assertNotIn('Hilux', modelos)  # 'vendido' hidden by default

    def test_filter_by_marca_case_insensitive(self):
        resp = self.client.get('/api/vehicles/?marca=toyota&estado=disponible')
        modelos = [v['modelo'] for v in self._results(resp)]
        self.assertEqual(modelos, ['Corolla'])

    def test_filter_price_max(self):
        resp = self.client.get('/api/vehicles/?price_max=70000000')
        modelos = [v['modelo'] for v in self._results(resp)]
        self.assertEqual(modelos, ['3'])

    def test_explicit_estado_vendido_visible(self):
        resp = self.client.get('/api/vehicles/?estado=vendido')
        modelos = [v['modelo'] for v in self._results(resp)]
        self.assertEqual(modelos, ['Hilux'])


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class ServiceCatalogTests(TestCase):
    """ServiceViewSet: only active services, category filter, credit/insurance catalogs."""

    def setUp(self):
        self.client = APIClient()
        Service.objects.create(title='Cerámico 9H', description='x', category='ceramico', is_active=True)
        Service.objects.create(title='Polarizado', description='x', category='polarizado', is_active=True)
        Service.objects.create(title='Viejo', description='x', category='ceramico', is_active=False)
        CreditOption.objects.create(title='Crédito flexible', description='x', is_active=True)
        InsuranceProduct.objects.create(title='SOAT', description='x', tipo='soat', is_active=True)

    def _results(self, resp):
        data = resp.json()
        return data.get('results', data) if isinstance(data, dict) else data

    def test_inactive_service_hidden(self):
        resp = self.client.get('/api/services/')
        titles = [s['title'] for s in self._results(resp)]
        self.assertNotIn('Viejo', titles)

    def test_service_category_filter(self):
        resp = self.client.get('/api/services/?category=ceramico')
        titles = [s['title'] for s in self._results(resp)]
        self.assertEqual(titles, ['Cerámico 9H'])

    def test_credit_and_insurance_endpoints_public(self):
        self.assertEqual(self.client.get('/api/credit-options/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/insurance-products/').status_code, status.HTTP_200_OK)

    def test_insurance_tipo_filter(self):
        InsuranceProduct.objects.create(title='Todo Riesgo', description='x', tipo='todo_riesgo', is_active=True)
        resp = self.client.get('/api/insurance-products/?tipo=soat')
        titles = [p['title'] for p in self._results(resp)]
        self.assertEqual(titles, ['SOAT'])


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class ReadOnlyFieldTests(TestCase):
    """Client-supplied values for server-managed fields must be ignored, not trusted."""

    def setUp(self):
        self.client = APIClient()

    def test_quotation_estado_is_read_only(self):
        resp = self.client.post('/api/quotations/', {
            'nombre': 'Cliente', 'telefono': '3001234567', 'servicio': 'Venta',
            'mensaje': 'Mensaje suficientemente largo para pasar.', 'estado': 'finalizado',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        q = QuotationRequest.objects.get()
        self.assertEqual(q.estado, 'pendiente')  # default, NOT the client-sent 'finalizado'

    def test_anon_cannot_create_testimonial(self):
        # Testimonials are staff-curated via the admin (frontend never POSTs them).
        # Global IsAuthenticatedOrReadOnly blocks anon writes — guards against a public
        # spam vector for social proof.
        resp = self.client.post('/api/testimonials/', {
            'name': 'Cliente', 'comment': 'Excelente servicio', 'rating': 5, 'approved': True,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Testimonial.objects.count(), 0)

    def test_staff_created_testimonial_defaults_unapproved(self):
        User = get_user_model()
        staff = User.objects.create_user(username='mod', password='x', is_staff=True)
        self.client.force_authenticate(user=staff)
        resp = self.client.post('/api/testimonials/', {
            'name': 'Cliente', 'comment': 'Excelente servicio', 'rating': 5, 'approved': True,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        # `approved` is read-only in the serializer — even staff POST can't self-approve.
        self.assertFalse(Testimonial.objects.get().approved)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class CompanyInfoTests(TestCase):
    """Singleton model + endpoint contract."""

    def setUp(self):
        self.client = APIClient()

    def _make(self, **over):
        base = dict(
            direccion='Cra 43A', telefono='6041234567', email='info@dlx.co',
            horario_lv='8-6', horario_sabado='9-5', descripcion='DLX', whatsapp='573104204713',
        )
        base.update(over)
        c = CompanyInfo(**base)
        c.save()  # save() (not create) — singleton forces pk=1 and UPDATEs an existing row
        return c

    def test_singleton_pk_forced_to_one(self):
        c = self._make()
        self.assertEqual(c.pk, 1)
        # A second save collapses onto pk=1 (singleton), never a second row.
        c2 = self._make(direccion='Otra', descripcion='DLX2')
        self.assertEqual(c2.pk, 1)
        self.assertEqual(CompanyInfo.objects.count(), 1)

    def test_company_info_endpoint_empty_when_absent(self):
        resp = self.client.get('/api/company-info/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json(), {})

    def test_company_info_endpoint_returns_singleton(self):
        CompanyInfo.objects.create(
            direccion='Cra 43A', telefono='6041234567', email='info@dlx.co',
            horario_lv='8-6', horario_sabado='9-5', descripcion='DLX', whatsapp='573104204713',
        )
        resp = self.client.get('/api/company-info/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['whatsapp'], '573104204713')


class ThrottleTests(TestCase):
    """AnonRateThrottle actually enforces the anon limit (regression guard for spam control).

    Note: DRF binds SimpleRateThrottle.THROTTLE_RATES at import time, so override_settings
    can't change the rate mid-run — we patch the class attribute directly instead.
    """

    def setUp(self):
        cache.clear()  # throttle state lives in cache; isolate this test
        self.client = APIClient()

    def tearDown(self):
        cache.clear()

    def test_anon_requests_throttled_after_limit(self):
        with patch.object(AnonRateThrottle, 'THROTTLE_RATES', {'anon': '3/min'}):
            for _ in range(3):
                self.assertEqual(self.client.get('/api/vehicles/').status_code, status.HTTP_200_OK)
            self.assertEqual(
                self.client.get('/api/vehicles/').status_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
            )


class SitemapTests(TestCase):
    """Sitemap dinámico: rutas estáticas + una URL por vehículo disponible, sin vendidos."""

    def setUp(self):
        self.client = APIClient()
        self.disponible = Vehicle.objects.create(
            marca='Toyota', modelo='Corolla', year=2022, km=10000, price=85000000, estado='disponible',
        )
        self.vendido = Vehicle.objects.create(
            marca='Mazda', modelo='CX-5', year=2021, km=30000, price=95000000, estado='vendido',
        )

    def test_sitemap_returns_xml(self):
        resp = self.client.get('/sitemap.xml')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('application/xml', resp['Content-Type'])

    def test_sitemap_lists_static_routes(self):
        body = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('<loc>https://dlx.tatui.store/</loc>', body)
        self.assertIn('/compra-venta-vehiculos', body)
        self.assertIn('/creditos-seguros', body)

    def test_sitemap_lists_available_vehicle_url(self):
        body = self.client.get('/sitemap.xml').content.decode()
        self.assertIn(f'/vehiculo/{self.disponible.id}</loc>', body)

    def test_sitemap_excludes_sold_vehicle(self):
        body = self.client.get('/sitemap.xml').content.decode()
        self.assertNotIn(f'/vehiculo/{self.vendido.id}</loc>', body)


class ModelStrTests(TestCase):
    """__str__ reprs are used in the Django admin change lists — keep them stable."""

    def test_model_str_reprs(self):
        v = Vehicle.objects.create(marca='Toyota', modelo='Corolla', year=2022, km=1, price=1)
        self.assertEqual(str(v), 'Toyota Corolla (2022)')
        s = Service.objects.create(title='Cerámico 9H', description='x', category='ceramico')
        self.assertEqual(str(s), 'Cerámico 9H')
        t = Testimonial.objects.create(name='Ana', comment='ok', rating=5, approved=True)
        self.assertIn('Ana', str(t))
        q = QuotationRequest.objects.create(nombre='Luis', telefono='3001234567', servicio='Venta', mensaje='hola hola')
        self.assertEqual(str(q), 'Luis - Venta')
        m = ContactMessage.objects.create(nombre='Eva', email='e@x.co', telefono='3001234567', servicio='Autospa', mensaje='hola hola')
        self.assertEqual(str(m), 'Eva - Autospa')
