from rest_framework import serializers
from .models import (
    Vehicle, Testimonial, Service, QuotationRequest,
    ContactMessage, CreditOption, InsuranceProduct, CompanyInfo
)


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
    class Meta:
        model = Testimonial
        fields = '__all__'
        read_only_fields = ['approved', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class QuotationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationRequest
        fields = '__all__'
        read_only_fields = ['estado', 'created_at', 'updated_at']


class ContactMessageSerializer(serializers.ModelSerializer):
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
