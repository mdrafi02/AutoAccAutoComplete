#!/usr/bin/env python3
"""
Web Interface for Robot Framework Keyword Recommendation System

This provides a web-based interface for the keyword recommendation system
with real-time autocomplete and intelligent suggestions.
"""

from flask import Flask, render_template, request, jsonify
import json
import sys
import os

# Add parent directory to path to import ml_models
base_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, base_dir)
from ml_models.robot_keyword_recommender import RobotKeywordRecommender

# Configure Flask to find templates and static files in web directory
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
static_dir = os.path.join(os.path.dirname(__file__), 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Global recommender instance
recommender = None

def initialize_recommender():
    """Initialize the recommender with existing model or train on available data."""
    global recommender
    
    # Look for model in data/models directory
    model_file = os.path.join(base_dir, "data", "models", "robot_keyword_model.pkl")
    # Also check for models with .pkl extension in data/models
    models_dir = os.path.join(base_dir, "data", "models")
    
    # Find any existing model file
    model_loaded = False
    try:
        if os.path.exists(model_file):
            print(f"Loading existing model from {model_file}...")
            recommender = RobotKeywordRecommender(model_file)
            print("Model loaded successfully!")
            model_loaded = True
        elif os.path.exists(models_dir):
            # Look for any .pkl file in models directory
            pkl_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
            if pkl_files:
                model_path = os.path.join(models_dir, pkl_files[0])
                print(f"Loading existing model from {model_path}...")
                recommender = RobotKeywordRecommender(model_path)
                print("Model loaded successfully!")
                model_loaded = True
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Will create empty recommender or train from XML files...")
        model_loaded = False
    
    # If model not loaded, try to train from XML files or create empty recommender
    if not model_loaded:
        print("No valid model found. Checking for XML files to train...")
        recommender = RobotKeywordRecommender()
        
        # Look for output.xml files in data/xml_files directory and subdirectories
        xml_dir = os.path.join(base_dir, "data", "xml_files")
        if os.path.exists(xml_dir):
            output_files = []
            # Search in main directory
            for f in os.listdir(xml_dir):
                file_path = os.path.join(xml_dir, f)
                if os.path.isfile(file_path) and f.endswith('.xml'):
                    output_files.append(file_path)
                elif os.path.isdir(file_path):
                    # Search in subdirectories (like CLS_ROBOTS_RBAC_XML_FILES)
                    for sub_file in os.listdir(file_path):
                        sub_file_path = os.path.join(file_path, sub_file)
                        if os.path.isfile(sub_file_path) and sub_file.endswith('.xml'):
                            output_files.append(sub_file_path)
            
            if output_files:
                print(f"Found {len(output_files)} XML files. Training model...")
                print(f"  Files in main directory: {len([f for f in output_files if os.path.dirname(f) == xml_dir])}")
                print(f"  Files in subdirectories: {len([f for f in output_files if os.path.dirname(f) != xml_dir])}")
                try:
                    recommender.train_on_output_files(output_files, model_file)
                    print(f"Model trained and saved to {model_file}")
                except Exception as e:
                    print(f"Error training model: {e}")
                    import traceback
                    traceback.print_exc()
                    print("Continuing with empty recommender...")
            else:
                print("No XML files found in data/xml_files/. Using empty recommender.")
                print("You can add XML files to data/xml_files/ and restart to train the model.")
        else:
            print("No data/xml_files directory found. Using empty recommender.")
            print("You can create data/xml_files/ and add XML files to train the model.")

@app.route('/')
def index():
    """Main page with the recommendation interface."""
    return render_template('index.html')

@app.route('/test')
def test_ui():
    """Simple test UI for keyword recommendations."""
    return render_template('test_ui.html')

@app.route('/editor')
def notepad_editor():
    """Notepad-style editor with autocomplete."""
    return render_template('notepad_editor.html')

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """API endpoint to get keyword recommendations."""
    if not recommender:
        return jsonify({'error': 'Recommender not initialized'}), 500
    
    data = request.get_json()
    current_keyword = data.get('keyword', '')
    context = data.get('context', '')
    max_recommendations = data.get('max_recommendations', 10)
    
    try:
        recommendations = recommender.get_recommendations(
            current_keyword, context, max_recommendations
        )
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/autocomplete', methods=['POST'])
def get_autocomplete():
    """API endpoint to get autocomplete suggestions."""
    if not recommender:
        return jsonify({'error': 'Recommender not initialized'}), 500
    
    data = request.get_json()
    partial_keyword = data.get('keyword', '')
    library_filter = data.get('library', None)
    
    try:
        suggestions = recommender.get_autocomplete(partial_keyword, library_filter)
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/context', methods=['POST'])
def get_context_recommendations():
    """API endpoint to get context-based recommendations."""
    if not recommender:
        return jsonify({'error': 'Recommender not initialized'}), 500
    
    data = request.get_json()
    context_keywords = data.get('keywords', [])
    max_recommendations = data.get('max_recommendations', 10)
    
    try:
        recommendations = recommender.get_context_recommendations(
            context_keywords, max_recommendations
        )
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/popular', methods=['GET'])
def get_popular_keywords():
    """API endpoint to get popular keywords."""
    if not recommender:
        return jsonify({'error': 'Recommender not initialized'}), 500
    
    library = request.args.get('library', None)
    limit = int(request.args.get('limit', 20))
    
    try:
        popular = recommender.get_popular_keywords(library, limit)
        return jsonify({'keywords': popular})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    """API endpoint to get available libraries."""
    if not recommender:
        return jsonify({'error': 'Recommender not initialized'}), 500
    
    try:
        stats = recommender.get_library_statistics()
        libraries = [{'name': lib, 'keyword_count': data['keyword_count']} 
                    for lib, data in stats.items()]
        return jsonify({'libraries': libraries})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """API endpoint to get system statistics."""
    if not recommender:
        return jsonify({'error': 'Recommender not initialized'}), 500
    
    try:
        stats = recommender.get_library_statistics()
        return jsonify({'statistics': stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/next-keywords', methods=['POST'])
def get_next_keywords():
    """
    API endpoint to get next keyword suggestions in library.keyword format.
    Returns top 3 suggestions based on previous keywords context.
    If no previous keywords, returns popular keywords.
    """
    if not recommender:
        return jsonify({'error': 'Recommender not initialized'}), 500
    
    data = request.get_json()
    previous_keywords = data.get('keywords', [])
    max_suggestions = data.get('max', 3)  # Default to 3, but allow override
    
    try:
        suggestions = []
        
        if previous_keywords:
            # Get context-based recommendations
            recommendations = recommender.get_context_recommendations(
                previous_keywords, max_suggestions
            )
            
            # Format as library.keyword
            for rec in recommendations[:max_suggestions]:
                suggestions.append({
                    'keyword': f"{rec['library']}.{rec['keyword']}",
                    'library': rec['library'],
                    'keyword_name': rec['keyword'],
                    'confidence': round(rec['confidence'] * 100, 1),  # As percentage
                    'usage_count': rec['usage_count']
                })
        else:
            # No context, return popular keywords
            popular = recommender.get_popular_keywords(None, max_suggestions)
            for kw_data in popular[:max_suggestions]:
                keyword = kw_data.get('keyword', '')
                library = kw_data.get('library', 'BuiltIn')
                count = kw_data.get('frequency', 0)  # Note: get_popular_keywords returns 'frequency'
                
                suggestions.append({
                    'keyword': f"{library}.{keyword}",
                    'library': library,
                    'keyword_name': keyword,
                    'confidence': 0.0,  # No confidence for popular keywords
                    'usage_count': count
                })
        
        return jsonify({
            'suggestions': suggestions,
            'count': len(suggestions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    initialize_recommender()
    app.run(debug=True, host='0.0.0.0', port=5000)

