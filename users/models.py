from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    whatsapp = models.CharField(_('WhatsApp number'), max_length=20, default='+584141234567')
    document_id = models.CharField(_('Document ID'), max_length=20, default='V12345678')
    document_type = models.CharField(
        _('Document type'),
        max_length=10,
        choices=[
            ('CI', 'Cédula'),
            ('PASS', 'Pasaporte'),
        ],
        default='CI'
    )
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.document_type}: {self.document_id})"

    def save(self, *args, **kwargs):
        # Set default values for superuser
        if self.is_superuser and not self.whatsapp:
            self.whatsapp = '+584141234567'
        if self.is_superuser and not self.document_id:
            self.document_id = 'V12345678'
        super().save(*args, **kwargs)
