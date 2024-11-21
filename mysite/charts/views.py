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
from django.conf import settings
import asyncio
import websockets
import os

import time

# Directory path for project folders
PROJECTS_DIRECTORY = '/app/data/Projects'

# MongoDB URI from environment variable
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://myuser:mypassword@mongodb:27017/')

# Define the directory path inside the container
DEFAULT_DIRECTORY = '/app/data/tmp0'

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
        async with websockets.connect(settings.ROSBRIDGE_WS_URL) as websocket:
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
    

# Ensure that the directory exists
if not os.path.exists(PROJECTS_DIRECTORY):
    os.makedirs(PROJECTS_DIRECTORY)

@api_view(['GET'])
def list_projects(request):
    """
    Lists all project directories in the PROJECTS_DIRECTORY.
    """
    try:
        # Get list of all directories in the PROJECTS_DIRECTORY
        projects = [d for d in os.listdir(PROJECTS_DIRECTORY) if os.path.isdir(os.path.join(PROJECTS_DIRECTORY, d))]
        return JsonResponse({"projects": projects}, status=200)
    except Exception as e:
        logger.error("Error listing project directories: %s", str(e))
        return JsonResponse({"error": "Could not retrieve projects."}, status=500)

@api_view(['POST'])
def create_project(request):
    """
    Creates a new project directory in the PROJECTS_DIRECTORY.
    """
    project_name = request.data.get("project_name")

    # Validate the project name
    if not project_name:
        return JsonResponse({"error": "Project name is required."}, status=400)

    project_path = os.path.join(PROJECTS_DIRECTORY, project_name)

    # Check if project directory already exists
    if os.path.exists(project_path):
        return JsonResponse({"error": "Project already exists."}, status=400)

    try:
        # Create a new directory for the project
        os.makedirs(project_path)
        logger.info("Created new project directory: %s", project_path)
        return JsonResponse({"status": "success", "project_name": project_name}, status=201)
    except Exception as e:
        logger.error("Error creating project directory: %s", str(e))
        return JsonResponse({"error": "Could not create project."}, status=500)
    
@api_view(['GET'])
def list_subjects(request, project_name):
    """
    Lists all subjects (folders) within a project.
    """
    project_path = os.path.join(PROJECTS_DIRECTORY, project_name)
    
    if not os.path.exists(project_path):
        return JsonResponse({"error": "Project not found"}, status=404)
    
    subjects = [d for d in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, d))]
    return JsonResponse({"subjects": subjects}, status=200)

