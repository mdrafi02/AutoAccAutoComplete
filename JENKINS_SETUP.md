# Jenkins Pipeline Setup Guide

This guide explains how to set up and configure the Jenkins pipeline for automated testing and weekly model training.

## 📋 Overview

The Jenkins pipeline provides:
- **Automated Testing**: Runs unit tests on every commit/PR
- **Weekly Training**: Automatically trains the model once a week
- **Model Versioning**: Tracks model versions with timestamps
- **Code Quality Checks**: Runs linting and formatting checks
- **TensorFlow.js Conversion**: Converts models for frontend use
- **Notifications**: Sends email notifications on success/failure

## 🚀 Quick Setup

### 1. Prerequisites

- Jenkins server (2.400+ recommended)
- Python 3.7+ installed on Jenkins agent
- Git repository access
- Required Jenkins plugins:
  - Pipeline
  - HTML Publisher (for coverage reports)
  - Coverage (for code coverage)
  - Email Extension (for notifications)
  - Build Timestamp (optional)

### 2. Install Jenkins Plugins

```bash
# Via Jenkins UI: Manage Jenkins > Plugins
# Or via Jenkins CLI
```

Required plugins:
- `workflow-aggregator` (Pipeline)
- `htmlpublisher` (HTML Publisher)
- `cobertura` (Coverage)
- `email-ext` (Email Extension)
- `build-timestamp` (optional)

### 3. Create Jenkins Pipeline Job

1. **New Item** → **Pipeline**
2. **Pipeline Definition**: Select "Pipeline script from SCM"
3. **SCM**: Git
4. **Repository URL**: `git@github.com:mdrafi02/AutoAccAutoComplete.git`
5. **Credentials**: Add your GitHub credentials
6. **Branch Specifier**: `*/main` (or your main branch)
7. **Script Path**: `Jenkinsfile`

### 4. Configure Environment Variables

In Jenkins job configuration, add environment variables:

```groovy
// In Jenkinsfile or via Jenkins UI > Configure > Environment Variables

XML_FOLDER = "/path/to/your/xml/files"  // Path to Robot Framework XML files
NOTIFICATION_EMAIL = "your-email@example.com"  // Email for notifications
```

### 5. Set Up Weekly Training Schedule

#### Option A: Using Build Triggers (Recommended)

1. Go to **Configure** → **Build Triggers**
2. Select **Build periodically**
3. Add cron expression: `H 2 * * 0` (Every Sunday at 2 AM)

Or in Jenkinsfile, add:
```groovy
triggers {
    cron('H 2 * * 0')  // Every Sunday at 2 AM
}
```

#### Option B: Manual Trigger with Parameters

1. Go to **Configure** → **This project is parameterized**
2. Add boolean parameters:
   - `RUN_TRAINING` (default: false)
   - `DEPLOY_MODEL` (default: false)

3. Trigger manually via "Build with Parameters"

### 6. Configure Build Parameters (Optional)

Add these parameters for flexible control:

- **RUN_TRAINING** (Boolean): Force training run
- **DEPLOY_MODEL** (Boolean): Deploy model after training
- **XML_FOLDER** (String): Override XML folder path
- **MODEL_VERSION** (String): Override model version

## 📁 Directory Structure

The pipeline expects this structure:

```
workspace/
├── data/
│   └── xml_files/          # Robot Framework XML files
├── models/                  # Trained models (created by pipeline)
│   ├── keyword_predictor_v1_20240101_020000.keras
│   ├── keyword_predictor_latest.keras
│   ├── tokenizer_v1_20240101_020000.json
│   └── tokenizer_latest.json
├── tfjs_model/              # TensorFlow.js models (created by pipeline)
├── tests/                   # Unit tests
├── htmlcov/                 # Coverage reports (generated)
└── ...
```

## 🔧 Pipeline Stages

### 1. Checkout
- Checks out code from Git repository

### 2. Setup Environment
- Creates Python virtual environment
- Installs dependencies from `requirements.txt` (consolidated file with all dependencies)

### 3. Run Tests
- Runs pytest with coverage
- Generates HTML and XML coverage reports
- Publishes coverage reports to Jenkins

### 4. Code Quality
- Runs flake8 for linting
- Runs black for code formatting checks

