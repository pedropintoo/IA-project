#!/bin/bash

# Kill any existing server instances
pids=$(lsof -ti tcp:8000)
if [[ -n "$pids" ]]; then
    echo "Existing server instances detected. Terminating..."
    kill $pids
    # Wait for the processes to terminate
    sleep 1
fi

total_score=0
total_runs=5

# echo "Starting server..."

# Start the server script with unbuffered output
python3 -u server.py > server_log.txt 2>&1 &
PID_SERVER=$!
# echo "Server started with PID $PID_SERVER"

sleep 1

# Function to kill the server on Ctrl+C
trap "kill $PID_SERVER 2>/dev/null; exit" SIGINT

# echo "Starting agent tests..."

for i in $(seq 1 $total_runs)
do
    echo "Run #$i"

    # Start the agent script
    python3 student.py > /dev/null 2>&1 &
    PID_AGENT=$!
    # echo "Agent started with PID $PID_AGENT"

    # Wait for the agent script to finish if it's still running
    if ps -p $PID_AGENT > /dev/null; then
        wait $PID_AGENT
        # echo "Agent finished"
    fi

    # Wait for the 'Saving' line to appear in the log
    timeout=10    # Maximum time to wait in seconds
    interval=0.5  # Interval between checks
    elapsed=0

    # echo "Waiting for 'Saving' line to appear in the log..."
    while (( $(echo "$elapsed < $timeout" | bc -l) )); do
        if grep --text 'Saving' server_log.txt > /dev/null; then
            # echo "'Saving' line found in the log"
            break
        fi
        sleep $interval
        elapsed=$(echo "$elapsed + $interval" | bc)
    done

    # Extract the last line with 'Saving' from the server log
    last_score_line=$(grep --text 'Saving' server_log.txt | tail -n 1)

    # Check if the line was found
    if [[ -z "$last_score_line" ]]; then
        # echo "Score line not found after waiting."
        continue
    fi

    # Extract the score from the line
    score=$(echo "$last_score_line" | awk -F'[<>]' '{print $2}')

    # Check if score is a valid number
    if [[ $score =~ ^[0-9]+$ ]]; then
        echo "Score: $score"
        # Add the score to total_score
        total_score=$((total_score + score))
    else
        echo "Score not found or invalid."
    fi

    # Clean up the log file for the next run
    > server_log.txt

done

echo -ne "\n"

# Ensure the server is terminated
if ps -p $PID_SERVER > /dev/null; then
    kill $PID_SERVER
    wait $PID_SERVER
    echo "Server terminated"
fi

# Calculate the average score
average_score=$(echo "scale=2; $total_score / $total_runs" | bc)

echo "Average score after $total_runs runs: $average_score"