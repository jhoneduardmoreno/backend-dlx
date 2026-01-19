from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import (
    Vehicle, Testimonial, Service, QuotationRequest,
    ContactMessage, CreditOption, InsuranceProduct, CompanyInfo
)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['imagen_preview', 'marca', 'modelo', 'year', 'km', 'price', 'estado', 'created_at']
    list_filter = ['estado', 'marca', 'year']
    search_fields = ['marca', 'modelo', 'placa']
    list_editable = ['estado']
    readonly_fields = ['imagen_preview_large', 'created_at', 'updated_at']

    fieldsets = (
        ('Información del Vehículo', {
            'fields': ('marca', 'modelo', 'year', 'placa', 'km', 'price', 'estado')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview_large'),
            'description': 'Sube una imagen del vehículo (formatos: JPG, PNG, WebP)'
        }),
        ('Descripción', {
            'fields': ('descripcion',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def imagen_preview(self, obj):
        """Miniatura de imagen en la lista"""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width: 60px; height: 45px; object-fit: cover; border-radius: 4px;" />',
                obj.imagen.url
            )
        return mark_safe('<span style="color: #999; font-size: 12px;">Sin imagen</span>')
    imagen_preview.short_description = 'Imagen'

    def imagen_preview_large(self, obj):
        """Previsualización grande en el formulario de edición"""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.imagen.url
            )
        return mark_safe('<span style="color: #999;">No hay imagen cargada</span>')
    imagen_preview_large.short_description = 'Vista previa'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'service', 'approved', 'created_at']
    list_filter = ['approved', 'rating']
    list_editable = ['approved']
    search_fields = ['name', 'comment']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'is_active', 'order']
    list_filter = ['category', 'is_active']
    list_editable = ['is_active', 'order']
    search_fields = ['title', 'description']


@admin.register(QuotationRequest)
class QuotationRequestAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'servicio', 'telefono', 'estado', 'created_at']
    list_filter = ['estado', 'servicio']
    list_editable = ['estado']
    search_fields = ['nombre', 'email', 'telefono']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'servicio', 'telefono', 'leido', 'created_at']
    list_filter = ['leido', 'servicio']
    list_editable = ['leido']
    search_fields = ['nombre', 'email', 'mensaje']


@admin.register(CreditOption)
class CreditOptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'max_months', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'order']


@admin.register(InsuranceProduct)
class InsuranceProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'tipo', 'is_active', 'order']
    list_filter = ['tipo', 'is_active']
    list_editable = ['is_active', 'order']


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'email']

    def has_add_permission(self, request):
        # Solo permitir una instancia
        if CompanyInfo.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False
