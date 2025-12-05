# Robot Framework Keyword Predictor

An intelligent LSTM-based keyword prediction system for Robot Framework test automation. This tool learns from existing test cases and predicts the next keyword(s) in a sequence, helping developers write more consistent and efficient test scripts.

## 🎯 Features

- **Intelligent Keyword Prediction**: Predicts next keywords based on context using LSTM neural networks
- **Hierarchical Depth-Based Prediction**: Predict multiple levels ahead with configurable depth
- **Interactive CLI**: User-friendly command-line interface for real-time predictions
- **REST API**: FastAPI-based REST API for integration with IDEs and other tools
- **Incremental Learning**: Add new data and continue training without starting from scratch
- **Automatic Context Handling**: Automatically manages context size based on model architecture

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- TensorFlow 2.x
- Robot Framework XML files (for training)

### Installation

1. **Clone or navigate to the project directory:**
```bash
cd robot_keyword_model2
```

2. **Install dependencies:**
```bash
# For API usage
pip install -r requirements_api.txt

# For training (if needed)
pip install tensorflow numpy scikit-learn ijson
```

3. **Train a model (if you don't have one):**
```bash
# Extract keywords from XML files
python extract_keywords.py --folder /path/to/xml/files --output keyword_dataset.json

# Clean the dataset
python clean_keyword_dataset.py --input keyword_dataset.json --output keyword_dataset_cleaned.json

# Train the model
python train_keyword_predictor.py --input keyword_dataset_cleaned.json
```

## 📖 Usage

### Command Line Interface (CLI)

#### Basic Usage (Depth 1 - Default)

```bash
python predict_keywords_siva.py
```

This starts an interactive session where you can:
1. Enter initial keywords (comma-separated)
2. View top predictions
3. Select a prediction or add your own keyword
4. Continue building the sequence

#### Hierarchical Predictions (Depth 2+)

```bash
# Predict with depth 2 (shows next level for each prediction)
python predict_keywords_siva.py --depth 2

# Predict with depth 3 (deeper hierarchy)
python predict_keywords_siva.py --depth 3
```

**Example CLI Session:**
```
👉 YOUR INPUT: login1.login_user, login1.authenticate

📊 MODEL RESPONSE - Top 3 predictions (depth 2):
   ──────────────────────────────────────────────────────────────────
   1. login1.logout                    ████████████████████░░░░░░░░░░ 65.2%
      ├─ login1.cleanup                █████████░░░░░░░░░░░░░░░░░░░░ 45.0%
      ├─ login1.close_connection       ███████░░░░░░░░░░░░░░░░░░░░░░ 32.0%
      └─ login1.finalize               █████░░░░░░░░░░░░░░░░░░░░░░░░ 18.0%
   2. login1.close_session             █████████░░░░░░░░░░░░░░░░░░░░ 30.1%
      ├─ login1.verify_logout          ██████████░░░░░░░░░░░░░░░░░░░░ 52.0%
      ├─ login1.clear_cache            ██████░░░░░░░░░░░░░░░░░░░░░░ 28.0%
      └─ login1.reset_state            ███░░░░░░░░░░░░░░░░░░░░░░░░░░ 15.0%
   3. login1.refresh                    ████░░░░░░░░░░░░░░░░░░░░░░░░░░ 18.5%
   ──────────────────────────────────────────────────────────────────
```

### REST API

#### Start the API Server

```bash
python api_keyword_predictor.py
```

The API will be available at `http://localhost:8000`

#### API Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Predict Next Keywords:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["tntmgt1.obtain_tenant", "tntmgt1.get_tenant_username"],
    "top_k": 3,
    "depth": 2
  }'
```

**Response (depth: 2):**
```json
{
  "predictions": [
    {
      "keyword": "tntmgt1.validate_tenant",
      "probability": 0.652,
      "next_predictions": [
        {
          "keyword": "tntmgt1.save_tenant",
          "probability": 0.45,
          "next_predictions": null
        },
        {
          "keyword": "tntmgt1.update_tenant",
          "probability": 0.32,
          "next_predictions": null
        }
      ]
    }
  ],
  "context_used": ["tntmgt1.obtain_tenant", "tntmgt1.get_tenant_username"],
  "context_size": 2,
  "full_sequence_length": 2
}
```

#### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

For detailed API documentation, see [API_USAGE.md](API_USAGE.md)

## 🔧 Configuration

### CLI Options

```bash
python predict_keywords_siva.py --help

