#!/bin/bash

# Define variables
IMAGE_NAME="personal-finance"
CONTAINER_NAME="personal-finance"
PORT="5050"

# Check if the container is running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping running container $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME
fi

# Check if the container exists (even if not running)
if [ "$(docker ps -a -q -f name=$CONTAINER_NAME)" ]; then
    echo "Removing container $CONTAINER_NAME..."
    docker rm $CONTAINER_NAME
fi

# Check if the image exists
if [ "$(docker images -q $IMAGE_NAME)" ]; then
    echo "Removing image $IMAGE_NAME..."
    docker rmi $IMAGE_NAME
fi

# Prepare the classes-temp directory
echo "Preparing classes-temp directory..."
rm -rf classes-temp # Remove any existing temp directory
mkdir -p classes-temp
cp -f ../gcloud-classes/*.py classes-temp/

# Build the Docker image
echo "Building the Docker image..."
docker build -t $IMAGE_NAME .

# Check if the build succeeded
if [ $? -ne 0 ]; then
    echo "Error: Docker image build failed!"
    exit 1
fi

# Run the container
echo "Running the Docker container..."
docker run -d \
    --name $CONTAINER_NAME \
    -v /Users/michasmi/.config/use-toolsexplorationfirebase-a1c9659f6fe2.json:/app/key.json \
    --env-file ./env_vars.env \
    -e GOOGLE_APPLICATION_CREDENTIALS="/app/key.json" \
    -e REDIRECT_URI="http://localhost:${PORT}/" \
    --restart always \
    -p "${PORT}:${PORT}" \
    $IMAGE_NAME

-p 8080:8080 \
    your-image-name

# Check if the container started successfully
if [ $? -eq 0 ]; then
    echo "Container '$CONTAINER_NAME' is running."
    # Cleanup the temp directory
    rm -rf classes-temp
else
    echo "Error: Failed to start the container!"
    exit 1
fi
