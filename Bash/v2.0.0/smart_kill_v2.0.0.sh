#!/bin/bash

# Smart kill script - finds and kills processes by name

if [ $# -eq 0 ]; then
    echo "Usage: smart-kill <process_name>"
    echo "Example: smart-kill raycast"
    exit 1
fi

PROCESS_NAME="$1"

# Find all matching processes (case-insensitive)
PIDS=$(pgrep -i "$PROCESS_NAME" 2>/dev/null)

if [ -z "$PIDS" ]; then
    # If pgrep didn't find anything, try with ps and grep
    PROCESSES=$(ps aux | grep -i "$PROCESS_NAME" | grep -v grep | grep -v "smart-kill")

    if [ -z "$PROCESSES" ]; then
        echo "No processes found matching: $PROCESS_NAME"
        exit 1
    fi

    # Extract PIDs from ps output
    PIDS=$(echo "$PROCESSES" | awk '{print $2}')
fi

# Count number of matching processes
NUM_PIDS=$(echo "$PIDS" | wc -l | tr -d ' ')

if [ "$NUM_PIDS" -eq 1 ]; then
    # Single process found - kill it
    PID=$(echo "$PIDS" | head -n1)
    PROCESS_INFO=$(ps -p "$PID" -o pid,comm,args 2>/dev/null | tail -n1)

    echo "Found process:"
    echo "  $PROCESS_INFO"
    echo ""
    read -p "Kill this process? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill "$PID" 2>/dev/null

        # Check if process still exists after normal kill
        sleep 0.5
        if kill -0 "$PID" 2>/dev/null; then
            echo "Process didn't terminate, using kill -9..."
            kill -9 "$PID" 2>/dev/null
        fi

        echo "Process $PID killed"
    else
        echo "Cancelled"
    fi
else
    # Multiple processes found - show list and ask user to select
    echo "Found $NUM_PIDS processes matching '$PROCESS_NAME':"
    echo ""

    # Create array to store PIDs
    declare -a PID_ARRAY
    i=1

    while IFS= read -r pid; do
        PID_ARRAY[$i]=$pid
        PROCESS_INFO=$(ps -p "$pid" -o pid,comm,%cpu,%mem,args 2>/dev/null | tail -n1)
        printf "%2d) %s\n" $i "$PROCESS_INFO"
        ((i++))
    done <<< "$PIDS"

    echo ""
    echo "Select processes to kill:"
    echo "  - Enter numbers separated by spaces (e.g., '1 3 5')"
    echo "  - Enter 'a' to kill all processes"
    echo "  - Enter 'q' to quit"
    echo ""
    read -p "Your choice: " CHOICE

    if [ "$CHOICE" = "q" ]; then
        echo "Cancelled"
        exit 0
    elif [ "$CHOICE" = "a" ]; then
        echo ""
        read -p "Kill ALL $NUM_PIDS processes? (y/n): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for pid in $PIDS; do
                kill "$pid" 2>/dev/null
                echo "Killed process $pid"
            done

            # Force kill any remaining
            sleep 0.5
            for pid in $PIDS; do
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null
                    echo "Force killed process $pid"
                fi
            done
        else
            echo "Cancelled"
        fi
    else
        # Kill selected processes
        for num in $CHOICE; do
            if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#PID_ARRAY[@]}" ]; then
                pid=${PID_ARRAY[$num]}
                if [ ! -z "$pid" ]; then
                    kill "$pid" 2>/dev/null
                    echo "Killed process $pid"

                    # Force kill if needed
                    sleep 0.5
                    if kill -0 "$pid" 2>/dev/null; then
                        kill -9 "$pid" 2>/dev/null
                        echo "Force killed process $pid"
                    fi
                fi
            else
                echo "Invalid selection: $num"
            fi
        done
    fi
fi