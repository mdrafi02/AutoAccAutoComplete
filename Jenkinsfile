properties([
    parameters([
        booleanParam(name: 'RUN_TRAINING', defaultValue: false, description: 'Run model training pipeline'),
        booleanParam(name: 'DEPLOY_MODEL', defaultValue: false, description: 'Deploy model to production'),
        stringParam(name: 'XML_FOLDER_PATH', defaultValue: '', description: 'Path to XML files folder (e.g., /path/to/xml_files or relative to workspace)')
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
        // Set timestamp for model versioning
        env.MODEL_TIMESTAMP = sh(
            script: "date +'%Y%m%d_%H%M%S'",
            returnStdout: true
        ).trim()
        
        echo "🔧 Setting up Python virtual environment..."
        sh """
            python3 -m venv ${env.VENV_PATH} || true
            ${env.PIP} install --upgrade pip setuptools wheel
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
            ${env.PYTHON} -m black --check . --exclude='/(venv|env|\.venv|node_modules|build|dist|\.git|\.eggs|\.mypy_cache|\.pytest_cache|\.tox|__pycache__|\.ipynb_checkpoints)/' || {
                echo "❌ Code formatting check failed! Run 'black .' to auto-format."
                exit 1
            }
            echo "✅ Code formatting is correct!"
            
            # Run flake8 for critical errors only (syntax errors, undefined names, etc.)
            echo "🔍 Running flake8 for critical errors..."
            ${env.PYTHON} -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics \
                --exclude=venv,env,.venv,node_modules,build,dist,*.egg-info,__pycache__,.pytest_cache,.mypy_cache || {
                echo "❌ Flake8 found critical errors!"
                exit 1
            }
            echo "✅ No critical errors found!"
        """
    }
    
    // Weekly Training stage - conditional
    if (params.RUN_TRAINING == true || env.BUILD_CAUSE == 'TIMERTRIGGER') {
        stage('Weekly Training') {
            try {
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
                
                // Run full training pipeline
                sh """
                    echo "📊 Step 1: Extracting keywords from XML files..."
                    ${env.PYTHON} extract_keywords.py --folder ${env.XML_FOLDER} --output ${env.DATASET_OUTPUT} || {
                        echo "❌ ERROR: Keyword extraction failed!"
                        exit 1
                    }
                    
                    echo "🧹 Step 2: Cleaning dataset..."
                    ${env.PYTHON} clean_keyword_dataset.py --input ${env.DATASET_OUTPUT} --output ${env.CLEANED_DATASET} || {
                        echo "❌ ERROR: Dataset cleaning failed!"
                        exit 1
                    }
                    
                    echo "🎯 Step 3: Inspecting dataset..."
                    ${env.PYTHON} inspect_keyword_dataset.py --file ${env.CLEANED_DATASET} || true
                    
                    echo "🏋️  Step 4: Training model..."
                    ${env.PYTHON} train_keyword_predictor.py \
                        --input ${env.CLEANED_DATASET} \
                        --model-output ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras \
                        --tokenizer-output ${env.TOKENIZER_OUTPUT} || {
                        echo "❌ ERROR: Model training failed!"
                        exit 1
                    }
                    
                    echo "📦 Step 5: Copying model and tokenizer to latest..."
                    # Verify model file exists
                    if [ ! -f "${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras" ]; then
                        echo "❌ ERROR: Model file not found after training!"
                        exit 1
                    fi
                    
                    # Verify tokenizer file exists
                    if [ ! -f "${env.TOKENIZER_OUTPUT}" ]; then
                        echo "❌ ERROR: Tokenizer file not found after training: ${env.TOKENIZER_OUTPUT}"
                        exit 1
                    fi
                    
                    cp ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras ${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras
                    cp ${env.TOKENIZER_OUTPUT} ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json
                    cp ${env.TOKENIZER_OUTPUT} ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.json
                """
                
                echo "✅ Training completed successfully!"
                
                // Verify files exist before archiving
                if (!fileExists("${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras")) {
                    error("Model file not found: ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras")
                }
                if (!fileExists("${env.MODEL_DIR}/${env.TOKENIZER_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.json")) {
                    error("Tokenizer file not found: ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.json")
                }
                
                // Archive model artifacts (use relative paths from workspace)
                archiveArtifacts artifacts: "models/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras, models/${env.TOKENIZER_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.json", allowEmptyArchive: false
            } catch (Exception e) {
                echo "❌ Training failed: ${e.getMessage()}"
                throw e
            }
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
                    ${env.PIP} install tensorflowjs || true
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