### 5. Weekly Training (Conditional)
- **Trigger**: Weekly schedule or manual parameter
- Extracts keywords from XML files
- Cleans dataset
- Inspects dataset
- Trains model with versioning
- Archives model artifacts

### 6. Convert to TensorFlow.js (Conditional)
- Converts trained model to TensorFlow.js format
- Archives TF.js model files

### 7. Deploy Model (Conditional)
- Deploys model to production (customize as needed)
- Only runs if `DEPLOY_MODEL` parameter is true

## 📧 Notifications

The pipeline sends email notifications on:
- ✅ **Success**: Training completed successfully
- ❌ **Failure**: Training or tests failed

Configure email in Jenkinsfile:
```groovy
NOTIFICATION_EMAIL = "your-email@example.com"
```

Or set up Slack/Teams webhooks by modifying the `post` sections.

## 🎯 Usage Examples

### Run Tests Only (Default)
```bash
# Triggered on every commit/PR
# Runs: Checkout → Setup → Tests → Code Quality
```

### Run Full Training Pipeline
```bash
# Option 1: Wait for weekly schedule (Sunday 2 AM)
# Option 2: Build with Parameters → RUN_TRAINING = true
```

### Run Training + Deployment
```bash
# Build with Parameters:
# - RUN_TRAINING = true
# - DEPLOY_MODEL = true
```

## 🔍 Monitoring

### View Test Results
- **Coverage Report**: Available in "Coverage Report" link in build
- **Test Results**: Check console output or pytest HTML reports

### View Model Artifacts
- **Models**: Archived in build artifacts
- **Location**: `models/keyword_predictor_v{version}_{timestamp}.keras`

### View Build History
- Jenkins dashboard shows build status
- Click on build number to see details

## 🛠️ Troubleshooting

### Issue: Tests Fail
```bash
# Check:
1. Python version (needs 3.7+)
2. Dependencies installed correctly
3. Test files are in tests/ directory
4. Model files exist (for tests that need them)
```

### Issue: Training Fails
```bash
# Check:
1. XML_FOLDER path is correct and accessible
2. XML files exist in the folder
3. Sufficient disk space for models
4. Python dependencies (tensorflow, etc.) installed
```

### Issue: Model Not Found
```bash
# Ensure:
1. Training stage completed successfully
2. Model files are in models/ directory
3. File permissions are correct
```

### Issue: Email Notifications Not Working
```bash
# Configure:
1. Jenkins → Configure System → Email Extension
2. Set SMTP server settings
3. Test email configuration
```

## 📝 Customization

### Change Training Schedule
Edit Jenkinsfile:
```groovy
triggers {
    cron('H 2 * * 1')  // Every Monday at 2 AM
    // cron('0 */6 * * *')  // Every 6 hours
}
```

### Add Custom Deployment
Edit the "Deploy Model" stage:
```groovy
stage('Deploy Model') {
    steps {
        sh """
            # Your deployment script
            scp ${MODEL_DIR}/${MODEL_NAME}_latest.keras user@server:/path/
            ssh user@server 'systemctl restart api-service'
        """
    }
}
```

### Add Slack Notifications
Install Slack plugin and add:
```groovy
slackSend(
    channel: '#ml-models',
    color: 'good',
    message: "Model training completed: Build #${env.BUILD_NUMBER}"
)
```

## 🔐 Security Best Practices

1. **Credentials**: Store sensitive data in Jenkins Credentials
2. **Secrets**: Don't hardcode passwords/API keys
3. **Permissions**: Restrict who can trigger training
4. **Artifacts**: Secure model storage location
5. **Notifications**: Use secure channels for notifications

## 📊 Metrics and Reporting

The pipeline provides:
- **Test Coverage**: HTML and XML reports
- **Build History**: Success/failure rates
- **Model Versions**: Tracked with timestamps
- **Artifact Storage**: Models archived per build

## 🚀 Next Steps

1. ✅ Set up Jenkins server
2. ✅ Install required plugins
3. ✅ Create pipeline job
4. ✅ Configure environment variables
5. ✅ Set up weekly schedule
6. ✅ Test pipeline with manual trigger
7. ✅ Monitor first weekly training run

## 📚 Additional Resources

- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Pipeline Syntax Reference](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Email Extension Plugin](https://plugins.jenkins.io/email-ext/)

---

**Questions?** Check the build logs or contact your DevOps team.

