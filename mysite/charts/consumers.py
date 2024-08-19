import json
import asyncio
import websockets
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class BridgeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("connecting to rosbridge")
        self.ros_bridge = await websockets.connect('ws://172.20.0.5:9090')
        await self.ros_bridge.send(json.dumps({
            "op": "subscribe",
            "topic": "/sensor_data"
        }))
        await self.accept()
        asyncio.create_task(self.forward_data())

    async def disconnect(self, close_code):
        await self.ros_bridge.close()

    async def forward_data(self):
        logger.debug("forwarding data")
        while True:
            message = await self.ros_bridge.recv()
            logger.debug(f"Received message from ROS: {message}")
            await self.send(text_data=message)


