properties([
    parameters([
        booleanParam(name: 'RUN_TRAINING', defaultValue: false, description: 'Run model training pipeline'),
        booleanParam(name: 'DEPLOY_MODEL', defaultValue: false, description: 'Deploy model to production'),
        booleanParam(name: 'FRESH_TRAINING', defaultValue: false, description: 'Train on new data only (ignore old data). Default: false (merge with old data)'),
        stringParam(name: 'XML_FOLDER_PATH', defaultValue: '', description: 'Path to XML files folder (e.g., /path/to/xml_files or relative to workspace)')
    ]),
    // Schedule weekly training: Every Sunday at 2 AM (random minute to avoid load spikes)
    pipelineTriggers([
        cron('H 2 * * 0')  // H = hash (random minute), 2 = hour, * = any day, * = any month, 0 = Sunday
    ])
])

node {
    // Environment variables
    env.VENV_PATH = "${WORKSPACE}/venv"
    env.PYTHON = "${env.VENV_PATH}/bin/python"
    env.PIP = "${env.VENV_PATH}/bin/pip"
    env.MODEL_DIR = "${WORKSPACE}/models"
    env.MODEL_NAME = "keyword_predictor"
    env.TOKENIZER_NAME = "tokenizer"
    // Use parameter if provided, otherwise default to workspace/data/xml_files
    env.XML_FOLDER = params.XML_FOLDER_PATH ?: "${WORKSPACE}/data/xml_files"
    env.DATASET_OUTPUT = "${WORKSPACE}/keyword_dataset.json"
    env.CLEANED_DATASET = "${WORKSPACE}/keyword_dataset_cleaned.json"
    env.MODEL_VERSION = "${env.BUILD_NUMBER}"
    env.NOTIFICATION_EMAIL = "your-email@example.com"
    
    stage('Checkout') {
        echo "📦 Checking out code from ${env.GIT_BRANCH}"
        checkout scm
    }
    
    stage('Setup Environment') {
        // Set timestamp for model versioning (sandbox-safe approach)
        env.MODEL_TIMESTAMP = sh(
            script: 'date +%Y%m%d_%H%M%S',
            returnStdout: true
        ).trim()
        
        echo "🔧 Setting up Python virtual environment..."
        echo "   Model timestamp: ${env.MODEL_TIMESTAMP}"
        sh """
            python3 -m venv ${env.VENV_PATH} || true
            ${env.PIP} install --upgrade pip wheel
            # Install setuptools<81 first to avoid pkg_resources deprecation warning
            ${env.PIP} install "setuptools<81.0.0"
            ${env.PIP} install -r requirements.txt
        """
    }
    
    stage('Run Tests') {
        echo "🧪 Running unit tests..."
        sh """
            ${env.PYTHON} -m pytest tests/ -v --cov=. --cov-report=html --cov-report=xml --cov-report=term || true
        """
    }
    
    stage('Code Quality') {
        echo "🔍 Running code quality checks..."
        sh """
            # Check code formatting with black (exclude checkpoints and other generated files)
            echo "📝 Checking code formatting..."
            # Use pyproject.toml for exclude patterns, or specify directories directly
            ${env.PYTHON} -m black --check . || {
                echo "❌ Code formatting check failed! Run 'black .' to auto-format."
                exit 1
            }
            echo "✅ Code formatting is correct!"
            
            # Run flake8 for critical errors only (syntax errors, undefined names, etc.)
            echo "🔍 Running flake8 for critical errors..."
            ${env.PYTHON} -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics \\
                --exclude=venv,env,.venv,node_modules,build,dist,*.egg-info,__pycache__,.pytest_cache,.mypy_cache || {
                echo "❌ Flake8 found critical errors!"
                exit 1
            }
            echo "✅ No critical errors found!"
        """
    }
    
    // Weekly Training stages - conditional
    if (params.RUN_TRAINING == true || env.BUILD_CAUSE == 'TIMERTRIGGER') {
        // Create models directory and validate inputs
        stage('Prepare Training') {
            echo "🚀 Starting weekly training pipeline..."
            
            // Create models directory
            sh "mkdir -p ${env.MODEL_DIR}"
            
            // Check if XML data exists - fail stage if not available
            sh """
                if [ ! -d "${env.XML_FOLDER}" ] || [ -z "\$(ls -A ${env.XML_FOLDER} 2>/dev/null)" ]; then
                    echo "❌ ERROR: XML folder is empty or doesn't exist: ${env.XML_FOLDER}"
                    echo "ℹ️  To configure: Provide XML_FOLDER_PATH build parameter (e.g., /path/to/xml_files)"
                    echo "ℹ️  Or set it as an environment variable in Jenkins job configuration"
                    exit 1
                fi
            """
            
            // Set tokenizer output path as environment variable
            env.TOKENIZER_OUTPUT = "${WORKSPACE}/tokenizer.json"
            
            echo "✅ Preparation complete. XML folder: ${env.XML_FOLDER}"
        }
        
        stage('Extract Keywords') {
            echo "📊 Extracting keywords from XML files..."
            
            if (params.FRESH_TRAINING) {
                echo "🔄 Using fresh mode (new data only)..."
                sh """
                    ${env.PYTHON} extract_keywords.py --folder ${env.XML_FOLDER} --output ${env.DATASET_OUTPUT} || {
                        echo "❌ ERROR: Keyword extraction failed!"
                        exit 1
                    }
                """
                echo "✅ Keyword extraction completed! (New data only, old data ignored)"
            } else {
                echo "🔄 Using merge mode (preserve existing data)..."
                sh """
                    ${env.PYTHON} extract_keywords.py --folder ${env.XML_FOLDER} --output ${env.DATASET_OUTPUT} --merge || {
                        echo "❌ ERROR: Keyword extraction failed!"
                        exit 1
                    }
                """
                echo "✅ Keyword extraction completed! (Old data preserved, duplicates removed)"
            }
        }
        
        stage('Clean Dataset') {
            echo "🧹 Cleaning dataset..."
            
            if (params.FRESH_TRAINING) {
                echo "🔄 Using fresh mode (new data only)..."
                sh """
                    ${env.PYTHON} clean_keyword_dataset.py --input ${env.DATASET_OUTPUT} --output ${env.CLEANED_DATASET} || {
                        echo "❌ ERROR: Dataset cleaning failed!"
                        exit 1
                    }
                """
                echo "✅ Dataset cleaning completed! (New data only, old cleaned data ignored)"
            } else {
                echo "🔄 Using append mode (preserve existing cleaned data)..."
                sh """
                    ${env.PYTHON} clean_keyword_dataset.py --input ${env.DATASET_OUTPUT} --output ${env.CLEANED_DATASET} --append || {
                        echo "❌ ERROR: Dataset cleaning failed!"
                        exit 1
                    }
                """
                echo "✅ Dataset cleaning completed! (Old cleaned data preserved, duplicates removed)"
            }
        }
        
        stage('Inspect Dataset') {
            echo "🎯 Inspecting dataset statistics..."
            sh """
                ${env.PYTHON} inspect_keyword_dataset.py --file ${env.CLEANED_DATASET} || true
            """
            echo "✅ Dataset inspection completed!"
        }
        
        stage('Train Model') {
            echo "🏋️  Training LSTM model..."
            
            sh """
                # Check if we should continue training from existing model
                # Only use incremental training if:
                # 1. FRESH_TRAINING is false (merge mode)
                # 2. Existing model and tokenizer files exist
                if [ "${params.FRESH_TRAINING}" = "false" ] && [ -f "${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras" ] && [ -f "${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json" ]; then
                    echo "🔄 Continuing training from existing model (incremental learning)..."
                    echo "   Existing model: ${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras"
                    echo "   Existing tokenizer: ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json"
                    ${env.PYTHON} train_keyword_predictor.py \
                        --input ${env.CLEANED_DATASET} \
                        --model-output ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras \
                        --tokenizer-output ${env.TOKENIZER_OUTPUT} \
                        --continue-training \
                        --existing-model ${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras \
                        --existing-tokenizer ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json || {
                        echo "❌ ERROR: Model training failed!"
                        exit 1
                    }
                else
                    if [ "${params.FRESH_TRAINING}" = "true" ]; then
                        echo "🆕 Training new model from scratch (fresh training mode)..."
                    else
                        echo "🆕 Training new model from scratch (no existing model found)..."
                    fi
                    ${env.PYTHON} train_keyword_predictor.py \
                        --input ${env.CLEANED_DATASET} \
                        --model-output ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras \
                        --tokenizer-output ${env.TOKENIZER_OUTPUT} || {
                        echo "❌ ERROR: Model training failed!"
                        exit 1
                    }
                fi
            """
            echo "✅ Model training completed!"
        }
        
        stage('Archive Models') {
            echo "📦 Archiving model and tokenizer..."
            
            // Verify model file exists
            if (!fileExists("${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras")) {
                error("Model file not found: ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras")
            }
            
            // Verify tokenizer file exists
            if (!fileExists("${env.TOKENIZER_OUTPUT}")) {
                error("Tokenizer file not found after training: ${env.TOKENIZER_OUTPUT}")
            }
            
            sh """
                # Copy to latest versions
                cp ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras ${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras
                cp ${env.TOKENIZER_OUTPUT} ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json
                cp ${env.TOKENIZER_OUTPUT} ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.json
                
                echo "✅ Model and tokenizer copied to latest versions"
            """
            
            // Archive model artifacts (use relative paths from workspace)
            archiveArtifacts artifacts: "models/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras, models/${env.TOKENIZER_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.json", allowEmptyArchive: false
            
            echo "✅ Model archiving completed!"
        }
        
        // Convert to TensorFlow.js - only if training was successful
        if (fileExists("${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras")) {
            stage('Convert to TensorFlow.js') {
                echo "🔄 Converting model to TensorFlow.js format..."
                
                // Verify required files exist before conversion
                if (!fileExists("${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json")) {
                    error("Cannot convert: Tokenizer file not found: ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json. Training may have failed.")
                }
                
                sh """
                    # Install latest tensorflowjs for better .keras format support
                    ${env.PIP} install "tensorflowjs>=4.22.0" || true
                    mkdir -p ${WORKSPACE}/tfjs_model
                    ${env.PYTHON} convert_to_tfjs.py \
                        --model ${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras \
                        --tokenizer ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json \
                        --output ${WORKSPACE}/tfjs_model \
                        --tokenizer-output ${WORKSPACE}/tfjs_model/tokenizer_js.json
                """
                
                // Archive TF.js model
                archiveArtifacts artifacts: "tfjs_model/**", allowEmptyArchive: false
            }
        }
        
        // Deploy Model - only if training was successful and deployment is enabled
        if (params.DEPLOY_MODEL == true && fileExists("${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras") && fileExists("${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json")) {
            stage('Deploy Model') {
                echo "🚀 Deploying model..."
                // Add your deployment logic here
                // Examples:
                // - Copy model to production server
                // - Update API service with new model
                // - Restart services
                
                sh """
                    echo "Deployment logic goes here..."
                    echo "Model: ${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras"
                    echo "Tokenizer: ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json"
                """
            }
        }
    }
}
