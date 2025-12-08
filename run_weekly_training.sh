#!/bin/bash
###############################################################################
# Weekly Training Script for Keyword Predictor Model
# 
# This script runs the weekly training pipeline as a backup to Jenkins.
# It can be scheduled via cron to run automatically.
#
# Usage:
#   ./run_weekly_training.sh
#   Or schedule via cron: 0 2 * * 0 /path/to/run_weekly_training.sh
#
# Configuration:
#   Set environment variables in this script or export them before running:
#   - PROJECT_DIR: Root directory of the project (default: script directory)
#   - XML_FOLDER: Path to XML files folder (required)
#   - LOG_DIR: Directory for log files (default: PROJECT_DIR/logs)
#   - NOTIFICATION_EMAIL: Email for notifications (optional)
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration - Modify these as needed
PROJECT_DIR="${PROJECT_DIR:-${SCRIPT_DIR}}"
XML_FOLDER="${XML_FOLDER:-${PROJECT_DIR}/data/xml_files}"
LOG_DIR="${LOG_DIR:-${PROJECT_DIR}/logs}"
VENV_PATH="${VENV_PATH:-${PROJECT_DIR}/venv}"
MODEL_DIR="${MODEL_DIR:-${PROJECT_DIR}/models}"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-}"

# Create directories
mkdir -p "${LOG_DIR}"
mkdir -p "${MODEL_DIR}"

# Generate timestamp for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/training_${TIMESTAMP}.log"
ERROR_LOG="${LOG_DIR}/training_${TIMESTAMP}_error.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# Function to send email notification
send_notification() {
    local subject="$1"
    local body="$2"
    
    if [ -n "${NOTIFICATION_EMAIL}" ] && command -v mail &> /dev/null; then
        echo "${body}" | mail -s "${subject}" "${NOTIFICATION_EMAIL}" 2>/dev/null || true
    fi
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    log "❌ Training pipeline failed with exit code: ${exit_code}"
    log "Check error log: ${ERROR_LOG}"
    
    # Send failure notification
    send_notification "Model Training Failed - ${TIMESTAMP}" \
        "The weekly model training failed at $(date).\n\nCheck logs:\n- ${LOG_FILE}\n- ${ERROR_LOG}"
    
    exit ${exit_code}
}

# Set error trap
trap 'handle_error' ERR

# Start logging
log "=========================================="
log "🚀 Starting Weekly Training Pipeline"
log "=========================================="
log "Project Directory: ${PROJECT_DIR}"
log "XML Folder: ${XML_FOLDER}"
log "Model Directory: ${MODEL_DIR}"
log "Log Directory: ${LOG_DIR}"
log "Timestamp: ${TIMESTAMP}"
log "=========================================="

# Check if XML folder exists
if [ ! -d "${XML_FOLDER}" ]; then
    log "❌ ERROR: XML folder not found: ${XML_FOLDER}"
    log "Please set XML_FOLDER environment variable or create the folder"
    exit 1
fi

# Check if XML folder is not empty
if [ -z "$(ls -A "${XML_FOLDER}" 2>/dev/null)" ]; then
    log "❌ ERROR: XML folder is empty: ${XML_FOLDER}"
    exit 1
fi

# Change to project directory
cd "${PROJECT_DIR}" || {
    log "❌ ERROR: Cannot change to project directory: ${PROJECT_DIR}"
    exit 1
}

# Setup Python virtual environment
log "🔧 Setting up Python virtual environment..."
if [ ! -d "${VENV_PATH}" ]; then
    log "Creating virtual environment at ${VENV_PATH}..."
    python3 -m venv "${VENV_PATH}" || {
        log "❌ ERROR: Failed to create virtual environment"
        exit 1
    }
fi

# Activate virtual environment
source "${VENV_PATH}/bin/activate" || {
    log "❌ ERROR: Failed to activate virtual environment"
    exit 1
}

# Upgrade pip and install dependencies
log "📦 Installing/updating dependencies..."
"${VENV_PATH}/bin/pip" install --upgrade pip wheel --quiet
"${VENV_PATH}/bin/pip" install "setuptools<81.0.0" --quiet
"${VENV_PATH}/bin/pip" install -r requirements.txt --quiet || {
    log "❌ ERROR: Failed to install dependencies"
    exit 1
}

# Set paths for intermediate files
DATASET_OUTPUT="${PROJECT_DIR}/keyword_dataset.json"
CLEANED_DATASET="${PROJECT_DIR}/keyword_dataset_cleaned.json"
TOKENIZER_OUTPUT="${PROJECT_DIR}/tokenizer.json"

# Generate model filename with timestamp
MODEL_VERSION=$(date +%Y%m%d)
MODEL_OUTPUT="${MODEL_DIR}/keyword_predictor_v${MODEL_VERSION}_${TIMESTAMP}.keras"
MODEL_LATEST="${MODEL_DIR}/keyword_predictor_latest.keras"
TOKENIZER_LATEST="${MODEL_DIR}/tokenizer_latest.json"
TOKENIZER_VERSIONED="${MODEL_DIR}/tokenizer_v${MODEL_VERSION}_${TIMESTAMP}.json"

