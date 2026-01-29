#!/bin/bash
# Test script for verifying a tool works locally
# Usage: ./scripts/test_tool.sh <tool_name>
# Example: ./scripts/test_tool.sh error-decoder

set -e

TOOL_NAME=$1

if [ -z "$TOOL_NAME" ]; then
    echo "Usage: ./scripts/test_tool.sh <tool-name>"
    echo "Example: ./scripts/test_tool.sh error-decoder"
    exit 1
fi

echo "🧪 Testing tool: $TOOL_NAME"
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "❌ Server not running. Start it with: uvicorn main:app --reload"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Test main endpoint (try common patterns)
echo "📡 Testing endpoints..."

# Try POST endpoint
if curl -s -X POST "http://localhost:8000/$TOOL_NAME/decode" \
    -H "Content-Type: application/json" \
    -d '{"error_message": "rate limit exceeded"}' > /dev/null 2>&1; then
    echo "✅ POST /$TOOL_NAME/decode works"
elif curl -s -X POST "http://localhost:8000/$TOOL_NAME/calculate" \
    -H "Content-Type: application/json" \
    -d '{"input_tokens_monthly": 1000000, "output_tokens_monthly": 500000}' > /dev/null 2>&1; then
    echo "✅ POST /$TOOL_NAME/calculate works"
elif curl -s -X GET "http://localhost:8000/$TOOL_NAME/check" > /dev/null 2>&1; then
    echo "✅ GET /$TOOL_NAME/check works"
else
    echo "⚠️  Could not test main endpoint (may need tool-specific test)"
fi

# Test patterns/models/providers endpoint
if curl -s "http://localhost:8000/$TOOL_NAME/patterns" > /dev/null 2>&1; then
    echo "✅ GET /$TOOL_NAME/patterns works"
elif curl -s "http://localhost:8000/$TOOL_NAME/models" > /dev/null 2>&1; then
    echo "✅ GET /$TOOL_NAME/models works"
elif curl -s "http://localhost:8000/$TOOL_NAME/providers" > /dev/null 2>&1; then
    echo "✅ GET /$TOOL_NAME/providers works"
else
    echo "⚠️  Could not test data endpoint (may not exist for this tool)"
fi

# Test widget endpoint
if curl -s "http://localhost:8000/$TOOL_NAME/widget" | grep -q "widget" > /dev/null 2>&1; then
    echo "✅ GET /$TOOL_NAME/widget works"
else
    echo "❌ GET /$TOOL_NAME/widget failed"
fi

# Test subscribe endpoint
if curl -s -X POST "http://localhost:8000/$TOOL_NAME/alerts/subscribe" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' > /dev/null 2>&1; then
    echo "✅ POST /$TOOL_NAME/alerts/subscribe works"
else
    echo "❌ POST /$TOOL_NAME/alerts/subscribe failed"
fi

echo ""
echo "🧪 Running pytest tests..."

# Run pytest for this tool
if python -m pytest "tests/test_${TOOL_NAME//-/_}.py" -v; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed"
    exit 1
fi

echo ""
echo "🎉 Tool $TOOL_NAME is working correctly!"
