from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Vehicle, Testimonial, Service, QuotationRequest,
    ContactMessage, CreditOption, InsuranceProduct, CompanyInfo
)
from .serializers import (
    VehicleSerializer, VehicleListSerializer, TestimonialSerializer,
    ServiceSerializer, QuotationRequestSerializer, ContactMessageSerializer,
    CreditOptionSerializer, InsuranceProductSerializer, CompanyInfoSerializer
)


class CreateAnyAdminRead(permissions.BasePermission):
    """Anonymous users can POST (submit form); only staff can list/retrieve customer data."""
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return bool(request.user and request.user.is_staff)


class VehicleViewSet(viewsets.ModelViewSet):
    """
    API para gestión de vehículos.
    GET /api/vehicles/ - Lista todos los vehículos disponibles
    GET /api/vehicles/{id}/ - Detalle de un vehículo
    GET /api/vehicles/?marca=Toyota&year=2022 - Filtrar vehículos
    """
    queryset = Vehicle.objects.filter(estado='disponible')
    serializer_class = VehicleSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['marca', 'modelo']
    ordering_fields = ['price', 'year', 'km', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer

    def get_queryset(self):
        queryset = Vehicle.objects.all()

        # Filtros personalizados
        marca = self.request.query_params.get('marca')
        year = self.request.query_params.get('year')
        price_max = self.request.query_params.get('price_max')
        estado = self.request.query_params.get('estado')

        if marca:
            queryset = queryset.filter(marca__iexact=marca)
        if year:
            queryset = queryset.filter(year=year)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        if estado:
            queryset = queryset.filter(estado=estado)
        else:
            # Por defecto solo mostrar disponibles
            queryset = queryset.filter(estado='disponible')

        return queryset


class TestimonialViewSet(viewsets.ModelViewSet):
    """
    API para testimonios de clientes.
    GET /api/testimonials/ - Lista testimonios aprobados
    POST /api/testimonials/ - Crear nuevo testimonio
    """
    queryset = Testimonial.objects.filter(approved=True)
    serializer_class = TestimonialSerializer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        # Solo mostrar testimonios aprobados en GET
        if self.action == 'list':
            return Testimonial.objects.filter(approved=True)
        return Testimonial.objects.all()


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para servicios de autospa.
    GET /api/services/ - Lista todos los servicios activos
    GET /api/services/{id}/ - Detalle de un servicio
    GET /api/services/?category=ceramico - Filtrar por categoría
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer

    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class QuotationRequestViewSet(viewsets.ModelViewSet):
    """
    POST /api/quotations/  — anyone can submit a quotation request.
    GET  /api/quotations/  — staff only (contains customer PII).
    """
    queryset = QuotationRequest.objects.all()
    serializer_class = QuotationRequestSerializer
    permission_classes = [CreateAnyAdminRead]
    http_method_names = ['post', 'get']


class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    POST /api/contact-messages/  — anyone can send a contact message.
    GET  /api/contact-messages/  — staff only (contains customer PII).
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [CreateAnyAdminRead]
    http_method_names = ['post', 'get']


class CreditOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para opciones de crédito/financiamiento.
    GET /api/credit-options/ - Lista opciones de crédito activas
    """
    queryset = CreditOption.objects.filter(is_active=True)
    serializer_class = CreditOptionSerializer


class InsuranceProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para productos de seguros.
    GET /api/insurance-products/ - Lista seguros activos
    GET /api/insurance-products/?tipo=soat - Filtrar por tipo
    """
    queryset = InsuranceProduct.objects.filter(is_active=True)
    serializer_class = InsuranceProductSerializer

    def get_queryset(self):
        queryset = InsuranceProduct.objects.filter(is_active=True)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


class CompanyInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para información de la empresa.
    GET /api/company-info/ - Obtiene información de la empresa
    """
    queryset = CompanyInfo.objects.all()
    serializer_class = CompanyInfoSerializer

    def list(self, request):
        # Retorna singleton de información de empresa
        try:
            instance = CompanyInfo.objects.first()
            if instance:
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            return Response({})
        except CompanyInfo.DoesNotExist:
            return Response({})
