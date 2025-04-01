import asyncio
import threading
import sys
import signal
import os
from django.conf import settings
from app.websocket_server import start_server

def run_websocket_server(stop_event):
    """Run the WebSocket server in the event loop."""
    try:
        # Ensure Django settings are configured
        if not settings.configured:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fipo.settings')
            import django
            django.setup()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def stop_server():
            loop.stop()
            loop.close()

        try:
            server_task = loop.create_task(start_server())
            while not stop_event.is_set():
                loop.run_until_complete(asyncio.sleep(1))
            stop_server()
        except Exception as e:
            print(f"WebSocket server error: {e}")
            stop_server()
    except Exception as e:
        print(f"Error starting WebSocket server: {e}")

def start_websocket_server():
    """Start the WebSocket server in a separate thread with proper signal handling."""
    stop_event = threading.Event()
    websocket_thread = threading.Thread(target=run_websocket_server, args=(stop_event,), daemon=True)
    websocket_thread.start()
    return stop_event, websocket_thread

def setup_signal_handlers(stop_event, websocket_thread):
    """Setup signal handlers in the main thread for graceful shutdown."""
    def signal_handler(signum, frame):
        print("\nShutting down WebSocket server...")
        stop_event.set()
        websocket_thread.join(timeout=5)
        sys.exit(0)

    # Setup signal handlers in the main thread
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def setup_signal_handlers(thread):
    """This function is now deprecated as signal handling is managed in start_websocket_server"""
    pass