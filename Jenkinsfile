pipeline {
    agent any
    
    parameters {
        booleanParam(name: 'RUN_TRAINING', defaultValue: false, description: 'Run model training pipeline')
        booleanParam(name: 'DEPLOY_MODEL', defaultValue: false, description: 'Deploy model to production')
    }
    
    environment {
        // Python virtual environment
        VENV_PATH = "${WORKSPACE}/venv"
        PYTHON = "${VENV_PATH}/bin/python"
        PIP = "${VENV_PATH}/bin/pip"
        
        // Model paths
        MODEL_DIR = "${WORKSPACE}/models"
        MODEL_NAME = "keyword_predictor"
        TOKENIZER_NAME = "tokenizer"
        
        // Training data paths (configure these based on your setup)
        XML_FOLDER = "${WORKSPACE}/data/xml_files"
        DATASET_OUTPUT = "${WORKSPACE}/keyword_dataset.json"
        CLEANED_DATASET = "${WORKSPACE}/keyword_dataset_cleaned.json"
        
        // Versioning
        MODEL_VERSION = "${env.BUILD_NUMBER}"
        
        // Notification (configure your email/Slack webhook)
        NOTIFICATION_EMAIL = "your-email@example.com"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "📦 Checking out code from ${env.GIT_BRANCH}"
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    // Set timestamp for model versioning
                    env.MODEL_TIMESTAMP = sh(
                        script: "date +'%Y%m%d_%H%M%S'",
                        returnStdout: true
                    ).trim()
                    
                    echo "🔧 Setting up Python virtual environment..."
                    sh """
                        python3 -m venv ${VENV_PATH} || true
                        ${PIP} install --upgrade pip setuptools wheel
                        ${PIP} install -r requirements_api.txt
                        ${PIP} install -r requirements_test.txt || true
                        ${PIP} install tensorflow numpy scikit-learn ijson
                    """
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    echo "🧪 Running unit tests..."
                    sh """
                        ${PYTHON} -m pytest tests/ -v --cov=. --cov-report=html --cov-report=xml --cov-report=term || true
                    """
                }
            }
        }
        
        stage('Code Quality') {
            steps {
                script {
                    echo "🔍 Running code quality checks..."
                    sh """
                        ${PYTHON} -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
                        ${PYTHON} -m black --check . || true
                    """
                }
            }
        }
        
        stage('Weekly Training') {
            when {
                // Run weekly training on Sundays at 2 AM (configure via cron trigger)
                // Or trigger manually with parameter
                anyOf {
                    expression { params.RUN_TRAINING == true }
                    expression { env.BUILD_CAUSE == 'TIMERTRIGGER' }
                }
            }
            steps {
                script {
                    echo "🚀 Starting weekly training pipeline..."
                    
                    // Create models directory
                    sh "mkdir -p ${MODEL_DIR}"
                    
                    // Check if XML data exists
                    sh """
                        if [ ! -d "${XML_FOLDER}" ] || [ -z "\$(ls -A ${XML_FOLDER} 2>/dev/null)" ]; then
                            echo "⚠️  WARNING: XML folder is empty or doesn't exist: ${XML_FOLDER}"
                            echo "⚠️  Training will be skipped. Please configure XML_FOLDER environment variable."
                            exit 1
                        fi
                    """
                    
                    // Run full training pipeline
                    sh """
                        echo "📊 Step 1: Extracting keywords from XML files..."
                        ${PYTHON} extract_keywords.py --folder ${XML_FOLDER} --output ${DATASET_OUTPUT}
                        
                        echo "🧹 Step 2: Cleaning dataset..."
                        ${PYTHON} clean_keyword_dataset.py --input ${DATASET_OUTPUT} --output ${CLEANED_DATASET}
                        
                        echo "🎯 Step 3: Inspecting dataset..."
                        ${PYTHON} inspect_keyword_dataset.py --input ${CLEANED_DATASET} || true
                        
                        echo "🏋️  Step 4: Training model..."
                        TOKENIZER_OUTPUT="${WORKSPACE}/tokenizer.json"
                        ${PYTHON} train_keyword_predictor.py \
                            --input ${CLEANED_DATASET} \
                            --output ${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras \
                            --tokenizer-output ${TOKENIZER_OUTPUT}
                        
                        echo "📦 Step 5: Copying model and tokenizer to latest..."
                        # Verify model file exists
                        if [ ! -f "${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras" ]; then
                            echo "❌ ERROR: Model file not found after training!"
                            exit 1
                        fi
                        
                        # Verify tokenizer file exists
                        if [ ! -f "${TOKENIZER_OUTPUT}" ]; then
                            echo "❌ ERROR: Tokenizer file not found after training: ${TOKENIZER_OUTPUT}"
                            exit 1
                        fi
                        
                        cp ${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras ${MODEL_DIR}/${MODEL_NAME}_latest.keras
                        cp ${TOKENIZER_OUTPUT} ${MODEL_DIR}/${TOKENIZER_NAME}_latest.json
                        cp ${TOKENIZER_OUTPUT} ${MODEL_DIR}/${TOKENIZER_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.json
                    """
                }
            }
            post {
                success {
                    script {
                        echo "✅ Training completed successfully!"
                        // Verify files exist before archiving
                        if (!fileExists("${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras")) {
                            error("Model file not found: ${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras")
                        }
                        if (!fileExists("${MODEL_DIR}/${TOKENIZER_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.json")) {
                            error("Tokenizer file not found: ${MODEL_DIR}/${TOKENIZER_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.json")
                        }
                        
                        // Archive model artifacts
                        archiveArtifacts artifacts: "${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras, ${MODEL_DIR}/${TOKENIZER_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.json", allowEmptyArchive: false
                    }
                }
                failure {
                    script {
                        echo "❌ Training failed!"
                    }
                }
            }
        }
        
        stage('Convert to TensorFlow.js') {
            when {
                // Only run if training was triggered
                anyOf {
                    expression { params.RUN_TRAINING == true }
                    expression { env.BUILD_CAUSE == 'TIMERTRIGGER' }
                }
            }
            steps {
                script {
                    echo "🔄 Converting model to TensorFlow.js format..."
                    
                    // Verify required files exist before conversion
                    if (!fileExists("${MODEL_DIR}/${MODEL_NAME}_latest.keras")) {
                        error("Cannot convert: Model file not found: ${MODEL_DIR}/${MODEL_NAME}_latest.keras. Training may have failed.")
                    }
                    if (!fileExists("${MODEL_DIR}/${TOKENIZER_NAME}_latest.json")) {
                        error("Cannot convert: Tokenizer file not found: ${MODEL_DIR}/${TOKENIZER_NAME}_latest.json. Training may have failed.")
                    }
                    
                    sh """
                        ${PIP} install tensorflowjs || true
                        ${PYTHON} convert_to_tfjs.py \
                            --model ${MODEL_DIR}/${MODEL_NAME}_latest.keras \
                            --tokenizer ${MODEL_DIR}/${TOKENIZER_NAME}_latest.json \
                            --output ${WORKSPACE}/tfjs_model \
                            --tokenizer-output ${WORKSPACE}/tfjs_model/tokenizer_js.json
                    """
                }
            }
            post {
                success {
                    // Archive TF.js model
                    archiveArtifacts artifacts: "tfjs_model/**", allowEmptyArchive: false
                }
            }
        }
        
        stage('Deploy Model') {
            when {
                // Deploy if training was successful and deployment is enabled
                allOf {
                    anyOf {
                        expression { params.RUN_TRAINING == true }
                        expression { env.BUILD_CAUSE == 'TIMERTRIGGER' }
                    }
                    expression { params.DEPLOY_MODEL == true }
                }
            }
            steps {
                script {
                    echo "🚀 Deploying model..."
                    // Add your deployment logic here
                    // Examples:
                    // - Copy model to production server
                    // - Update API service with new model
                    // - Restart services
                    
                    sh """
                        echo "Deployment logic goes here..."
                        echo "Model: ${MODEL_DIR}/${MODEL_NAME}_latest.keras"
                        echo "Tokenizer: ${MODEL_DIR}/${TOKENIZER_NAME}_latest.json"
                    """
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "🧹 Cleaning up..."
            }
        }
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed!"
        }
        unstable {
            echo "⚠️  Pipeline is unstable!"
        }
    }
}
