from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleViewSet, TestimonialViewSet, ServiceViewSet,
    QuotationRequestViewSet, ContactMessageViewSet,
    CreditOptionViewSet, InsuranceProductViewSet, CompanyInfoViewSet
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'quotations', QuotationRequestViewSet, basename='quotation')
router.register(r'contact-messages', ContactMessageViewSet, basename='contact-message')
router.register(r'credit-options', CreditOptionViewSet, basename='credit-option')
router.register(r'insurance-products', InsuranceProductViewSet, basename='insurance-product')
router.register(r'company-info', CompanyInfoViewSet, basename='company-info')

urlpatterns = [
    path('', include(router.urls)),
]
