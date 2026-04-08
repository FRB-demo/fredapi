#!/usr/bin/env bash
# Smoke test runner
# Waits for services to be ready, then runs smoke tests.

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
MAX_RETRIES=30
RETRY_INTERVAL=2

echo "=== AI Research Assistant Smoke Tests ==="

# Wait for backend to be ready
echo "Waiting for backend at ${BACKEND_URL}..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "${BACKEND_URL}/health" > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "ERROR: Backend did not become ready after $((MAX_RETRIES * RETRY_INTERVAL)) seconds"
        exit 1
    fi
    echo "  Attempt $i/$MAX_RETRIES - retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
done

# Run smoke tests
echo ""
echo "Running smoke tests..."
pytest tests/smoke/ -v -x --tb=short -m smoke

echo ""
echo "=== Smoke tests complete ==="
