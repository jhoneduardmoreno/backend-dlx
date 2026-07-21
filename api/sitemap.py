"""Sitemap dinámico servido en /sitemap.xml.

Lista las rutas de marketing estáticas del SPA + una URL por cada vehículo disponible
(`/vehiculo/<id>`), para que las fichas de vehículo — el activo principal del negocio —
sean indexables (long-tail). nginx proxya `/sitemap.xml` a este backend; robots.txt ya
apunta a https://dlx.tatui.store/sitemap.xml.
"""
from xml.sax.saxutils import escape

from django.conf import settings
from django.http import HttpResponse

from .models import Vehicle

# Rutas estáticas del SPA (deben reflejar las rutas de App.tsx) con su changefreq/priority.
STATIC_ROUTES = [
    ("/", "weekly", "1.0"),
    ("/compra-venta-vehiculos", "daily", "0.9"),
    ("/vende-tu-vehiculo", "monthly", "0.9"),
    ("/autospa-integral", "monthly", "0.8"),
    ("/ceramico-9h", "monthly", "0.7"),
    ("/tapiceria-automotriz", "monthly", "0.7"),
    ("/polarizado-nanoceramico", "monthly", "0.7"),
    ("/latoneria-pintura", "monthly", "0.7"),
    ("/creditos-seguros", "monthly", "0.8"),
    ("/sobre-dlx", "monthly", "0.6"),
    ("/contacto", "monthly", "0.8"),
]


def _url_node(loc, changefreq, priority, lastmod=None):
    parts = [f"<loc>{escape(loc)}</loc>"]
    if lastmod:
        parts.append(f"<lastmod>{lastmod}</lastmod>")
    parts.append(f"<changefreq>{changefreq}</changefreq>")
    parts.append(f"<priority>{priority}</priority>")
    return "  <url>" + "".join(parts) + "</url>"


def sitemap_xml(request):
    base = settings.SITE_URL.rstrip("/")
    nodes = [_url_node(f"{base}{path}", cf, pr) for path, cf, pr in STATIC_ROUTES]

    # Sólo vehículos disponibles: los 'vendido'/'reservado' no tienen ficha pública.
    for vehicle in Vehicle.objects.filter(estado="disponible").order_by("id"):
        lastmod = vehicle.updated_at.date().isoformat() if vehicle.updated_at else None
        nodes.append(_url_node(f"{base}/vehiculo/{vehicle.id}", "weekly", "0.8", lastmod))

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(nodes)
        + "\n</urlset>\n"
    )
    return HttpResponse(body, content_type="application/xml; charset=utf-8")
