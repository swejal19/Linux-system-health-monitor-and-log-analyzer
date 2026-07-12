#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"

echo "============================================================"
echo "       LINUX SYSTEM HEALTH MONITOR & LOG ANALYZER"
echo "============================================================"
echo "Project root: ${PROJECT_ROOT}"
echo

if [[ ! -x "${PYTHON_BIN}" ]]; then
    echo "ERROR: Python virtual environment not found at:"
    echo "${PYTHON_BIN}"
    echo
    echo "Create the virtual environment and install dependencies first."
    exit 1
fi

echo "Running system health monitor..."
echo

"${PYTHON_BIN}" "${PROJECT_ROOT}/src/monitor.py"

echo
echo "Running log analyzer..."
echo

"${PYTHON_BIN}" "${PROJECT_ROOT}/src/log_analyzer.py"

echo
echo "============================================================"
echo "All monitoring and log-analysis tasks completed successfully."
echo "============================================================"
