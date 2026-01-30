#!/bin/bash
# Start local server and open widgets for manual testing

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

PORT=8765
echo "Starting local server on port $PORT..."

# Start server in background
uvicorn main:app --port $PORT --host 127.0.0.1 &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server..."
for i in {1..15}; do
    if curl -s http://localhost:$PORT/ > /dev/null; then
        echo "Server ready!"
        break
    fi
    sleep 1
done

echo ""
echo "Test widgets at:"
echo "  Error Decoder: http://localhost:$PORT/error-decoder/widget"
echo "  Pricing:       http://localhost:$PORT/pricing/widget"
echo "  Status:        http://localhost:$PORT/status/widget"
echo ""
echo "Press Ctrl+C to stop server"

# Wait for interrupt
trap "kill $SERVER_PID 2>/dev/null; exit" INT TERM
wait $SERVER_PID
