import os
from django.conf import settings

def branding(request):
    return {
        'restaurant_name': settings.RESTAURANT_NAME,
        'restaurant_whatsapp': os.environ.get('RESTAURANT_WHATSAPP', '').strip(),
    }
