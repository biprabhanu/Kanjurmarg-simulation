#!/usr/bin/env bash
# Compiles the FobEngine (the exact code embedded in the AnyLogic model) inside a small
# runner class and executes all experiments. Output goes to build/raw/.
#   usage: scripts/run_engine.sh [replications] [durationMin] [warmupMin] [walkSpeed] [baseSeed]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
mkdir -p "$BUILD/java" "$BUILD/raw"

{
  echo "public class EngineRunner {"
  cat "$ROOT/engine/FobEngine.java"
  cat "$ROOT/engine/RunnerMain.java"
  echo "}"
} > "$BUILD/java/EngineRunner.java"

javac -d "$BUILD/java" "$BUILD/java/EngineRunner.java"
java -cp "$BUILD/java" EngineRunner "$BUILD/raw" "${1:-30}" "${2:-60}" "${3:-0}" "${4:-1.30}" "${5:-1001}"
