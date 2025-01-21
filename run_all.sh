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
  pkill -f "uvicorn services.service_b.main:app --host 0.0.0.0 --port 8002"
  echo "Stopping service-a..."
  pkill -f "uvicorn services.service_a.main:app --host 0.0.0.0 --port 8001"
  echo "Stopping Jaeger..."
  pkill -f "jaeger-all-in-one"
  echo "Stopping Redis..."
  brew services stop redis
}

# Function to kill process using a specific port
kill_port() {
  PORT=$1
  PID=$(lsof -t -i:"$PORT")
  if [ -n "$PID" ]; then
    echo "Killing process on port $PORT (PID: $PID)"
    kill -9 "$PID"
  fi
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
  sudo mv jaeger-1.41.0-darwin-amd64/jaeger-all-in-one /usr/local/bin/
  if [ $? -ne 0 ]; then
    echo "Failed to move jaeger-all-in-one"
    exit 1
  fi
  sudo chmod +x /usr/local/bin/jaeger-all-in-one
  if [ $? -ne 0 ]; then
    echo "Failed to set executable permission for jaeger-all-in-one"
    exit 1
  fi
  rm -rf jaeger-1.41.0-darwin-amd64 jaeger-1.41.0-darwin-amd64.tar.gz
  check_status "Downloading and installing Jaeger"
fi

# Kill any running process that might be using the Jaeger port
kill_port 14269

# Check if Jaeger is running and only try to start it if it is not.
if ! pgrep -x "jaeger-all-in-one" > /dev/null
then
    echo "Starting Jaeger..."
    jaeger-all-in-one &
    sleep 5 # Give Jaeger some time to start
    check_status "Starting Jaeger"
else
    echo "Jaeger is already running"
fi

# Kill any process using the ports before starting the services
kill_port 8001
kill_port 8002
kill_port 8080

export PYTHONPATH=$(pwd)

# Start service-a
echo "Starting service-a..."
cd services/service_a
if [ $? -ne 0 ]; then
  echo "Failed to change directory to services/service_a"
  exit 1
fi
uvicorn main:app --host 0.0.0.0 --port 8001 &
sleep 5  # Give service-a some time to start
cd -
if [ $? -ne 0 ]; then
  echo "Failed to change directory back"
  exit 1
fi
check_status "Starting service-a"

# Start service-b
echo "Starting service-b..."
cd services/service_b
if [ $? -ne 0 ]; then
  echo "Failed to change directory to services/service_b"
  exit 1
fi
uvicorn main:app --host 0.0.0.0 --port 8002 &
sleep 5  # Give service-b some time to start
cd -
if [ $? -ne 0 ]; then
  echo "Failed to change directory back"
  exit 1
fi
check_status "Starting service-b"

# Start the FastAPI application
echo "Starting API Gateway..."
uvicorn main:app --host 0.0.0.0 --port 8080
check_status "Starting API Gateway"