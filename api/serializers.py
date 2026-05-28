from rest_framework import serializers
from .models import (
    Vehicle, Testimonial, Service, QuotationRequest,
    ContactMessage, CreditOption, InsuranceProduct, CompanyInfo
)


def _no_newlines(value: str) -> str:
    """Reject control chars / CRLF in single-line fields — basic email-header-injection guard."""
    if value and any(c in value for c in '\r\n\x00'):
        raise serializers.ValidationError('Caracteres no permitidos.')
    return value


class VehicleSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = '__all__'

    def get_imagen_url(self, obj):
        """Devuelve la URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


class VehicleListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['id', 'marca', 'modelo', 'year', 'km', 'price', 'estado', 'imagen', 'imagen_url']

    def get_imagen_url(self, obj):
        """Devuelve la URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


class TestimonialSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, validators=[_no_newlines])
    comment = serializers.CharField(max_length=2000)
    service = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True, validators=[_no_newlines])

    class Meta:
        model = Testimonial
        fields = '__all__'
        read_only_fields = ['approved', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class QuotationRequestSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=100, validators=[_no_newlines])
    # Email opcional: el form "vende tu carro" no lo solicita para reducir fricción de conversión.
    email = serializers.EmailField(max_length=254, required=False, allow_blank=True, allow_null=True, validators=[_no_newlines])
    telefono = serializers.CharField(max_length=20, validators=[_no_newlines])
    servicio = serializers.CharField(max_length=100, validators=[_no_newlines])
    mensaje = serializers.CharField(max_length=5000)
    vehiculo = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True, validators=[_no_newlines])

    class Meta:
        model = QuotationRequest
        fields = '__all__'
        read_only_fields = ['estado', 'created_at', 'updated_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=100, validators=[_no_newlines])
    email = serializers.EmailField(max_length=254, validators=[_no_newlines])
    telefono = serializers.CharField(max_length=20, validators=[_no_newlines])
    servicio = serializers.CharField(max_length=100, validators=[_no_newlines])
    mensaje = serializers.CharField(max_length=5000)

    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = ['leido', 'created_at']


class CreditOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditOption
        fields = '__all__'


class InsuranceProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProduct
        fields = '__all__'


class CompanyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInfo
        fields = '__all__'
