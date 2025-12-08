# Keyword Predictor API Usage Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies (recommended)
pip install -r requirements.txt

# Or install minimal dependencies for API only
pip install -r requirements-minimal.txt
```

### 2. Start the API Server

```bash
python api_keyword_predictor.py
```

Or with custom model/tokenizer paths:

```bash
python api_keyword_predictor.py --model keyword_predictor.keras --tokenizer tokenizer.json
```

Or on a different port:

```bash
python api_keyword_predictor.py --port 8080
```

### 3. Access API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "context_size": 2,
  "message": "Model loaded and ready"
}
```

### Predict Next Keywords

```bash
POST /predict
```

**Request Body:**
```json
{
  "keywords": ["login1.login_user", "login1.authenticate"],
  "top_k": 3,
  "depth": 1
}
```

**Parameters:**
- `keywords` (required): List of keywords representing the sequence context
- `top_k` (optional): Number of top predictions to return at each level (default: 3, max: 10)
- `depth` (optional): Number of levels deep to predict (default: 1, max: 5)
  - `depth: 1` = Only current level predictions (same as before)
  - `depth: 2` = Current level + next level for each prediction
  - `depth: 3+` = Recursively predicts deeper levels

**Response (depth: 1):**
```json
{
  "predictions": [
    {
      "keyword": "login1.logout",
      "probability": 0.652,
      "next_predictions": null
    },
    {
      "keyword": "login1.close_session",
      "probability": 0.301,
      "next_predictions": null
    },
    {
      "keyword": "login1.refresh",
      "probability": 0.185,
      "next_predictions": null
    }
  ],
  "context_used": ["login1.login_user", "login1.authenticate"],
  "context_size": 2,
  "full_sequence_length": 2
}
```

**Response (depth: 2) - Hierarchical Predictions:**
```json
{
  "predictions": [
    {
      "keyword": "login1.logout",
      "probability": 0.652,
      "next_predictions": [
        {
          "keyword": "login1.cleanup",
          "probability": 0.45,
          "next_predictions": null
        },
        {
          "keyword": "login1.close_connection",
          "probability": 0.32,
          "next_predictions": null
        },
        {
          "keyword": "login1.finalize",
          "probability": 0.18,
          "next_predictions": null
        }
      ]
    },
    {
      "keyword": "login1.close_session",
      "probability": 0.301,
      "next_predictions": [
        {
          "keyword": "login1.verify_logout",
          "probability": 0.52,
          "next_predictions": null
        },
        {
          "keyword": "login1.clear_cache",
          "probability": 0.28,
          "next_predictions": null
        },
        {
          "keyword": "login1.reset_state",
          "probability": 0.15,
          "next_predictions": null
        }
      ]
    },
    {
      "keyword": "login1.refresh",
      "probability": 0.185,
      "next_predictions": [
        {
          "keyword": "login1.reload",
          "probability": 0.41,
          "next_predictions": null
        },
        {
          "keyword": "login1.update",
          "probability": 0.29,
          "next_predictions": null
        },
        {
          "keyword": "login1.sync",
          "probability": 0.12,
          "next_predictions": null
        }
      ]
    }
  ],
  "context_used": ["login1.login_user", "login1.authenticate"],
  "context_size": 2,
  "full_sequence_length": 2
}
```

### Get Model Information

```bash
GET /model/info
```

**Response:**
```json
{
  "context_size": 2,
  "input_shape": [null, 2],
  "vocab_size": 1234,
  "model_loaded": true
}
```

## 💻 Example Usage

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Predict next keyword (depth: 1, default)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["login1.login_user", "login1.authenticate"],
    "top_k": 3,
    "depth": 1
  }'

# Predict with depth 2 (hierarchical predictions)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["tntmgt1.obtain_tenant", "tntmgt1.get_tenant_username"],
    "top_k": 3,
    "depth": 2
  }'

# Predict with depth 3 (deeper hierarchy)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["login1.login_user", "login1.authenticate"],
    "top_k": 3,
    "depth": 3
  }'
```

**Note:** Make sure there's no trailing comma in the JSON. The last property in the JSON object should not have a comma after it.

### Using Python requests

```python
import requests

# Predict next keywords (depth: 1, default)
response = requests.post(
    "http://localhost:8000/predict",
    json={
        "keywords": ["login1.login_user", "login1.authenticate"],
        "top_k": 3,
        "depth": 1
    }
)

data = response.json()
for pred in data["predictions"]:
    print(f"{pred['keyword']}: {pred['probability']*100:.2f}%")

