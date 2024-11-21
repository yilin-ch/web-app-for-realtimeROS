# web-app-for-realtimeROS
This project provides a web interface for interacting with a real-time ROS (Robot Operating System) using Django and WebSockets. The application allows users to receive and display data from ROS topics and subscribe to ROS logs in real-time.

This repository contains the backend of the project, encapsulated in a Docker container. For the front-end:
https://github.com/yilin-ch/coreui-free-react-admin-template.

## Table of Contents
- [Prerequisites](#prerequisites)

- [Usage](#usage)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)



## Prerequisites
- Docker and Docker Compose (for Docker installation)
- Python 3.8+
- Git

## Usage

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yilin-ch/web-app-for-realtimeROS.git
   cd web-app-for-realtimeROS

2. Modify(or create) .env file in the project root directory with the following content:
    ```sh
    HOST_DATA_PATH=/path/to/your/data 
    ROSBRIDGE_WS_URL=ws://your.ros.ip:port
    ```
    HOST_DATA_PATH: The path to the host directory to be mounted into the container.

    ROSBRIDGE_WS_URL: The WebSocket URL for connecting to the ROS bridge.

    Replace them with your actual paths.

3. Build and start the containers:
    ```sh
    docker-compose up --build

### Running the Application

1. Simply using the following command to run the server:
    ```sh
    docker-compose up 
    ```
    The server will now be running on http://localhost:8000.

2. Make sure you have put the container for ROS under the same network as this web server in Docker. The server will not connect to ROS otherwise.
