#!/bin/bash

# Kill any existing server instances
pids=$(lsof -ti tcp:8000)
if [[ -n "$pids" ]]; then
    echo "Existing server instances detected. Terminating..."
    kill $pids
    sleep 1
fi

total_score=0
total_runs=5
log_file="server_log.txt"

# Start the server with unbuffered output
python3 -u server.py > "$log_file" 2>&1 &
PID_SERVER=$!
# echo "Server started with PID $PID_SERVER"
sleep 1

# Ensure the server is terminated on Ctrl+C
trap "kill $PID_SERVER 2>/dev/null; exit" SIGINT

# Function to extract score and steps from the log
extract_metrics() {
    local log_file=$1

    # Extract the last 'Saving' line and score
    score=$(grep --text 'Saving' "$log_file" | tail -n 1 | sed -n 's/.*<\([0-9]*\)>.*/\1/p')
    
    # Extract steps from the last [xxxx] occurrence
    steps=$(grep --text -o '\[[0-9]*\]' "$log_file" | tail -n 1 | awk -F'[][]' '{print $2}')

    echo "$score" "$steps"
}

# Run the agent and capture metrics
for i in $(seq 1 "$total_runs"); do
    echo "Run #$i"

    NAME="lwe >> rsa" python3 student.py > /dev/null 2>&1 &
    PID_AGENT=$!
    # echo "Agent started with PID $PID_AGENT"

    # Wait for agent completion
    if ps -p $PID_AGENT > /dev/null; then
        wait $PID_AGENT
    fi

    # Wait for 'Saving' in the log with a timeout
    timeout=10
    interval=20
    elapsed=0

    while (( $(echo "$elapsed < $timeout" | bc -l) )); do
        if grep --text 'Saving' "$log_file" > /dev/null; then
            sleep 1
            break
        fi
        sleep "$interval"
        elapsed=$(echo "$elapsed + $interval" | bc)
    done

    # Extract metrics
    read -r score steps <<< "$(extract_metrics "$log_file")"

    # Handle score
    if [[ $score =~ ^[0-9]+$ ]]; then
        echo "Score: $score"
        total_score=$((total_score + score))
    else
        echo "Score not found or invalid."
    fi

    # Handle steps
    if [[ -n "$steps" ]]; then
        echo "Steps: $steps"
    else
        echo "No steps found."
    fi

    # Clear the log file
    : > "$log_file"
done

# Ensure the server is terminated
if ps -p $PID_SERVER > /dev/null; then
    kill $PID_SERVER
    wait $PID_SERVER
    echo "Server terminated"
fi

# Calculate and display the average score
if [[ $total_runs -gt 0 ]]; then
    average_score=$(echo "scale=2; $total_score / $total_runs" | bc)
    echo "Average score after $total_runs runs: $average_score"
else
    echo "No runs completed."
fi
