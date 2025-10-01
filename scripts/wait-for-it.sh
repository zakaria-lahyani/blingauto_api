#!/bin/bash
# =============================================================================
# wait-for-it.sh - Wait for service to be available
# Usage: ./wait-for-it.sh host:port [-t timeout] [-- command args]
# =============================================================================

set -e

TIMEOUT=15
QUIET=0

usage() {
    cat << USAGE >&2
Usage:
    $0 host:port [-t timeout] [-- command args]
    -t TIMEOUT                      Timeout in seconds, zero for no timeout
    -q | --quiet                     Don't output any status messages
    -- COMMAND ARGS                  Execute command with args after the test finishes
USAGE
    exit 1
}

wait_for() {
    if [ $TIMEOUT -gt 0 ]; then
        echo "Waiting $TIMEOUT seconds for $HOST:$PORT"
    else
        echo "Waiting for $HOST:$PORT without a timeout"
    fi

    start_ts=$(date +%s)
    while :
    do
        if [ $ISBUSY -eq 1 ]; then
            nc -z $HOST $PORT
            result=$?
        else
            (echo > /dev/tcp/$HOST/$PORT) >/dev/null 2>&1
            result=$?
        fi

        if [ $result -eq 0 ]; then
            end_ts=$(date +%s)
            echo "$HOST:$PORT is available after $((end_ts - start_ts)) seconds"
            break
        fi

        sleep 1

        if [ $TIMEOUT -gt 0 ]; then
            elapsed=$(($(date +%s) - start_ts))
            if [ $elapsed -ge $TIMEOUT ]; then
                echo "Timeout occurred after waiting $TIMEOUT seconds for $HOST:$PORT"
                exit 1
            fi
        fi
    done
}

# Process arguments
while [ $# -gt 0 ]
do
    case "$1" in
        *:* )
        HOST=$(echo $1 | cut -d: -f1)
        PORT=$(echo $1 | cut -d: -f2)
        shift 1
        ;;
        -q | --quiet)
        QUIET=1
        shift 1
        ;;
        -t)
        TIMEOUT="$2"
        if [ -z "$TIMEOUT" ]; then break; fi
        shift 2
        ;;
        --)
        shift
        break
        ;;
        --help)
        usage
        ;;
        *)
        echo "Unknown argument: $1"
        usage
        ;;
    esac
done

if [ -z "$HOST" ] || [ -z "$PORT" ]; then
    echo "Error: you need to provide a host and port to test."
    usage
fi

ISBUSY=0
if command -v nc > /dev/null 2>&1; then
    ISBUSY=1
fi

wait_for

if [ -n "$@" ]; then
    exec "$@"
fi
