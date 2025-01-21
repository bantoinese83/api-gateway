#!/bin/bash

# Function to check the status of the last command and print a message
check_status() {
  if [ $? -eq 0 ]; then
    echo "$1 succeeded."
  else
    echo "$1 failed."
    exit 1
  fi
}

# Function to stop all services
stop_services() {
  echo "Stopping API Gateway..."
  pkill -f "uvicorn main:app --host 0.0.0.0 --port 8080"
  echo "Stopping service-b..."
  pkill -f "uvicorn main:app --host 0.0.0.0 --port 8002"
  echo "Stopping service-a..."
  pkill -f "uvicorn main:app --host 0.0.0.0 --port 8001"
  echo "Stopping Jaeger..."
  pkill -f "jaeger-all-in-one"
  echo "Stopping Redis..."
  brew services stop redis
}

# Check if the script is called with the "stop" argument
if [ "$1" == "stop" ]; then
  stop_services
  exit 0
fi

# Start Redis
echo "Starting Redis..."
brew services start redis
check_status "Starting Redis"

# Install Jaeger if not installed
if ! command -v jaeger-all-in-one &> /dev/null; then
  echo "Jaeger not found, downloading..."
  curl -LO https://github.com/jaegertracing/jaeger/releases/download/v1.41.0/jaeger-1.41.0-darwin-amd64.tar.gz
  tar -xzf jaeger-1.41.0-darwin-amd64.tar.gz
  sudo mv jaeger-1.41.0-darwin-amd64/jaeger-all-in-one /usr/local/bin/ || { echo "Failed to move jaeger-all-in-one"; exit 1; }
  sudo chmod +x /usr/local/bin/jaeger-all-in-one || { echo "Failed to set executable permission for jaeger-all-in-one"; exit 1; }
  rm -rf jaeger-1.41.0-darwin-amd64 jaeger-1.41.0-darwin-amd64.tar.gz
  check_status "Downloading and installing Jaeger"
fi

# Start Jaeger
echo "Starting Jaeger..."
jaeger-all-in-one &
sleep 5  # Give Jaeger some time to start
check_status "Starting Jaeger"

# Start service-a
echo "Starting service-a..."
cd service-a || { echo "Failed to change directory to service-a"; exit 1; }
uvicorn main:app --host 0.0.0.0 --port 8001 &
sleep 5  # Give service-a some time to start
cd .. || { echo "Failed to change directory back"; exit 1; }
check_status "Starting service-a"

# Start service-b
echo "Starting service-b..."
cd service-b || { echo "Failed to change directory to service-b"; exit 1; }
uvicorn main:app --host 0.0.0.0 --port 8002 &
sleep 5  # Give service-b some time to start
cd .. || { echo "Failed to change directory back"; exit 1; }
check_status "Starting service-b"

# Start the FastAPI application
echo "Starting API Gateway..."
uvicorn main:app --host 0.0.0.0 --port 8080
check_status "Starting API Gateway"