Options:
  --model, -m      Path to trained model file (default: keyword_predictor.keras)
  --tokenizer, -t  Path to tokenizer JSON file (default: tokenizer.json)
  --depth, -d      Depth for hierarchical prediction (default: 1)
```

### API Options

```bash
python api_keyword_predictor.py --help

Options:
  --host           Host to bind to (default: 0.0.0.0)
  --port           Port to bind to (default: 8000)
  --model, -m      Path to model file
  --tokenizer, -t  Path to tokenizer file
  --reload         Enable auto-reload for development
```

## 📁 Project Structure

```
robot_keyword_model2/
├── README.md                      # This file
├── API_USAGE.md                   # Detailed API documentation
├── INCREMENTAL_UPDATE_GUIDE.md    # Guide for incremental updates
├── LSTM_EXPLANATION.md            # Technical explanation of LSTM model
├── NAMING_CONVENTIONS.md          # Code naming conventions
│
├── extract_keywords.py            # Extract keywords from XML files
├── clean_keyword_dataset.py       # Clean and filter dataset
├── inspect_keyword_dataset.py     # Analyze dataset statistics
├── train_keyword_predictor.py    # Train the LSTM model
├── predict_keywords_siva.py       # Interactive CLI for predictions
├── predict_keywords.py            # Alternative CLI (simpler)
├── api_keyword_predictor.py       # REST API server
├── api_example_client.py          # Example API client
├── run_pipeline.py                # Orchestrate full pipeline
│
├── keyword_dataset.json           # Raw extracted dataset
├── keyword_dataset_cleaned.json   # Cleaned dataset
├── keyword_predictor.keras        # Trained model
├── tokenizer.json                 # Tokenizer for text processing
│
└── requirements_api.txt           # API dependencies
```

## 🔄 Complete Pipeline

### Full Training Pipeline

```bash
# Run the complete pipeline from XML files to trained model
python run_pipeline.py --xml-folder /path/to/xml/files
```

### Incremental Updates

Add new data without retraining from scratch:

```bash
# Extract new keywords and merge with existing dataset
python extract_keywords.py --folder /path/to/new/xml \
    --output keyword_dataset.json --merge

# Clean the updated dataset
python clean_keyword_dataset.py --input keyword_dataset.json \
    --output keyword_dataset_cleaned.json --append

# Continue training with new data
python train_keyword_predictor.py --input keyword_dataset_cleaned.json \
    --continue-training --epochs 10
```

For detailed incremental update instructions, see [INCREMENTAL_UPDATE_GUIDE.md](INCREMENTAL_UPDATE_GUIDE.md)

## 🎓 How It Works

### Depth-Based Prediction

The system supports hierarchical prediction with configurable depth:

- **Depth 1** (default): Returns top_k predictions for the current context
- **Depth 2**: For each top_k prediction, also returns the next top_k predictions
- **Depth 3+**: Recursively continues deeper, creating a prediction tree

This allows you to see not just the immediate next keyword, but also what might come after that, helping with longer-term test planning.

### Model Architecture

- **LSTM (Long Short-Term Memory)**: Neural network that learns sequential patterns
- **Embedding Layer**: Converts keywords to dense vectors
- **Context Window**: Uses last N keywords to predict the next one
- **Vocabulary**: Automatically handles new keywords during incremental training

For technical details, see [LSTM_EXPLANATION.md](LSTM_EXPLANATION.md)

## 📝 Examples

### Python Integration

```python
import requests

def predict_next_keywords(keywords, top_k=3, depth=2):
    response = requests.post(
        'http://localhost:8000/predict',
        json={
            'keywords': keywords,
            'top_k': top_k,
            'depth': depth
        }
    )
    return response.json()['predictions']

