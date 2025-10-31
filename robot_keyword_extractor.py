#!/usr/bin/env python3
"""
Robot Framework Keyword Extractor

This script reads a Robot Framework output.xml file and lists all keywords
used in the order of execution, including their hierarchy and timing information.
"""

import xml.etree.ElementTree as ET
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any


class RobotKeywordExtractor:
    """Extracts and processes keywords from Robot Framework output.xml files."""
    
    def __init__(self, output_file: str):
        """Initialize the extractor with the output.xml file path."""
        self.output_file = output_file
        self.keywords = []
        
    def parse_xml(self) -> ET.Element:
        """Parse the XML file and return the root element."""
        try:
            tree = ET.parse(self.output_file)
            return tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File '{self.output_file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    
    def extract_keywords_recursive(self, element: ET.Element, level: int = 0, 
                                 parent_name: str = "", test_name: str = "") -> None:
        """
        Recursively extract keywords from XML elements.
        
        Args:
            element: XML element to process
            level: Current nesting level
            parent_name: Name of parent element
            test_name: Name of the test case
        """
        # Check if this is a keyword element
        if element.tag == 'kw':
            keyword_name = element.get('name', 'Unknown')
            keyword_type = element.get('type', 'keyword')
            keyword_library = element.get('library', '')
            
            # Extract timing information
            start_time = element.get('starttime', '')
            end_time = element.get('endtime', '')
            
            # Extract status
            status_elem = element.find('status')
            status = status_elem.get('status', 'UNKNOWN') if status_elem is not None else 'UNKNOWN'
            
            # Extract arguments
            arguments = []
            args_elem = element.find('arguments')
            if args_elem is not None:
                for arg in args_elem.findall('arg'):
                    arguments.append(arg.text or '')
            
            # Extract return values
            return_values = []
            return_elem = element.find('return')
            if return_elem is not None:
                for ret in return_elem.findall('return'):
                    return_values.append(ret.text or '')
            
            # Store keyword information
            keyword_info = {
                'name': keyword_name,
                'type': keyword_type,
                'library': keyword_library,
                'level': level,
                'parent': parent_name,
                'test_name': test_name,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'arguments': arguments,
                'return_values': return_values,
                'execution_order': len(self.keywords) + 1
            }
            
            self.keywords.append(keyword_info)
            
            # Update parent name for nested keywords
            current_parent = f"{parent_name}.{keyword_name}" if parent_name else keyword_name
        
        # Check if this is a test case
        elif element.tag == 'test':
            test_name = element.get('name', 'Unknown Test')
            current_parent = test_name
        
        # Recursively process child elements
        for child in element:
            if element.tag == 'test':
                self.extract_keywords_recursive(child, level, current_parent, test_name)
            elif element.tag == 'kw':
                self.extract_keywords_recursive(child, level + 1, current_parent, test_name)
            else:
                self.extract_keywords_recursive(child, level, parent_name, test_name)
    
    def extract_keywords(self) -> List[Dict[str, Any]]:
        """Extract all keywords from the output.xml file."""
        root = self.parse_xml()
        
        # Check if root is robot element or find robot element
        if root.tag == 'robot':
            robot_elem = root
        else:
            robot_elem = root.find('.//robot')
            if robot_elem is None:
                print("Error: No robot element found in the XML file.")
                sys.exit(1)
        
        # Extract keywords from all test suites
        for suite in robot_elem.findall('.//suite'):
            self.extract_keywords_recursive(suite)
        
        return self.keywords
    
    def print_keywords(self, show_details: bool = False, filter_status: str = None) -> None:
        """Print the extracted keywords in execution order."""
        if not self.keywords:
            print("No keywords found in the output file.")
            return
        
        print(f"\nFound {len(self.keywords)} keywords in execution order:\n")
        print("=" * 80)
        
        for i, keyword in enumerate(self.keywords, 1):
            # Filter by status if specified
            if filter_status and keyword['status'].upper() != filter_status.upper():
                continue
            
            # Basic information
            indent = "  " * keyword['level']
            print(f"{i:3d}. {indent}{keyword['name']}")
            
            if show_details:
                print(f"     Type: {keyword['type']}")
                if keyword['library']:
                    print(f"     Library: {keyword['library']}")
                if keyword['parent']:
                    print(f"     Parent: {keyword['parent']}")
                if keyword['test_name']:
                    print(f"     Test: {keyword['test_name']}")
                print(f"     Status: {keyword['status']}")
                if keyword['start_time']:
                    print(f"     Start: {keyword['start_time']}")
                if keyword['end_time']:
                    print(f"     End: {keyword['end_time']}")
                if keyword['arguments']:
                    print(f"     Arguments: {', '.join(keyword['arguments'])}")
                if keyword['return_values']:
                    print(f"     Returns: {', '.join(keyword['return_values'])}")
                print()
    
    def export_to_csv(self, output_file: str) -> None:
        """Export keywords to CSV file."""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['execution_order', 'name', 'type', 'library', 'level', 
                         'parent', 'test_name', 'status', 'start_time', 'end_time', 
                         'arguments', 'return_values']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for keyword in self.keywords:
                # Convert lists to strings for CSV
                keyword_copy = keyword.copy()
                keyword_copy['arguments'] = '; '.join(keyword['arguments'])
                keyword_copy['return_values'] = '; '.join(keyword['return_values'])
                writer.writerow(keyword_copy)
        
        print(f"Keywords exported to {output_file}")


def main():
    """Main function to run the keyword extractor."""
    parser = argparse.ArgumentParser(
        description="Extract Robot Framework keywords from output.xml in execution order"
    )
    parser.add_argument(
        'output_file',
        help='Path to the Robot Framework output.xml file'
    )
    parser.add_argument(
        '-d', '--details',
        action='store_true',
        help='Show detailed information for each keyword'
    )
    parser.add_argument(
        '-s', '--status',
        choices=['PASS', 'FAIL', 'SKIP'],
        help='Filter keywords by status (PASS, FAIL, SKIP)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Export keywords to CSV file'
    )
    
    args = parser.parse_args()
    
    # Create extractor and process the file
    extractor = RobotKeywordExtractor(args.output_file)
    extractor.extract_keywords()
    
    # Print results
    extractor.print_keywords(show_details=args.details, filter_status=args.status)
    
    # Export to CSV if requested
    if args.output:
        extractor.export_to_csv(args.output)
    
    # Print summary
    total_keywords = len(extractor.keywords)
    if args.status:
        filtered_count = len([k for k in extractor.keywords 
                            if k['status'].upper() == args.status.upper()])
        print(f"\nSummary: {filtered_count} keywords with status '{args.status}' out of {total_keywords} total keywords.")
    else:
        print(f"\nSummary: {total_keywords} keywords found in execution order.")


if __name__ == "__main__":
    main()
