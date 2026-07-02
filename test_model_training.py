#!/usr/bin/env python3
"""
Quick test script to verify XML files can be processed and model can be trained.
Tests with a small subset first.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_models.robot_keyword_recommender import RobotKeywordRecommender


def find_xml_files(xml_dir):
    """Find all XML files in xml_dir and one level of subdirectories."""
    output_files = []
    if not os.path.exists(xml_dir):
        return output_files

    for f in os.listdir(xml_dir):
        file_path = os.path.join(xml_dir, f)
        if os.path.isfile(file_path) and f.endswith('.xml'):
            output_files.append(file_path)
        elif os.path.isdir(file_path):
            for sub_file in os.listdir(file_path):
                sub_file_path = os.path.join(file_path, sub_file)
                if os.path.isfile(sub_file_path) and sub_file.endswith('.xml'):
                    output_files.append(sub_file_path)
    return output_files


def main():
    print("Testing model training with sample XML files...")

    xml_dir = os.path.join("data", "xml_files")
    all_xml_files = find_xml_files(xml_dir)

    if not all_xml_files:
        print(f"ERROR: No XML files found in {xml_dir}")
        return

    print(f"\nFound {len(all_xml_files)} total XML files in {xml_dir}")

    xml_files = all_xml_files[:5]
    print(f"Testing with {len(xml_files)} sample files:")
    for f in xml_files:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"  - {os.path.basename(f)} ({size_mb:.1f} MB)")

    recommender = RobotKeywordRecommender()

    print("\nTraining on sample files...")
    try:
        recommender.train_on_output_files(xml_files, "data/models/test_model.pkl")

        analyzer = recommender.analyzer
        print("\nTest successful!")
        print(f"  - Sequences analyzed: {len(analyzer.keyword_sequences)}")
        print(f"  - Unique keywords: {len(analyzer.keyword_frequencies)}")
        print(f"  - Libraries: {len(analyzer.library_keywords)}")

        print("\nTop 5 keywords from test:")
        for kw, count in analyzer.keyword_frequencies.most_common(5):
            lib = analyzer.keyword_libraries.get(kw, 'BuiltIn')
            print(f"  {lib}.{kw} ({count}x)")

        print(f"\nReady to train on all {len(all_xml_files)} files!")
        print("Run: python3 train_with_new_data.py")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
