import logging
import pandas as pd
import json
from django.http import JsonResponse
from pymongo import MongoClient
from rest_framework.decorators import api_view
from rest_framework.response import Response
from websocket import create_connection
from .serializers import TopicSerializer
from io import StringIO

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import asyncio
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test redis connection
def test_redis_connection(request):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)("test_channel", {"type": "test.message", "text": "Hello, world!"})
    message = async_to_sync(channel_layer.receive)("test_channel")
    return JsonResponse({"message": message})

# Test ros-bridge connection
async def test_ros_bridge_publish(request):
    try:
        async with websockets.connect('ws://172.18.0.4:9090') as websocket:
            await websocket.send(json.dumps({
                "op": "publish",
                "topic": "/test_topic",
                "msg": {
                    "data": "test_message"
                }
            }))
            response = await websocket.recv()
            return JsonResponse({"status": "success", "message": response})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def get_filenames(request):
    MONGO_URI = "mongodb://myuser:mypassword@localhost:27017/"
    DATABASE_NAME = "mydatabase"
    COLLECTION_NAME = "historydata"

    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    filenames = collection.find({}, {"filename": 1, "_id": 0})

    filenames_list = [file["filename"] for file in filenames]

    client.close()

    return JsonResponse(filenames_list, safe=False)

def get_file_data(request, filename):
    try:
        MONGO_URI = "mongodb://myuser:mypassword@localhost:27017/"
        DATABASE_NAME = "mydatabase"
        COLLECTION_NAME = "historydata"

        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        document = collection.find_one({"filename": filename}, {"file_data": 1, "_id": 0})

        if document is None:
            return JsonResponse({'error': 'File not found in database'}, status=404)

        file_data = document["file_data"]
        file_content = file_data.decode('utf-8')  # Decode bytes to string

        data = pd.read_csv(StringIO(file_content), sep='\t', skiprows=4)

        columns_to_extract = ['pelvis_tx', 'pelvis_ty', 'pelvis_tz', 'knee_angle_r', 'knee_angle_l', 'ankle_angle_r', 'ankle_angle_l']
        
        if not all(col in data.columns for col in columns_to_extract):
            return JsonResponse({'error': 'Some columns are missing in the file'}, status=400)

        selected_data = data[columns_to_extract]
        result = selected_data.to_dict(orient='list')

        return JsonResponse(result, safe=False)

    except Exception as e:
        logger.error("Error fetching file data: %s", str(e))
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def publish_topic(request):
    logger.info("Received request with data: %s", request.data)
    serializer = TopicSerializer(data=request.data)
    if serializer.is_valid():
        topic = serializer.validated_data['topic']
        message = serializer.validated_data['message']

        logger.info("Valid data received - Topic: %s, Message: %s", topic, message)

        try:
            # Connect to rosbridge websocket server
            ws = create_connection("ws://localhost:9090/")
            logger.info("Connected to rosbridge websocket server")
       
            # Create the ROS message in JSON format
            ros_message = {
                "op": "publish",
                "topic": "/flexbe/command/transition",
                "msg": {
                    "outcome": 0,
                    "target": message
                }
            }
            
       
            # Send the message
            ws.send(json.dumps(ros_message))
            ws.close()
            logger.info("Message sent to rosbridge - Topic: %s, Message: %s", topic, message)
            return Response({"status": "success", "topic": topic, "message": message})

        except Exception as e:
            logger.error("Failed to send message to rosbridge: %s", str(e))
            return Response({"status": "error", "message": "Failed to connect to rosbridge"}, status=500)

    else:
        logger.error("Invalid data received: %s", serializer.errors)
        return Response(serializer.errors, status=400)



