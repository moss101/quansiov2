#!/usr/bin/env bash
# Launch the full Quansio V9 local deployment: qualification environment,
# migrations, model provider and all twelve canonical services, with health
# verification. `launch.sh stop` tears everything down.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-python3}"
VPY=".venv/bin/python"
LOGDIR="${LOGDIR:-/tmp/quansio-services}"
export PYTHONPATH="$PWD:$PWD/generated/contracts/python${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$LOGDIR"

SERVICES=(
  "quansio-api:8080:services/quansio_api/main.py"
  "quansio-control:8081:services/quansio_control/main.py"
  "quansio-model-gateway:8082:services/quansio_model_gateway/main.py"
  "quansio-context:8083:services/quansio_context/main.py"
  "quansio-indexer:8084:services/quansio_indexer/main.py"
  "qworkerd:8085:services/qworkerd/main.py"
  "quansio-worker-gateway:8086:services/quansio_worker_gateway/main.py"
  "quansio-runtime:8087:services/quansio_runtime/main.py"
  "quansio-artifact:8088:services/quansio_artifact/main.py"
  "quansio-notify:8089:services/quansio_notify/main.py"
  "quansio-machine-control:8090:services/quansio_machine_control/main.py"
  "quansio-integration-broker:8091:services/quansio_integration_broker/main.py"
)
RUN_MOUNT="${RUN_MOUNT:-/tmp/quansio-qworkerd}"
export QUANSIO_GUEST_SANDBOX_ROOT="${QUANSIO_GUEST_SANDBOX_ROOT:-$RUN_MOUNT}"
export QUANSIO_MACHINE_STATE_ROOT="${QUANSIO_MACHINE_STATE_ROOT:-$RUN_MOUNT/machine-state}"
LLAMA_PORT=54340

wait_http() {
  local url="$1" name="$2" deadline=$((SECONDS + 60))
  while (( SECONDS < deadline )); do
    if curl -sf -o /dev/null --max-time 2 "$url"; then return 0; fi
    sleep 1
  done
  echo "LAUNCH: $name did not become healthy ($url)" >&2
  return 1
}

resolve_model() {
  # The enabled model profile needs a local GGUF. Resolve it from the
  # environment or discover it under $QUANSIO_MODEL_DIR; nothing here may
  # hard-code a machine-specific path.
  if [ -n "${QUANSIO_MODEL_GGUF:-}" ] && [ -f "${QUANSIO_MODEL_GGUF}" ]; then
    printf '%s' "$QUANSIO_MODEL_GGUF"
    return 0
  fi
  local dir="${QUANSIO_MODEL_DIR:-models}"
  local found
  found="$(find "$dir" -maxdepth 2 -name '*.gguf' 2>/dev/null | head -1 || true)"
  [ -n "$found" ] && printf '%s' "$found"
}

start_infra() {
  "$VPY" tools/environment/qualenv.py provision | tail -1
  "$VPY" -m quansio.platform.migrate up | tail -1
  # Real model provider (llama.cpp) for the enabled profile.
  if ! curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${LLAMA_PORT}/health"; then
    MODEL_GGUF="$(resolve_model)"
    if [ -x /opt/homebrew/bin/llama-server ] && [ -n "$MODEL_GGUF" ]; then
      nohup /opt/homebrew/bin/llama-server -m "$MODEL_GGUF" \
        --host 127.0.0.1 --port "$LLAMA_PORT" --alias quansio-local-lfm \
        > "$LOGDIR/llama-server.log" 2>&1 &
      echo $! > "$LOGDIR/llama-server.pid"
      wait_http "http://127.0.0.1:${LLAMA_PORT}/health" "llama-server" || true
      echo "LAUNCH: llama-server (real provider) started on :$LLAMA_PORT"
    else
      echo "LAUNCH: no local model provider configured (set QUANSIO_MODEL_GGUF or QUANSIO_MODEL_DIR with a .gguf inside); continuing without :$LLAMA_PORT"
    fi
  else
    echo "LAUNCH: llama-server already healthy on :$LLAMA_PORT"
  fi
  export QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL="http://127.0.0.1:${LLAMA_PORT}"
}

start_services() {
  mkdir -p "$RUN_MOUNT"
  for entry in "${SERVICES[@]}"; do
    IFS=':' read -r name port module <<< "$entry"
    if curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${port}/healthz"; then
      echo "LAUNCH: $name already healthy on :$port"
      continue
    fi
    svc_dir="${module#*/}"; svc_dir="${svc_dir%%/*}"
    nohup "$VPY" -m uvicorn "main:app" --app-dir "services/$svc_dir" \
      --host 127.0.0.1 --port "$port" \
      --log-level warning > "$LOGDIR/$name.log" 2>&1 &
    echo $! > "$LOGDIR/$name.pid"
  done
  for entry in "${SERVICES[@]}"; do
    IFS=':' read -r name port module <<< "$entry"
    wait_http "http://127.0.0.1:${port}/healthz" "$name"
    echo "LAUNCH: $name healthy on :$port"
  done
}

verify() {
  local failed=0
  for entry in "${SERVICES[@]}"; do
    IFS=':' read -r name port module <<< "$entry"
    if curl -sf --max-time 3 "http://127.0.0.1:${port}/healthz" | grep -q live; then
      echo "OK   $name :$port"
    else
      echo "FAIL $name :$port"; failed=1
    fi
  done
  return $failed
}

case "${1:-start}" in
  start)
    start_infra
    start_services
    verify
    echo "LAUNCH COMPLETE: Quansio V9 running — API :8080, control :8081, model-gateway :8082,"
    echo "context :8083, indexer :8084, qworkerd :8085, worker-gateway :8086, runtime :8087,"
    echo "artifact :8088, notify :8089, machine-control :8090, integration-broker :8091;"
    echo "Postgres/Redis/MinIO via compose; real model provider llama.cpp :$LLAMA_PORT. Logs in $LOGDIR."
    ;;
  stop)
    for entry in "${SERVICES[@]}"; do
      IFS=':' read -r name port module <<< "$entry"
      pidfile="$LOGDIR/$name.pid"
      if [ -f "$pidfile" ]; then
        kill "$(cat "$pidfile")" 2>/dev/null || true
        rm -f "$pidfile"
      fi
    done
    if [ -f "$LOGDIR/llama-server.pid" ]; then
      kill "$(cat "$LOGDIR/llama-server.pid")" 2>/dev/null || true
      rm -f "$LOGDIR/llama-server.pid"
    fi
    "$VPY" tools/environment/qualenv.py teardown | tail -1
    echo "STOPPED"
    ;;
  status)
    verify
    ;;
  *)
    echo "usage: launch.sh [start|stop|status]"
    exit 2
    ;;
esac
