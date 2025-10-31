#!/usr/bin/env python3
"""
Web Interface for Robot Framework Keyword Recommendation System

This provides a web-based interface for the keyword recommendation system
with real-time autocomplete and intelligent suggestions.
"""

from flask import Flask, render_template, request, jsonify
import json
from robot_keyword_recommender import RobotKeywordRecommender
import os

app = Flask(__name__)

# Global recommender instance
recommender = None

def initialize_recommender():
    """Initialize the recommender with existing model or train on available data."""
    global recommender
    
    model_file = "robot_keyword_model.pkl"
    
    if os.path.exists(model_file):
        print("Loading existing model...")
        recommender = RobotKeywordRecommender(model_file)
    else:
        print("No existing model found. Training on available data...")
        recommender = RobotKeywordRecommender()
        
        # Look for output.xml files in current directory
        output_files = []
        for file in os.listdir('.'):
            if file.endswith('output.xml'):
                output_files.append(file)
        
        if output_files:
            recommender.train_on_output_files(output_files, model_file)
        else:
            print("No output.xml files found. Please train the model first.")
            recommender = RobotKeywordRecommender()

@app.route('/')
def index():
    """Main page with the recommendation interface."""
    return render_template('index.html')

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

if __name__ == '__main__':
    initialize_recommender()
    app.run(debug=True, host='0.0.0.0', port=5000)

