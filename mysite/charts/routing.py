from django.urls import path
from .consumers import BridgeConsumer, LogConsumer

websocket_urlpatterns = [
    path('ws/bridge/', BridgeConsumer.as_asgi()),
    path('ws/flexbelogs/', LogConsumer.as_asgi())
]
