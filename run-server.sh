#!/bin/bash

# Start the first script and capture its process ID
python3 server.py &
PID_SCRIPT1=$!

# Start the second script in the background and suppress its output
python3 viewer.py > /dev/null 2>&1 &
PID_SCRIPT2=$!

# Function to kill both scripts on Ctrl+C
trap "kill $PID_SCRIPT1 $PID_SCRIPT2" SIGINT

# Wait for the first script to finish
wait $PID_SCRIPT1
wait $PID_SCRIPT2