@api_view(['POST'])
def create_subject(request, project_name):
    """
    Creates a new subject folder and saves subject info in a JSON file.
    """
    subject_id = request.data.get("subject_id")
    weight = request.data.get("weight")
    height = request.data.get("height")
    
    if not subject_id or not weight or not height:
        return JsonResponse({"error": "Subject ID, weight, and height are required"}, status=400)

    subject_path = os.path.join(PROJECTS_DIRECTORY, project_name, subject_id)
    
    if os.path.exists(subject_path):
        return JsonResponse({"error": "Subject already exists"}, status=400)

    try:
        # Create the subject folder
        os.makedirs(subject_path)
        
        # Save subject info in a JSON file
        subject_info = {
            "subject_id": subject_id,
            "weight": weight,
            "height": height
        }
        json_path = os.path.join(subject_path, "subject_info.json")
        with open(json_path, 'w') as json_file:
            json.dump(subject_info, json_file)
        
        return JsonResponse({"status": "success", "subject_id": subject_id}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@api_view(['GET'])
def list_sessions(request, project_name, subject_id):
    """
    Lists all sessions (folders) within a subject.
    """
    subject_path = os.path.join(PROJECTS_DIRECTORY, project_name, subject_id)
    
    if not os.path.exists(subject_path):
        return JsonResponse({"error": "Subject not found"}, status=404)
    
    sessions = [d for d in os.listdir(subject_path) if os.path.isdir(os.path.join(subject_path, d))]
    return JsonResponse({"sessions": sessions}, status=200)

@api_view(['POST'])
def create_session(request, project_name, subject_id):
    """
    Creates a new session folder within a subject.
    """
    session_name = request.data.get("session_name")

    if not session_name:
        return JsonResponse({"error": "Session name is required"}, status=400)

    session_path = os.path.join(PROJECTS_DIRECTORY, project_name, subject_id, session_name)
    
    if os.path.exists(session_path):
        return JsonResponse({"error": "Session already exists"}, status=400)

    try:
        # Create the session folder
        os.makedirs(session_path)
        return JsonResponse({"status": "success", "session_name": session_name}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@api_view(['GET'])
def list_datafiles(request, project_name, subject_id, session_name):
    """
    Lists all datafiles (folders) within a session.
    """
    session_path = os.path.join(PROJECTS_DIRECTORY, project_name, subject_id, session_name)
    
    if not os.path.exists(session_path):
        return JsonResponse({"error": "Session not found"}, status=404)
    
    datafiles = [d for d in os.listdir(session_path) if os.path.isdir(os.path.join(session_path, d))]
    return JsonResponse({"datafiles": datafiles}, status=200)

@api_view(['POST'])
def create_datafile(request, project_name, subject_id, session_name):
    """
    Creates a new datafile folder within a session.
    """
    datafile_name = request.data.get("datafile_name")
    
    if not datafile_name:
        return JsonResponse({"error": "Datafile name is required"}, status=400)

    datafile_path = os.path.join(PROJECTS_DIRECTORY, project_name, subject_id, session_name, datafile_name)
    
    if os.path.exists(datafile_path):
        return JsonResponse({"error": "Datafile already exists"}, status=400)

    try:
        # Create the datafile folder
        os.makedirs(datafile_path)
        return JsonResponse({"status": "success", "datafile_name": datafile_name}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Function to list filenames in the local directory
@api_view(['GET'])
def get_filenames(request):
    try:
        # Check if the directory exists
        if not os.path.exists(DEFAULT_DIRECTORY):
            return JsonResponse({"error": f"Directory {DEFAULT_DIRECTORY} does not exist"}, status=404)

        # List all filenames in the directory
        filenames = [f for f in os.listdir(DEFAULT_DIRECTORY) if os.path.isfile(os.path.join(DEFAULT_DIRECTORY, f))]
        return JsonResponse(filenames, safe=False)
    except Exception as e:
        logger.error("Error listing filenames: %s", str(e))
        return JsonResponse({"error": str(e)}, status=500)

# Function to fetch data from a specific file
# Modify the get_file_data view to handle GET requests and take filename from the URL
@api_view(['GET', 'POST'])
def get_file_data(request, filename=None):
    if request.method == 'POST':
        # When using POST, retrieve filename from the request data
        filename = request.data.get('filename')

    # If the filename is not provided in either method
    if not filename:
        return JsonResponse({"error": "Filename is required"}, status=400)

    file_path = os.path.join(DEFAULT_DIRECTORY, filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return JsonResponse({"error": "File not found"}, status=404)

    try:
        # Read the file content as a tab-separated values (TSV) file
        data = pd.read_csv(file_path, sep='\t', skiprows=4)

        # Define the columns to extract
        columns_to_extract = [
            'pelvis_tx', 'pelvis_ty', 'pelvis_tz',
            'knee_angle_r', 'knee_angle_l',
            'ankle_angle_r', 'ankle_angle_l'
        ]

        # Check if all the required columns are present
        if not all(col in data.columns for col in columns_to_extract):
            return JsonResponse({'error': 'Some columns are missing in the file'}, status=400)

        # Extract the selected columns
        selected_data = data[columns_to_extract]

        # Convert the first few lines of the result to a string for logging
        result_preview = data.head().to_string()

        # Log the first few lines of the result for debugging
        logger.info("First few lines of the result:\n%s", result_preview)

        # Convert the DataFrame to a dictionary for the response
        result = selected_data.to_dict(orient='list')

        return JsonResponse(result, safe=False)

    except Exception as e:
        logger.error("Error processing file '%s': %s", filename, str(e))
        return JsonResponse({"error": str(e)}, status=500)

""" def get_filenames(request):
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
        return JsonResponse({'error': str(e)}, status=500) """

@api_view(['POST'])
def publish_topic(request):
    logger.info("Received request with data: %s", request.data)
    serializer = TopicSerializer(data=request.data)
    if serializer.is_valid():
        topic = serializer.validated_data['topic']
        message = serializer.validated_data['message']
        branch = serializer.validated_data['branchValue']

        logger.info("Valid data received - Topic: %s, Message: %s, branch: %s", topic, message, branch)

        try:
            # Connect to rosbridge websocket server
            ws = create_connection(settings.ROSBRIDGE_WS_URL)
            logger.info("Connected to rosbridge websocket server")
       
            # Create the ROS message in JSON format
            ros_message = {
                "op": "publish",
                "topic": "/flexbe/command/transition",
                "msg": {
                    "outcome": branch,
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
    
@api_view(['POST'])
def set_name_and_path(request):
    logger.info("Received request to set name and path with data: %s", request.data)

    # Extract filename and filepath from the request data
    filename = request.data.get('filename')
    filepath = request.data.get('filepath')
    relativepath = request.data.get('relativePath')

    # Validate inputs
    if not filename or not filepath:
        return JsonResponse({"error": "Filename and filepath are required"}, status=400)
    
    newpath = os.path.join(PROJECTS_DIRECTORY, str(relativepath))

    try:
        os.makedirs(newpath, exist_ok=True)  # Creates the directory if it doesn't exist
        logger.info("Directory checked/created: %s", newpath)
    except Exception as e:
        logger.error("Failed to create directory: %s", str(e))
        return JsonResponse({"error": "Failed to create directory"}, status=500)

    try:
        # Connect to rosbridge websocket server
        ws = create_connection(settings.ROSBRIDGE_WS_URL)
        logger.info("Connected to rosbridge websocket server")
       
        # Create the ROS service call message in JSON format
        ros_message = {
            "op": "call_service",
            "service": "/ik/set_name_and_path",
            "args": {
                "name": filename,
                "path": filepath
            }
        }
       
        # Send the message to the ROS service
        ws.send(json.dumps(ros_message))
        ws.close()
        logger.info("Sent filename and path to ROS service - Filename: %s, Filepath: %s", filename, filepath)

        return JsonResponse({"status": "success", "filename": filename, "filepath": filepath})

    except Exception as e:
        logger.error("Failed to send message to rosbridge: %s", str(e))
        return JsonResponse({"error": "Failed to connect to rosbridge"}, status=500)
