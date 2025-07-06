#!/usr/bin/env bash
set -euo pipefail

# Forward termination signals to child processes
trap 'kill -TERM "$PID" 2>/dev/null' TERM INT

SPEC="$1"   # e.g. /spec/openapi.yaml
OUT="$2"    # e.g. /app

# 1) Generate the app
printf "[GEN] Generating app from %s → %s\n" "$SPEC" "$OUT"
mkdir -p "$OUT"
python /kineto/generator.py "$SPEC" -o "$OUT"

# Change to output directory
cd "$OUT"

# Start server in background
printf "[RUN] Starting server\n"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
PID=$!
# Ensure PID forwarding
trap 'kill -TERM "$PID" 2>/dev/null' TERM INT
sleep 3

# Loop: run tests, refine on failure
MAX_ITERS=2
for (( ITER=1; ITER<=MAX_ITERS; ITER++ )); do
  printf "[TEST] Iteration %d – running tests\n" "$ITER"

  # Disable exit-on-error so that a failing pytest doesn't stop the script
  set +e
  pytest tests/test_api.py -v 2>&1 | tee test_results.log
  TEST_RC=${PIPESTATUS[0]}
  set -e
  printf "[TEST] pytest exit code: %d\n" "$TEST_RC"

  if [[ "$TEST_RC" -eq 0 ]]; then
    printf "[TEST] ✅ All tests passed on iteration %d\n" "$ITER"
    break
  fi

  if [[ "$ITER" -lt "$MAX_ITERS" ]]; then
    printf "[TEST] ❌ Tests failed (iteration %d), invoking refiner\n" "$ITER"
    printf "[REFINER] Starting refinement run %d\n" "$ITER"
    python /kineto/refiner.py "$SPEC" "$OUT" test_results.log
    printf "[REFINER] Completed refinement run %d\n" "$ITER"
    printf "[REFINER] Refinement complete; retrying tests\n"
  else
    printf "[TEST] ❌ Tests still failing after %d iterations\n" "$MAX_ITERS"
    exit 1
  fi
done

# Final serve: replace this shell with Uvicorn
printf "[RUN] Launching final server\n"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
