# TensorFlow.js Integration Guide

This guide explains how to use the keyword prediction model in JavaScript frontend applications using TensorFlow.js.

## 📋 Prerequisites

1. **Python Environment** (for conversion):
   ```bash
   pip install tensorflowjs
   ```

2. **Web Server** (to serve model files):
   - The model files need to be served via HTTP (not file://)
   - You can use any web server (Python's http.server, Node.js, nginx, etc.)

## 🔄 Step 1: Convert Model to TensorFlow.js Format

Run the conversion script:

```bash
python convert_to_tfjs.py --model keyword_predictor.keras --tokenizer tokenizer.json
```

This will create:
- `tfjs_model/` directory containing the converted model
- `tokenizer_js.json` - JavaScript-compatible tokenizer data

### Options:
```bash
python convert_to_tfjs.py --help

Options:
  --model, -m      Path to Keras model file (default: keyword_predictor.keras)
  --tokenizer, -t  Path to tokenizer JSON file (default: tokenizer.json)
  --output, -o     Output directory for TensorFlow.js model (default: tfjs_model)
  --tokenizer-output  Output path for tokenizer (default: tokenizer_js.json)
```

## 📁 Step 2: Copy Files to Web Server

Copy these files to your web server directory:

```
your_web_server/
├── tfjs_model/
│   ├── model.json
│   └── (weight files)
├── tokenizer_js.json
├── keyword_predictor_tfjs.js
└── (your HTML/JS files)
```

## 💻 Step 3: Use in JavaScript

### Basic Usage

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.15.0/dist/tf.min.js"></script>
    <script src="keyword_predictor_tfjs.js"></script>
</head>
<body>
    <script>
        async function main() {
            // Load model and tokenizer
            const predictor = await KeywordPredictor.load('tfjs_model', 'tokenizer_js.json');
            
            // Predict next keywords (depth 1)
            const predictions = await predictor.predict(
                ['login1.login_user', 'login1.authenticate'],
                3  // top_k
            );
            
            console.log('Predictions:', predictions);
            // Output: [
            //   { keyword: 'login1.logout', probability: 0.652 },
            //   { keyword: 'login1.close_session', probability: 0.301 },
            //   { keyword: 'login1.refresh', probability: 0.185 }
            // ]
            
            // Predict with depth 2 (hierarchical)
            const hierarchical = await predictor.predictWithDepth(
                ['tntmgt1.obtain_tenant', 'tntmgt1.get_tenant_username'],
                3,  // top_k
                2   // depth
            );
            
            console.log('Hierarchical predictions:', hierarchical);
        }
        
        main().catch(console.error);
    </script>
</body>
</html>
```

### Using in Node.js

```javascript
const tf = require('@tensorflow/tfjs-node');
const KeywordPredictor = require('./keyword_predictor_tfjs.js');

async function main() {
    const predictor = await KeywordPredictor.load('tfjs_model', 'tokenizer_js.json');
    const predictions = await predictor.predict(['keyword1', 'keyword2'], 3);
    console.log(predictions);
}
```

### Using in React/Vue/Angular

```javascript
import * as tf from '@tensorflow/tfjs';
import KeywordPredictor from './keyword_predictor_tfjs.js';

// In your component
const [predictor, setPredictor] = useState(null);

useEffect(() => {
    async function loadModel() {
        const model = await KeywordPredictor.load('tfjs_model', 'tokenizer_js.json');
        setPredictor(model);
    }
    loadModel();
}, []);

async function handlePredict(keywords) {
    if (!predictor) return;
    const predictions = await predictor.predictWithDepth(keywords, 3, 2);
    return predictions;
}
```

## 🔧 API Reference

### KeywordPredictor Class

#### `static async load(modelPath, tokenizerPath)`
Load model and tokenizer from files.

**Parameters:**
- `modelPath` (string): Path to TensorFlow.js model directory
- `tokenizerPath` (string): Path to tokenizer JSON file

**Returns:** `Promise<KeywordPredictor>`

#### `async predict(contextKeywords, topK = 3)`
Predict next keyword(s) based on context.

**Parameters:**
- `contextKeywords` (string[]): Array of previous keywords
- `topK` (number): Number of top predictions (default: 3)

**Returns:** `Promise<Array<{keyword: string, probability: number}>>`

#### `async predictWithDepth(contextKeywords, topK = 3, depth = 1)`
Predict with hierarchical depth.

**Parameters:**
- `contextKeywords` (string[]): Array of previous keywords
- `topK` (number): Number of top predictions at each level
- `depth` (number): Number of levels deep (default: 1)

**Returns:** `Promise<Array>` - Hierarchical predictions with `next_predictions` property

#### `getModelInfo()`
Get model metadata.

**Returns:** `Object` with `contextSize`, `vocabSize`, `inputShape`, `outputShape`

#### `dispose()`
Free model memory (call when done).

## 📝 Example: Complete Integration

```javascript
class KeywordAutocomplete {
    constructor() {
        this.predictor = null;
        this.isLoading = false;
    }

    async initialize() {
        try {
            this.isLoading = true;
            this.predictor = await KeywordPredictor.load('tfjs_model', 'tokenizer_js.json');
            console.log('Model loaded:', this.predictor.getModelInfo());
            return true;
        } catch (error) {
            console.error('Failed to load model:', error);
            return false;
        } finally {
            this.isLoading = false;
        }
    }

    async getSuggestions(keywords, topK = 5, depth = 2) {
        if (!this.predictor || this.isLoading) {
            return [];
        }

        try {
            const predictions = await this.predictor.predictWithDepth(
                keywords,
                topK,
                depth
            );
            return predictions;
        } catch (error) {
            console.error('Prediction error:', error);
            return [];
        }
    }

    cleanup() {
        if (this.predictor) {
            this.predictor.dispose();
            this.predictor = null;
        }
    }
}

// Usage
const autocomplete = new KeywordAutocomplete();
await autocomplete.initialize();

// Get suggestions as user types
const suggestions = await autocomplete.getSuggestions(
    ['login1.login_user', 'login1.authenticate'],
    5,
    2
);
```

## 🚀 Quick Start with Demo

1. **Convert the model:**
   ```bash
   python convert_to_tfjs.py
   ```

2. **Start a web server:**
   ```bash
   # Python 3
   python -m http.server 8000
   
   # Or Node.js
   npx http-server -p 8000
   ```

3. **Open the demo:**
   - Navigate to `http://localhost:8000/tfjs_example.html`
   - The model will auto-load
   - Enter keywords and click "Predict Next Keywords"

## ⚠️ Important Notes

1. **CORS**: Model files must be served from the same origin or with proper CORS headers
2. **File Size**: Model files can be large (several MB). Consider:
   - Using model quantization
   - Loading on demand
   - Showing loading progress
3. **Memory**: Dispose of models when done to free memory:
   ```javascript
   predictor.dispose();
   ```
4. **Performance**: Predictions run in the browser. For better performance:
   - Use WebGL backend (automatic in browser)
   - Consider Web Workers for heavy computations
   - Cache predictions when possible

## 🔍 Troubleshooting

### Model not loading
- Check browser console for errors
- Verify model files are accessible via HTTP
- Check CORS headers if loading from different origin

### Predictions are wrong
- Verify tokenizer matches the training tokenizer
- Check that keywords are normalized correctly
- Ensure context size matches model input

### Out of memory errors
- Dispose of old predictions/tensors
- Reduce batch size or depth
- Use `tf.memory()` to check memory usage

## 📚 Additional Resources

- [TensorFlow.js Documentation](https://www.tensorflow.org/js)
- [TensorFlow.js Model Conversion](https://www.tensorflow.org/js/guide/conversion)
- [TensorFlow.js Performance](https://www.tensorflow.org/js/guide/platform_environment)


