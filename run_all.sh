#!/bin/bash

# Set the PATH to include the directory where brew is installed
export PATH="/opt/homebrew/bin:$PATH"

# Function to check the status of the last command and print a message
check_status() {
  if ! eval "$1"; then
    echo "$2 failed."
    exit 1
  else
    echo "$2 succeeded."
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
  echo "Stopping Consul..."
  pkill -f "consul agent -dev -bind=127.0.0.1 -client=127.0.0.1"
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

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
  echo "Homebrew is not installed. Please install Homebrew and try again."
  exit 1
fi

# Start Redis
echo "Starting Redis..."
check_status "brew services start redis" "Starting Redis"

# Install Jaeger if not installed
if ! command -v jaeger-all-in-one &> /dev/null; then
  echo "Jaeger not found, downloading..."
  curl -LO https://github.com/jaegertracing/jaeger/releases/download/v1.41.0/jaeger-1.41.0-darwin-amd64.tar.gz
  tar -xzf jaeger-1.41.0-darwin-amd64.tar.gz
  sudo mv jaeger-1.41.0-darwin-amd64/jaeger-all-in-one /usr/local/bin/
  check_status "sudo chmod +x /usr/local/bin/jaeger-all-in-one" "Setting executable permission for jaeger-all-in-one"
  rm -rf jaeger-1.41.0-darwin-amd64 jaeger-1.41.0-darwin-amd64.tar.gz
  check_status "true" "Downloading and installing Jaeger"
fi

# Kill any running process that might be using the Jaeger port
kill_port 14269

# Check if Jaeger is running and only try to start it if it is not.
if ! pgrep -x "jaeger-all-in-one" > /dev/null; then
  echo "Starting Jaeger..."
  jaeger-all-in-one &
  sleep 5 # Give Jaeger some time to start
  check_status "true" "Starting Jaeger"
else
  echo "Jaeger is already running"
fi

# Install Consul if not installed
if ! command -v consul &> /dev/null; then
  echo "Consul not found, downloading..."
  curl -LO https://releases.hashicorp.com/consul/1.14.0/consul_1.14.0_darwin_amd64.zip
  unzip consul_1.14.0_darwin_amd64.zip
  sudo mv consul /usr/local/bin/
  check_status "sudo chmod +x /usr/local/bin/consul" "Setting executable permission for consul"
  rm -f consul_1.14.0_darwin_amd64.zip
  check_status "true" "Downloading and installing Consul"
fi

# Kill any process using the ports before starting the services
kill_port 8001
kill_port 8002
kill_port 8080
kill_port 8500

# Declare a variable to hold the current working directory
current_dir=$(pwd)

# Assign the value of the variable to the PYTHONPATH environment variable
export PYTHONPATH=$current_dir

# Start Consul
echo "Starting Consul..."
consul agent -dev -bind=127.0.0.1 -client=127.0.0.1 &
sleep 5  # Give Consul some time to start
check_status "true" "Starting Consul"

# Start service-a
echo "Starting service-a..."
cd services/service_a || exit
uvicorn main:app --host 0.0.0.0 --port 8001 &
sleep 5  # Give service-a some time to start
cd - || exit
check_status "true" "Starting service-a"

# Start service-b
echo "Starting service-b..."
cd services/service_b || exit
uvicorn main:app --host 0.0.0.0 --port 8002 &
sleep 5  # Give service-b some time to start
cd - || exit
check_status "true" "Starting service-b"

# Start the FastAPI application
echo "Starting API Gateway..."
uvicorn main:app --host 0.0.0.0 --port 8080
check_status "true" "Starting API Gateway"