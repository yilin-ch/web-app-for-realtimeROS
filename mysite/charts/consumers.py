import json
import asyncio
import websockets
import logging
from datetime import datetime, timezone

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class BridgeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("connecting to rosbridge")
        self.ros_bridge = await websockets.connect('ws://172.18.0.5:9090')
        await self.ros_bridge.send(json.dumps({
            "op": "subscribe",
            "topic": "/ik/output"
        }))
        await self.accept()
        asyncio.create_task(self.forward_data())

    async def disconnect(self, close_code):
        await self.ros_bridge.close()

    def rad_to_deg(self, rad):
        return rad * (180 / 3.14159265)
    
    #  convert radians to degrees
    def convert_data(self, data):
        return [
            self.rad_to_deg(val) if idx not in [3, 4, 5] else val
            for idx, val in enumerate(data)
        ]
    
    def convert_timestamp(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime('%H:%M:%S')

    async def forward_data(self):
        logger.debug("forwarding data")
        while True:
            message = await self.ros_bridge.recv()
            logger.debug(f"Received message from ROS: {message}")
            data = json.loads(message)
            if 'msg' in data:
                if 'data' in data['msg']:
                    # Convert the data
                    converted_data = self.convert_data(data['msg']['data'])
                    data['msg']['data'] = converted_data
                if 'time' in data['msg']:
                    # Convert the timestamp
                    converted_time = self.convert_timestamp(data['msg']['time'])
                    data['msg']['time'] = converted_time

            await self.send(text_data=json.dumps(data))


