#!/bin/bash

# Set vm.overcommit_memory = 1 to allow Redis to run properly
echo "vm.overcommit_memory = 1" > /etc/sysctl.d/99-custom.conf
sysctl -p

# Start Redis server in the background
redis-server --daemonize yes

# Run the configuration script
python /app/generate_config.py

# Start cron service
crond

# Start core Flask app
cd /app/core
nohup python run.py &

# Start marketplace Flask app
cd /app/marketplace
nohup python run.py &

# Start Api Gateway Flask app
cd /app/integration
nohup python run.py &

# Start Api Gateway Flask app
cd /app/gateway
nohup python run.py &

# Keep the container running
tail -f /dev/null
