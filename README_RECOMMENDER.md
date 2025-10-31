# Robot Framework Keyword Recommendation System

An intelligent recommendation system for Robot Framework keywords with autocomplete functionality, designed to speed up test case creation in browser-based test creation tools.

## Features

- **Autocomplete**: Real-time keyword suggestions as you type
- **Intelligent Recommendations**: Next keyword suggestions based on usage patterns
- **Context-Aware**: Recommendations based on previous keywords in the sequence
- **Pattern Analysis**: Learns from Robot Framework output.xml files
- **Web Interface**: Beautiful, modern web UI for easy integration
- **API Endpoints**: RESTful API for integration with existing tools

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Train the Model

First, train the recommendation system on your Robot Framework test outputs:

```bash
# Train on one or more output.xml or log.html files
python robot_keyword_recommender.py --train output.xml --save-model robot_keyword_model.pkl

# Train on multiple files (mix of XML and HTML)
python robot_keyword_recommender.py --train output1.xml log.html output2.xml --save-model robot_keyword_model.pkl
```

### 2. Start the Web Interface

```bash
python web_recommender.py
```

Then open your browser to `http://localhost:5000` to use the recommendation interface.

### 3. Use the Command Line Interface

```bash
# Get recommendations for a keyword
python robot_keyword_recommender.py --model robot_keyword_model.pkl --recommend "Login SCG System"

# Get autocomplete suggestions
python robot_keyword_recommender.py --model robot_keyword_model.pkl --autocomplete "Login"

# Get context-based recommendations
python robot_keyword_recommender.py --model robot_keyword_model.pkl --context "Login SCG System" "Create Dictionary"

# Get popular keywords from a library
python robot_keyword_recommender.py --model robot_keyword_model.pkl --popular "BuiltIn"

# View library statistics
python robot_keyword_recommender.py --model robot_keyword_model.pkl --stats
```

## API Usage

The web interface provides RESTful API endpoints that can be integrated into your test creation tool:

### Get Recommendations

```bash
POST /api/recommend
Content-Type: application/json

{
  "keyword": "Login SCG System",
  "context": "Optional context string",
  "max_recommendations": 10
}
```

### Get Autocomplete Suggestions

```bash
POST /api/autocomplete
Content-Type: application/json

{
  "keyword": "Login",
  "library": "optional_library_filter"
}
```

### Get Context-Based Recommendations

```bash
POST /api/context
Content-Type: application/json

{
  "keywords": ["Login SCG System", "Create Dictionary"],
  "max_recommendations": 10
}
```

### Get Popular Keywords

```bash
GET /api/popular?library=BuiltIn&limit=20
```

### Get Available Libraries

```bash
GET /api/libraries
```

### Get Statistics

```bash
GET /api/stats
```

## Integration with Test Creation Tool

To integrate this into your browser-based test creation tool:

### Option 1: Direct API Integration

```javascript
// Autocomplete example
async function getAutocompleteSuggestions(partialKeyword) {
    const response = await fetch('http://localhost:5000/api/autocomplete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keyword: partialKeyword })
    });
    const data = await response.json();
    return data.suggestions;
}

// Recommendations example
async function getRecommendations(currentKeyword, context) {
    const response = await fetch('http://localhost:5000/api/recommend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            keyword: currentKeyword,
            context: context,
            max_recommendations: 10
        })
    });
    const data = await response.json();
    return data.recommendations;
}
```

### Option 2: Embed the Web Interface

You can embed the web interface in an iframe or integrate it directly into your tool's UI.

### Option 3: Use as a Browser Extension

The API can be accessed from a browser extension to provide autocomplete functionality directly in your test creation tool.

## How It Works

1. **Pattern Analysis**: The system analyzes Robot Framework `output.xml` files to extract:
   - Keyword execution sequences
   - Transition patterns (which keywords follow which)
   - Context information (parent-child relationships)
   - Library usage patterns
   - Keyword frequencies

2. **Recommendation Engine**: 
   - Uses transition probabilities to suggest likely next keywords
   - Considers context (previous keywords) for more accurate suggestions
   - Filters by library when appropriate
   - Provides confidence scores based on usage frequency

3. **Autocomplete**:
   - Fuzzy matching for partial keyword input
   - Filters by library if specified
   - Sorts by frequency and relevance
   - Provides real-time suggestions

## Training Tips

- **More Data = Better Results**: Train on multiple output files from different test suites for better coverage
- **Update Regularly**: Retrain when adding new keywords or test patterns
- **Filter by Domain**: Consider creating separate models for different test domains if they have very different patterns

## File Structure

```
.
├── robot_keyword_extractor.py      # Extracts keywords from output.xml
├── robot_keyword_recommender.py    # Core recommendation engine
├── web_recommender.py              # Web interface (Flask)
├── templates/
│   └── index.html                  # Web UI
├── requirements.txt                # Python dependencies
└── robot_keyword_model.pkl         # Trained model (generated)
```

## Performance

- **Training**: Processes ~2000 keywords in < 5 seconds
- **Recommendations**: Returns results in < 100ms
- **Autocomplete**: Real-time suggestions with < 300ms debounce

## Future Enhancements

- [ ] Keyword argument suggestions
- [ ] Test case template recommendations
- [ ] Integration with Robot Framework documentation
- [ ] Machine learning model for improved accuracy
- [ ] Multi-user collaborative filtering
- [ ] Keyword usage analytics dashboard

## License

This tool is provided as-is for improving Robot Framework test creation efficiency.
