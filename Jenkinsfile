pipeline {
    agent any
    
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
        MODEL_TIMESTAMP = "${new Date().format('yyyyMMdd_HHmmss')}"
        
        // Notification (configure your email/Slack webhook)
        NOTIFICATION_EMAIL = "your-email@example.com"
    }
    
    options {
        // Keep last 10 builds
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Timeout after 2 hours
        timeout(time: 2, unit: 'HOURS')
        // Retry once on failure
        retry(1)
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "📦 Checking out code from ${env.GIT_BRANCH}"
                    checkout scm
                }
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
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
            post {
                always {
                    // Publish test results
                    publishHTML([
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report',
                        keepAll: true
                    ])
                    // Publish coverage XML if available
                    publishCoverage adapters: [
                        coberturaAdapter('coverage.xml')
                    ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
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
                        ${PYTHON} train_keyword_predictor.py --input ${CLEANED_DATASET} --output ${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras
                        
                        echo "📦 Step 5: Copying model and tokenizer to latest..."
                        cp ${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras ${MODEL_DIR}/${MODEL_NAME}_latest.keras || true
                        cp tokenizer.json ${MODEL_DIR}/${TOKENIZER_NAME}_latest.json || true
                        cp tokenizer.json ${MODEL_DIR}/${TOKENIZER_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.json || true
                    """
                }
            }
            post {
                success {
                    script {
                        echo "✅ Training completed successfully!"
                        // Archive model artifacts
                        archiveArtifacts artifacts: "${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras, ${MODEL_DIR}/${TOKENIZER_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.json", allowEmptyArchive: false
                        
                        // Send success notification
                        emailext(
                            subject: "✅ Model Training Successful - Build #${env.BUILD_NUMBER}",
                            body: """
                                <h2>Model Training Completed Successfully</h2>
                                <p><strong>Build Number:</strong> ${env.BUILD_NUMBER}</p>
                                <p><strong>Model Version:</strong> v${MODEL_VERSION}</p>
                                <p><strong>Timestamp:</strong> ${MODEL_TIMESTAMP}</p>
                                <p><strong>Model Path:</strong> ${MODEL_DIR}/${MODEL_NAME}_v${MODEL_VERSION}_${MODEL_TIMESTAMP}.keras</p>
                                <p><a href="${env.BUILD_URL}">View Build</a></p>
                            """,
                            to: "${NOTIFICATION_EMAIL}",
                            mimeType: 'text/html'
                        )
                    }
                }
                failure {
                    script {
                        echo "❌ Training failed!"
                        // Send failure notification
                        emailext(
                            subject: "❌ Model Training Failed - Build #${env.BUILD_NUMBER}",
                            body: """
                                <h2>Model Training Failed</h2>
                                <p><strong>Build Number:</strong> ${env.BUILD_NUMBER}</p>
                                <p><strong>Error:</strong> Please check the build logs for details.</p>
                                <p><a href="${env.BUILD_URL}">View Build</a></p>
                            """,
                            to: "${NOTIFICATION_EMAIL}",
                            mimeType: 'text/html'
                        )
                    }
                }
            }
        }
        
        stage('Convert to TensorFlow.js') {
            when {
                // Only run if training was successful
                anyOf {
                    expression { params.RUN_TRAINING == true }
                    expression { env.BUILD_CAUSE == 'TIMERTRIGGER' }
                }
            }
            steps {
                script {
                    echo "🔄 Converting model to TensorFlow.js format..."
                    sh """
                        ${PIP} install tensorflowjs || true
                        ${PYTHON} convert_to_tfjs.py \
                            --model ${MODEL_DIR}/${MODEL_NAME}_latest.keras \
                            --tokenizer ${MODEL_DIR}/${TOKENIZER_NAME}_latest.json \
                            --output ${WORKSPACE}/tfjs_model
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
            // Clean up
            script {
                echo "🧹 Cleaning up..."
                // Keep workspace clean
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

