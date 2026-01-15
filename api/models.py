from django.db import models


class Vehicle(models.Model):
    """Vehículos en inventario para compra/venta"""

    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('vendido', 'Vendido'),
        ('reservado', 'Reservado'),
    ]

    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=100)
    year = models.IntegerField()
    km = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=0)
    placa = models.CharField(max_length=10, unique=True, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    descripcion = models.TextField(null=True, blank=True)
    imagen = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.year})"


class Testimonial(models.Model):
    """Testimonios/reseñas de clientes"""

    name = models.CharField(max_length=100)
    comment = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    service = models.CharField(max_length=100, null=True, blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Testimonio'
        verbose_name_plural = 'Testimonios'

    def __str__(self):
        return f"{self.name} - {self.rating}⭐"


class Service(models.Model):
    """Servicios de autospa ofrecidos"""

    CATEGORY_CHOICES = [
        ('ceramico', 'Cerámico 9H'),
        ('tapiceria', 'Tapicería'),
        ('polarizado', 'Polarizado'),
        ('latoneria', 'Latonería y Pintura'),
        ('mantenimiento', 'Mantenimiento'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    benefits = models.JSONField(default=list)
    price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    duration_days = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    icon = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return self.title


class QuotationRequest(models.Model):
    """Solicitudes de cotización de clientes"""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('contactado', 'Contactado'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]

    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    servicio = models.CharField(max_length=100)
    mensaje = models.TextField()
    vehiculo = models.CharField(max_length=100, null=True, blank=True)
    valor_vehiculo = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de Cotización'
        verbose_name_plural = 'Solicitudes de Cotización'

    def __str__(self):
        return f"{self.nombre} - {self.servicio}"


class ContactMessage(models.Model):
    """Mensajes del formulario de contacto"""

    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    servicio = models.CharField(max_length=100)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensaje de Contacto'
        verbose_name_plural = 'Mensajes de Contacto'

    def __str__(self):
        return f"{self.nombre} - {self.servicio}"


class CreditOption(models.Model):
    """Opciones de financiamiento/crédito"""

    title = models.CharField(max_length=200)
    description = models.TextField()
    benefits = models.JSONField(default=list)
    interest_rate_min = models.FloatField(null=True, blank=True)
    interest_rate_max = models.FloatField(null=True, blank=True)
    max_months = models.IntegerField(default=60)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Opción de Crédito'
        verbose_name_plural = 'Opciones de Crédito'

    def __str__(self):
        return self.title


class InsuranceProduct(models.Model):
    """Productos de seguros"""

    TIPO_CHOICES = [
        ('soat', 'SOAT'),
        ('todo_riesgo', 'Todo Riesgo'),
        ('personalizado', 'Personalizado'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    coverages = models.JSONField(default=list)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Producto de Seguro'
        verbose_name_plural = 'Productos de Seguro'

    def __str__(self):
        return self.title


class CompanyInfo(models.Model):
    """Información de la empresa (singleton)"""

    nombre = models.CharField(max_length=200, default='DLX Automotive Hub')
    direccion = models.CharField(max_length=300)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    horario_lv = models.CharField(max_length=50, verbose_name='Horario L-V')
    horario_sabado = models.CharField(max_length=50)
    horario_domingo = models.CharField(max_length=50, default='Cerrado')
    years_experience = models.IntegerField(default=10)
    descripcion = models.TextField()
    valores = models.JSONField(default=list)
    instagram = models.URLField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    whatsapp = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Información de la Empresa'
        verbose_name_plural = 'Información de la Empresa'

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Singleton: solo puede existir una instancia
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
