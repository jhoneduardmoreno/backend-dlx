from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from api.sitemap import sitemap_xml

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # Sitemap dinámico (rutas estáticas + /vehiculo/<id>). nginx proxya /sitemap.xml aquí.
    path('sitemap.xml', sitemap_xml, name='sitemap'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
