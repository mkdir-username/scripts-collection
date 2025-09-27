#!/bin/bash

# Smart restart script - finds, kills and restarts processes by name

if [ $# -eq 0 ]; then
    echo "Usage: smart-restart <process_name>"
    echo "Example: smart-restart raycast"
    exit 1
fi

PROCESS_NAME="$1"
MODE="${2:-restart}"  # Default mode is restart, can be 'kill' for kill-only

# Find all matching processes (case-insensitive)
PIDS=$(pgrep -i "$PROCESS_NAME" 2>/dev/null)

if [ -z "$PIDS" ]; then
    # If pgrep didn't find anything, try with ps and grep
    PROCESSES=$(ps aux | grep -i "$PROCESS_NAME" | grep -v grep | grep -v "smart-restart" | grep -v "smart-kill")

    if [ -z "$PROCESSES" ]; then
        echo "No processes found matching: $PROCESS_NAME"

        # Try to find the application in common locations (macOS specific)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo ""
            echo "Looking for application to start..."

            # Search in Applications folder
            APP_PATH=""
            for app in "/Applications/"*"$PROCESS_NAME"*.app "/Applications/"*"${PROCESS_NAME^}"*.app "/System/Applications/"*"$PROCESS_NAME"*.app; do
                if [ -d "$app" ]; then
                    APP_PATH="$app"
                    break
                fi
            done

            if [ -n "$APP_PATH" ]; then
                echo "Found application: $APP_PATH"
                read -p "Start this application? (y/n): " -n 1 -r
                echo ""

                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    open "$APP_PATH"
                    echo "Application started"
                fi
            else
                echo "No matching application found in /Applications"
            fi
        fi
        exit 1
    fi

    # Extract PIDs from ps output
    PIDS=$(echo "$PROCESSES" | awk '{print $2}')
fi

# Store process commands for restart
declare -A PROCESS_CMDS
declare -A PROCESS_PATHS

while IFS= read -r pid; do
    # Get full command line for the process
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: Try to get the full command
        FULL_CMD=$(ps -p "$pid" -o command= 2>/dev/null | head -1)

        # For .app bundles, get the actual app path
        APP_PATH=$(ps -p "$pid" -o comm= 2>/dev/null | head -1)
        if [[ "$APP_PATH" == *"/Contents/MacOS/"* ]]; then
            # Extract the .app path
            APP_PATH="${APP_PATH%/Contents/MacOS/*}.app"
            if [ -d "$APP_PATH" ]; then
                PROCESS_PATHS[$pid]="$APP_PATH"
            fi
        fi
    else
        # Linux: Get the full command
        FULL_CMD=$(ps -p "$pid" -o args= 2>/dev/null | head -1)
    fi

    PROCESS_CMDS[$pid]="$FULL_CMD"
done <<< "$PIDS"

# Count number of matching processes
NUM_PIDS=$(echo "$PIDS" | wc -l | tr -d ' ')

# Function to kill a process
kill_process() {
    local pid=$1
    kill "$pid" 2>/dev/null

    # Check if process still exists after normal kill
    sleep 0.5
    if kill -0 "$pid" 2>/dev/null; then
        echo "Process didn't terminate, using kill -9..."
        kill -9 "$pid" 2>/dev/null
    fi

    # Wait a bit more to ensure process is fully terminated
    sleep 0.5
}

# Function to restart a process
restart_process() {
    local pid=$1
    local cmd="${PROCESS_CMDS[$pid]}"
    local app_path="${PROCESS_PATHS[$pid]}"

    echo "Stopping process $pid..."
    kill_process "$pid"

    echo "Restarting..."

    if [ -n "$app_path" ] && [ -d "$app_path" ]; then
        # It's a macOS .app bundle
        open "$app_path"
        echo "Restarted: $app_path"
    elif [ -n "$cmd" ]; then
        # Try to restart using the original command
        # Remove any leading/trailing whitespace
        cmd=$(echo "$cmd" | xargs)

        # Check if it's a full path to an executable
        if [[ "$cmd" == /* ]]; then
            # Extract just the executable and basic args (avoid complex shell constructs)
            EXEC_PATH=$(echo "$cmd" | awk '{print $1}')

            if [ -x "$EXEC_PATH" ]; then
                nohup $cmd > /dev/null 2>&1 &
                echo "Restarted: $cmd"
            else
                echo "Could not restart automatically (executable not found)"
                echo "Original command was: $cmd"
            fi
        else
            # Try to execute as-is
            if command -v "$(echo "$cmd" | awk '{print $1}')" > /dev/null 2>&1; then
                nohup $cmd > /dev/null 2>&1 &
                echo "Restarted: $cmd"
            else
                echo "Could not restart automatically (command not in PATH)"
                echo "Original command was: $cmd"
            fi
        fi
    else
        echo "Could not determine how to restart the process"
    fi
}

if [ "$NUM_PIDS" -eq 1 ]; then
    # Single process found
    PID=$(echo "$PIDS" | head -n1)
    PROCESS_INFO=$(ps -p "$PID" -o pid,comm,args 2>/dev/null | tail -n1)

    echo "Found process:"
    echo "  $PROCESS_INFO"
    echo ""

    if [ "$MODE" == "restart" ]; then
        read -p "Restart this process? (y/n): " -n 1 -r
    else
        read -p "Kill this process? (y/n): " -n 1 -r
    fi
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$MODE" == "restart" ]; then
            restart_process "$PID"
        else
            kill_process "$PID"
            echo "Process $PID killed"
        fi
    else
        echo "Cancelled"
    fi
else
    # Multiple processes found
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
    if [ "$MODE" == "restart" ]; then
        echo "Select processes to RESTART:"
    else
        echo "Select processes to KILL:"
    fi
    echo "  - Enter numbers separated by spaces (e.g., '1 3 5')"
    echo "  - Enter 'a' to process all"
    echo "  - Enter 'q' to quit"
    echo ""
    read -p "Your choice: " CHOICE

    if [ "$CHOICE" = "q" ]; then
        echo "Cancelled"
        exit 0
    elif [ "$CHOICE" = "a" ]; then
        echo ""
        if [ "$MODE" == "restart" ]; then
            read -p "Restart ALL $NUM_PIDS processes? (y/n): " -n 1 -r
        else
            read -p "Kill ALL $NUM_PIDS processes? (y/n): " -n 1 -r
        fi
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for pid in $PIDS; do
                if [ "$MODE" == "restart" ]; then
                    restart_process "$pid"
                else
                    kill_process "$pid"
                    echo "Killed process $pid"
                fi
            done
        else
            echo "Cancelled"
        fi
    else
        # Process selected items
        for num in $CHOICE; do
            if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#PID_ARRAY[@]}" ]; then
                pid=${PID_ARRAY[$num]}
                if [ ! -z "$pid" ]; then
                    if [ "$MODE" == "restart" ]; then
                        restart_process "$pid"
                    else
                        kill_process "$pid"
                        echo "Killed process $pid"
                    fi
                fi
            else
                echo "Invalid selection: $num"
            fi
        done
    fi
fi