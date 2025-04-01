"""
WSGI config for fipo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fipo.settings')

application = get_wsgi_application()
app = application

# Initialize WebSocket server after Django is fully loaded
try:
    from app.server_startup import start_websocket_server, setup_signal_handlers
    stop_event, websocket_thread = start_websocket_server()
    setup_signal_handlers(stop_event, websocket_thread)
except Exception as e:
    print(f"Error initializing WebSocket server: {e}")
