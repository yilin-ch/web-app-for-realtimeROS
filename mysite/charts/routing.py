from django.urls import path
from .consumers import BridgeConsumer

websocket_urlpatterns = [
    path('ws/bridge/', BridgeConsumer.as_asgi()),
]