# Usage
predictions = predict_next_keywords(
    ['login1.login_user', 'login1.authenticate'],
    depth=2
)

for pred in predictions:
    print(f"{pred['keyword']}: {pred['probability']*100:.1f}%")
    if pred.get('next_predictions'):
        for next_pred in pred['next_predictions']:
            print(f"  └─ {next_pred['keyword']}: {next_pred['probability']*100:.1f}%")
```

### JavaScript/TypeScript Integration

```javascript
async function predictNextKeywords(keywords, topK = 3, depth = 2) {
  const response = await fetch('http://localhost:8000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keywords, top_k: topK, depth })
  });
  return response.json();
}

// Usage
const result = await predictNextKeywords(
  ['login1.login_user', 'login1.authenticate'],
  3,
  2
);
console.log(result.predictions);
```

## 🧪 Testing

The project includes comprehensive unit tests for all major components.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_prediction.py
```

### Test Coverage

- **Prediction Functions**: `predict_next_keyword`, `predict_next_keyword_with_depth`
- **Keyword Extraction**: `extract_keywords_from_output`, `normalize_keyword`
- **API Endpoints**: All FastAPI endpoints with model loading
- **Model Loading**: Model and tokenizer loading functionality

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 🔄 CI/CD Pipeline

The project includes a Jenkins pipeline for automated testing and weekly model training.

### Features

- **Automated Testing**: Runs unit tests on every commit/PR
- **Weekly Training**: Automatically trains model once a week (configurable)
- **Model Versioning**: Tracks model versions with timestamps
- **Code Quality**: Runs linting and formatting checks
- **TensorFlow.js Conversion**: Converts models for frontend use
- **Notifications**: Email notifications on success/failure

### Quick Setup

1. **Install Jenkins plugins**: Pipeline, HTML Publisher, Coverage, Email Extension
2. **Create pipeline job**: Use `Jenkinsfile` from repository
3. **Configure environment**: Set `XML_FOLDER` and `NOTIFICATION_EMAIL`
4. **Set schedule**: Configure weekly training (default: Sunday 2 AM)

See [JENKINS_SETUP.md](JENKINS_SETUP.md) for complete setup instructions.

### Pipeline Stages

1. **Checkout**: Get code from repository
2. **Setup Environment**: Create virtual environment and install dependencies
3. **Run Tests**: Execute unit tests with coverage
4. **Code Quality**: Run linting and formatting checks
5. **Weekly Training** (conditional): Extract, clean, train, and version model
6. **Convert to TensorFlow.js** (conditional): Convert model for frontend
7. **Deploy Model** (conditional): Deploy to production

## 🐛 Troubleshooting

### Common Issues

1. **Model not found**: Ensure `keyword_predictor.keras` and `tokenizer.json` exist
2. **JSON decode error**: Check for trailing commas in JSON requests
3. **503 errors**: Model failed to load - check server logs
4. **400 errors**: Invalid input - verify keywords list and parameters

### Getting Help

- Check [API_USAGE.md](API_USAGE.md) for detailed API documentation
- Review [INCREMENTAL_UPDATE_GUIDE.md](INCREMENTAL_UPDATE_GUIDE.md) for update procedures
- Check server logs for detailed error messages

## 🔗 Additional Documentation

- [API_USAGE.md](API_USAGE.md) - Complete API reference and examples
- [INCREMENTAL_UPDATE_GUIDE.md](INCREMENTAL_UPDATE_GUIDE.md) - Incremental learning guide
- [LSTM_EXPLANATION.md](LSTM_EXPLANATION.md) - Technical model explanation
- [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) - Code style guide
- [TESTING.md](TESTING.md) - Testing guide and best practices
- [JENKINS_SETUP.md](JENKINS_SETUP.md) - Jenkins CI/CD pipeline setup
- [TENSORFLOW_JS_GUIDE.md](TENSORFLOW_JS_GUIDE.md) - Frontend integration guide

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]

---

**Made with ❤️ for Robot Framework test automation**

