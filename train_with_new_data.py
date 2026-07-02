#!/usr/bin/env python3
"""
Train model with new XML files from CLS_ROBOTS_RBAC_XML_FILES directory.

This script trains the model on all XML files including the new RBAC XML files.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_models.robot_keyword_recommender import RobotKeywordRecommender

def main():
    print("=" * 80)
    print("Training Robot Framework Keyword Recommendation Model")
    print("=" * 80)
    
    # Initialize recommender
    recommender = RobotKeywordRecommender()
    
    # Find all XML files in data/xml_files and subdirectories
    xml_dir = os.path.join("data", "xml_files")
    output_files = []
    
    if os.path.exists(xml_dir):
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
    
    if not output_files:
        print("ERROR: No XML files found!")
        print(f"Please add XML files to {xml_dir} or its subdirectories.")
        sys.exit(1)
    
    # Count files by location
    main_dir_files = [f for f in output_files if os.path.dirname(f) == xml_dir]
    subdir_files = [f for f in output_files if os.path.dirname(f) != xml_dir]
    
    print(f"\nFound {len(output_files)} XML files:")
    print(f"  - Main directory: {len(main_dir_files)} files")
    print(f"  - Subdirectories: {len(subdir_files)} files")
    if subdir_files:
        subdirs = set(os.path.dirname(f) for f in subdir_files)
        for subdir in subdirs:
            count = len([f for f in subdir_files if os.path.dirname(f) == subdir])
            print(f"    - {subdir}: {count} files")
    
    # Model file path
    model_file = os.path.join("data", "models", "robot_keyword_model.pkl")
    os.makedirs(os.path.dirname(model_file), exist_ok=True)
    
    print(f"\nTraining model on {len(output_files)} XML files...")
    print(f"Model will be saved to: {model_file}")
    print("=" * 80)
    
    try:
        # Train the model
        recommender.train_on_output_files(output_files, model_file)
        
        print("\n" + "=" * 80)
        print("Training completed successfully!")
        print("=" * 80)
        
        # Show statistics
        analyzer = recommender.analyzer
        print(f"\nModel Statistics:")
        print(f"  - Total keyword sequences analyzed: {len(analyzer.keyword_sequences)}")
        print(f"  - Unique keywords: {len(analyzer.keyword_frequencies)}")
        print(f"  - Keyword transitions: {len(analyzer.keyword_transitions)}")
        print(f"  - Libraries: {len(analyzer.library_keywords)}")
        
        # Show top keywords
        print(f"\nTop 10 Most Used Keywords:")
        for keyword, count in analyzer.keyword_frequencies.most_common(10):
            library = analyzer.keyword_libraries.get(keyword, 'BuiltIn')
            print(f"  {count:5d}x - {library}.{keyword}")
        
        # Show top libraries
        print(f"\nTop Libraries by Keyword Count:")
        library_counts = {lib: len(keywords) for lib, keywords in analyzer.library_keywords.items()}
        for library, count in sorted(library_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {count:4d} keywords - {library}")
        
        print(f"\n✅ Model saved to: {model_file}")
        print(f"\nYou can now:")
        print(f"  1. Restart the web server: python3 web/web_recommender.py")
        print(f"  2. Test the model via API: curl -X POST http://localhost:5000/api/next-keywords \\")
        print(f"     -H 'Content-Type: application/json' -d '{{\"keywords\": [\"Log To Console\"], \"max\": 3}}'")
        
    except Exception as e:
        print(f"\n❌ ERROR during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