# Predict with depth 2 (hierarchical)
response = requests.post(
    "http://localhost:8000/predict",
    json={
        "keywords": ["tntmgt1.obtain_tenant", "tntmgt1.get_tenant_username"],
        "top_k": 3,
        "depth": 2
    }
)

data = response.json()

def print_hierarchical(predictions, level=0):
    """Print hierarchical predictions in a tree format."""
    indent = "  " * level
    for pred in predictions:
        print(f"{indent}├─ {pred['keyword']}: {pred['probability']*100:.2f}%")
        if pred.get('next_predictions'):
            print_hierarchical(pred['next_predictions'], level + 1)

print_hierarchical(data["predictions"])
```

### Using the Example Client

```bash
python api_example_client.py
```

## 🔧 Configuration

### Environment Variables

- `MODEL_PATH`: Path to model file (default: `keyword_predictor.keras`)
- `TOKENIZER_PATH`: Path to tokenizer file (default: `tokenizer.json`)

### Command Line Arguments

```bash
python api_keyword_predictor.py --help
```

Options:
- `--host`: Host to bind to (default: `0.0.0.0`)
- `--port`: Port to bind to (default: `8000`)
- `--model`: Path to model file
- `--tokenizer`: Path to tokenizer file
- `--reload`: Enable auto-reload for development

## 📝 Notes

1. **Context Size**: The model uses only the last N keywords (where N = context_size) from your input sequence. This matches how the model was trained.

2. **Sequence Handling**: If you provide more keywords than the context size, only the last N will be used for prediction.

3. **Depth Parameter**: 
   - `depth: 1` (default): Returns only the immediate next predictions (same as original behavior)
   - `depth: 2`: For each top_k prediction, also returns the next top_k predictions
   - `depth: 3+`: Recursively continues deeper, creating a prediction tree
   - Higher depth values require more computation time

4. **Error Handling**: The API returns appropriate HTTP status codes:
   - `200`: Success
   - `400`: Bad request (invalid input, invalid depth, or invalid top_k)
   - `503`: Service unavailable (model not loaded)

5. **CORS**: CORS is enabled for all origins by default. Adjust in production.

6. **JSON Format**: Make sure your JSON is valid - no trailing commas allowed. The last property in a JSON object should not have a comma.

## 🎯 Integration Examples

### JavaScript/TypeScript

```javascript
async function predictNextKeyword(keywords) {
  const response = await fetch('http://localhost:8000/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      keywords: keywords,
      top_k: 3
    })
  });
  
  const data = await response.json();
  return data.predictions;
}

// Usage
const predictions = await predictNextKeyword([
  'login1.login_user',
  'login1.authenticate'
]);
console.log(predictions);
```

### Python

```python
import requests

def predict_next(keywords, top_k=3, depth=1):
    response = requests.post(
        'http://localhost:8000/predict',
        json={'keywords': keywords, 'top_k': top_k, 'depth': depth}
    )
    return response.json()['predictions']

# Usage - depth 1 (flat predictions)
predictions = predict_next(['login1.login_user', 'login1.authenticate'], depth=1)
for pred in predictions:
    print(f"{pred['keyword']}: {pred['probability']*100:.1f}%")

# Usage - depth 2 (hierarchical predictions)
predictions = predict_next(['tntmgt1.obtain_tenant', 'tntmgt1.get_tenant_username'], depth=2)
for pred in predictions:
    print(f"{pred['keyword']}: {pred['probability']*100:.1f}%")
    if pred.get('next_predictions'):
        for next_pred in pred['next_predictions']:
            print(f"  └─ {next_pred['keyword']}: {next_pred['probability']*100:.1f}%")
```

## 🐛 Troubleshooting

1. **Model not loaded**: Check that model and tokenizer files exist
2. **Connection refused**: Make sure the server is running
3. **503 errors**: Model failed to load - check server logs
4. **400 errors**: Invalid input - check your request format
   - **JSON decode error**: Check for trailing commas or invalid JSON syntax
   - **Invalid depth**: Depth must be between 1 and 5
   - **Invalid top_k**: top_k must be between 1 and 10
   - **Empty keywords**: Keywords list cannot be empty

**Common JSON Error Fix:**
```bash
# ❌ Wrong - trailing comma
-d '{
  "keywords": ["keyword1", "keyword2"],
  "top_k": 3,
  "depth": 2,    # <-- Remove this comma!
}'

# ✅ Correct - no trailing comma
-d '{
  "keywords": ["keyword1", "keyword2"],
  "top_k": 3,
  "depth": 2
}'
```


