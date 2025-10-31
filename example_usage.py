#!/usr/bin/env python3
"""
Example usage of the Robot Framework Keyword Extractor

This script demonstrates how to use the RobotKeywordExtractor class
to extract keywords from a Robot Framework output.xml file.
"""

from robot_keyword_extractor import RobotKeywordExtractor


def example_basic_usage():
    """Example of basic usage to extract keywords."""
    print("=== Basic Usage Example ===")
    
    # Initialize the extractor with your output.xml file
    extractor = RobotKeywordExtractor("output.xml")
    
    # Extract keywords
    keywords = extractor.extract_keywords()
    
    # Print keywords in execution order
    extractor.print_keywords()


def example_detailed_usage():
    """Example of detailed usage with filtering."""
    print("\n=== Detailed Usage Example ===")
    
    # Initialize the extractor
    extractor = RobotKeywordExtractor("output.xml")
    
    # Extract keywords
    extractor.extract_keywords()
    
    # Print only failed keywords with details
    print("Failed keywords only:")
    extractor.print_keywords(show_details=True, filter_status="FAIL")
    
    # Export to CSV
    extractor.export_to_csv("keywords_export.csv")


def example_custom_processing():
    """Example of custom processing of extracted keywords."""
    print("\n=== Custom Processing Example ===")
    
    # Initialize and extract
    extractor = RobotKeywordExtractor("output.xml")
    keywords = extractor.extract_keywords()
    
    # Custom analysis
    print(f"Total keywords found: {len(keywords)}")
    
    # Group by library
    libraries = {}
    for keyword in keywords:
        lib = keyword['library'] or 'BuiltIn'
        if lib not in libraries:
            libraries[lib] = 0
        libraries[lib] += 1
    
    print("\nKeywords by library:")
    for lib, count in sorted(libraries.items()):
        print(f"  {lib}: {count} keywords")
    
    # Find keywords with arguments
    with_args = [k for k in keywords if k['arguments']]
    print(f"\nKeywords with arguments: {len(with_args)}")
    
    # Find the most nested keyword
    max_level = max(keyword['level'] for keyword in keywords)
    nested_keywords = [k for k in keywords if k['level'] == max_level]
    print(f"\nMost nested keywords (level {max_level}):")
    for keyword in nested_keywords[:5]:  # Show first 5
        indent = "  " * keyword['level']
        print(f"  {indent}{keyword['name']}")


if __name__ == "__main__":
    print("Robot Framework Keyword Extractor - Usage Examples")
    print("=" * 50)
    
    # Run examples (uncomment the ones you want to test)
    # example_basic_usage()
    # example_detailed_usage()
    # example_custom_processing()
    
    print("\nTo use this script:")
    print("1. Place your Robot Framework output.xml file in the same directory")
    print("2. Uncomment the example functions you want to run")
    print("3. Run: python example_usage.py")
    print("\nOr use the command line interface:")
    print("python robot_keyword_extractor.py output.xml -d")