# Step 1: Extract keywords from XML files
log "📊 Step 1: Extracting keywords from XML files..."
"${VENV_PATH}/bin/python" extract_keywords.py \
    --folder "${XML_FOLDER}" \
    --output "${DATASET_OUTPUT}" \
    2>&1 | tee -a "${LOG_FILE}" || {
    log "❌ ERROR: Keyword extraction failed!"
    exit 1
}

# Step 2: Clean dataset
log "🧹 Step 2: Cleaning dataset..."
"${VENV_PATH}/bin/python" clean_keyword_dataset.py \
    --input "${DATASET_OUTPUT}" \
    --output "${CLEANED_DATASET}" \
    2>&1 | tee -a "${LOG_FILE}" || {
    log "❌ ERROR: Dataset cleaning failed!"
    exit 1
}

# Step 3: Inspect dataset (optional, non-blocking)
log "🎯 Step 3: Inspecting dataset..."
"${VENV_PATH}/bin/python" inspect_keyword_dataset.py \
    --file "${CLEANED_DATASET}" \
    2>&1 | tee -a "${LOG_FILE}" || log "⚠️  Dataset inspection had warnings (non-critical)"

# Step 4: Train model
log "🏋️  Step 4: Training model..."
"${VENV_PATH}/bin/python" train_keyword_predictor.py \
    --input "${CLEANED_DATASET}" \
    --model-output "${MODEL_OUTPUT}" \
    --tokenizer-output "${TOKENIZER_OUTPUT}" \
    2>&1 | tee -a "${LOG_FILE}" || {
    log "❌ ERROR: Model training failed!"
    exit 1
}

# Verify model and tokenizer files exist
if [ ! -f "${MODEL_OUTPUT}" ]; then
    log "❌ ERROR: Model file not found after training: ${MODEL_OUTPUT}"
    exit 1
fi

if [ ! -f "${TOKENIZER_OUTPUT}" ]; then
    log "❌ ERROR: Tokenizer file not found after training: ${TOKENIZER_OUTPUT}"
    exit 1
fi

# Step 5: Copy to latest versions
log "📦 Step 5: Copying model and tokenizer to latest versions..."
cp "${MODEL_OUTPUT}" "${MODEL_LATEST}" || {
    log "❌ ERROR: Failed to copy model to latest"
    exit 1
}
cp "${TOKENIZER_OUTPUT}" "${TOKENIZER_LATEST}" || {
    log "❌ ERROR: Failed to copy tokenizer to latest"
    exit 1
}
cp "${TOKENIZER_OUTPUT}" "${TOKENIZER_VERSIONED}" || {
    log "❌ ERROR: Failed to copy tokenizer to versioned file"
    exit 1
}

# Get model file size for logging
MODEL_SIZE=$(du -h "${MODEL_OUTPUT}" | cut -f1)
log "✅ Model saved: ${MODEL_OUTPUT} (${MODEL_SIZE})"
log "✅ Tokenizer saved: ${TOKENIZER_VERSIONED}"

# Optional: Convert to TensorFlow.js format
if command -v tensorflowjs_converter &> /dev/null || "${VENV_PATH}/bin/pip" show tensorflowjs &> /dev/null; then
    log "🔄 Step 6: Converting model to TensorFlow.js format..."
    TFJS_DIR="${PROJECT_DIR}/tfjs_model"
    mkdir -p "${TFJS_DIR}"
    
    "${VENV_PATH}/bin/python" convert_to_tfjs.py \
        --model "${MODEL_LATEST}" \
        --tokenizer "${TOKENIZER_LATEST}" \
        --output-dir "${TFJS_DIR}" \
        2>&1 | tee -a "${LOG_FILE}" || {
        log "⚠️  TensorFlow.js conversion had warnings (non-critical)"
    }
fi

# Success summary
log "=========================================="
log "✅ Weekly Training Pipeline Completed Successfully!"
log "=========================================="
log "Model: ${MODEL_OUTPUT}"
log "Model (latest): ${MODEL_LATEST}"
log "Tokenizer: ${TOKENIZER_VERSIONED}"
log "Tokenizer (latest): ${TOKENIZER_LATEST}"
log "Log file: ${LOG_FILE}"
log "=========================================="

# Send success notification
send_notification "Model Training Completed - ${TIMESTAMP}" \
    "The weekly model training completed successfully at $(date).\n\nModel: ${MODEL_OUTPUT}\nTokenizer: ${TOKENIZER_VERSIONED}\n\nLog: ${LOG_FILE}"

# Cleanup old log files (keep last 10)
log "🧹 Cleaning up old log files (keeping last 10)..."
cd "${LOG_DIR}" && ls -t training_*.log 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

log "✅ All done!"

exit 0

