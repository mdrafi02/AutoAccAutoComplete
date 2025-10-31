#!/usr/bin/env python3
"""
Robot Framework log.html Parser

Parses Robot Framework log.html files to extract keywords in execution order.
The log.html file contains JavaScript-embedded data that we can extract.
"""

import re
import json
import sys
from typing import List, Dict, Any, Optional
from collections import deque


class LogHTMLExtractor:
    """Extracts keywords from Robot Framework log.html files."""
    
    def __init__(self, log_file: str):
        """Initialize the extractor with the log.html file path."""
        self.log_file = log_file
        self.keywords = []
        self.execution_order = 0
        
    def parse_file(self):
        """Parse the log.html file."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File '{self.log_file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
        
        # Extract keywords from HTML content
        self.extract_from_html_content(content)
    
    def extract_from_html_content(self, content: str):
        """Extract keywords directly from HTML content."""
        # Robot Framework log.html contains JavaScript data in script tags
        # Look for various patterns
        
        # Pattern 1: var output = {...};
        pattern1 = r'var\s+output\s*=\s*(\{.*?"robot".*?\});'
        match = re.search(pattern1, content, re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                json_str = self.clean_json_string(json_str)
                data = json.loads(json_str)
                self.process_robot_data(data)
                return
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Pattern 2: Look for any JSON object with "robot" key
        pattern2 = r'(\{\s*"robot":\s*\{[^}]*\}(?:\s*,\s*"[^"]+":\s*[^}]+)*\})'
        matches = re.finditer(pattern2, content, re.DOTALL)
        for match in matches:
            try:
                json_str = self.clean_json_string(match.group(1))
                data = json.loads(json_str)
                if 'robot' in data:
                    self.process_robot_data(data)
                    return
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Pattern 3: Try to find JSON in script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        script_matches = re.finditer(script_pattern, content, re.DOTALL | re.IGNORECASE)
        for script_match in script_matches:
            script_content = script_match.group(1)
            # Look for JSON-like structures
            json_pattern = r'(\{[^{}]*"robot"[^{}]*\{[^{}]*\}[^{}]*\})'
            json_matches = re.finditer(json_pattern, script_content, re.DOTALL)
            for json_match in json_matches:
                try:
                    json_str = self.clean_json_string(json_match.group(1))
                    data = json.loads(json_str)
                    if 'robot' in data:
                        self.process_robot_data(data)
                        return
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Fallback: Try to extract from table structure
        if not self.keywords:
            self.extract_from_html_tables(content)
    
    def clean_json_string(self, json_str: str) -> str:
        """Clean JavaScript/JSON string to make it valid JSON."""
        # Remove JavaScript comments
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Fix trailing commas (common in JavaScript but not valid JSON)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Remove any leading/trailing whitespace
        json_str = json_str.strip()
        
        return json_str
    
    def process_robot_data(self, data: dict):
        """Process Robot Framework data structure."""
        if 'robot' not in data:
            return
        
        robot_data = data['robot']
        
        # Extract suites and their keywords
        if 'suite' in robot_data:
            suites = robot_data['suite'] if isinstance(robot_data['suite'], list) else [robot_data['suite']]
            for suite in suites:
                self.extract_from_suite(suite)
    
    def extract_from_suite(self, suite: dict, parent_name: str = "", level: int = 0, test_name: str = ""):
        """Recursively extract keywords from a test suite."""
        # Extract keywords from suite
        if 'kw' in suite:
            keywords = suite['kw'] if isinstance(suite['kw'], list) else [suite['kw']]
            for kw in keywords:
                self.extract_keyword(kw, parent_name, level, test_name)
        
        # Extract test cases
        if 'test' in suite:
            tests = suite['test'] if isinstance(suite['test'], list) else [suite['test']]
            for test in tests:
                test_name = test.get('name', 'Unknown Test')
                if 'kw' in test:
                    keywords = test['kw'] if isinstance(test['kw'], list) else [test['kw']]
                    for kw in keywords:
                        self.extract_keyword(kw, parent_name, level, test_name)
        
        # Recursively process nested suites
        if 'suite' in suite:
            nested_suites = suite['suite'] if isinstance(suite['suite'], list) else [suite['suite']]
            for nested_suite in nested_suites:
                self.extract_from_suite(nested_suite, parent_name, level, test_name)
    
    def extract_keyword(self, kw: dict, parent_name: str, level: int, test_name: str):
        """Extract keyword information from a keyword dictionary."""
        keyword_name = kw.get('name', 'Unknown')
        keyword_type = kw.get('type', 'keyword')
        
        # Extract library information
        library = ''
        if 'libname' in kw:
            library = kw['libname']
        
        # Extract status
        status = 'UNKNOWN'
        if 'status' in kw:
            status_info = kw['status']
            if isinstance(status_info, dict):
                status = status_info.get('status', 'UNKNOWN')
        
        # Extract timing
        start_time = ''
        end_time = ''
        if 'starttime' in kw:
            start_time = kw['starttime']
        if 'endtime' in kw:
            end_time = kw['endtime']
        
        # Extract arguments
        arguments = []
        if 'arguments' in kw:
            if isinstance(kw['arguments'], list):
                arguments = [str(arg) for arg in kw['arguments']]
            else:
                arguments = [str(kw['arguments'])]
        
        # Build parent chain
        current_parent = f"{parent_name}.{keyword_name}" if parent_name else keyword_name
        
        # Store keyword information
        self.execution_order += 1
        keyword_info = {
            'name': keyword_name,
            'type': keyword_type,
            'library': library,
            'level': level,
            'parent': parent_name,
            'test_name': test_name,
            'start_time': start_time,
            'end_time': end_time,
            'status': status,
            'arguments': arguments,
            'return_values': [],
            'execution_order': self.execution_order
        }
        
        self.keywords.append(keyword_info)
        
        # Recursively process nested keywords
        if 'kw' in kw:
            nested_keywords = kw['kw'] if isinstance(kw['kw'], list) else [kw['kw']]
            for nested_kw in nested_keywords:
                self.extract_keyword(nested_kw, current_parent, level + 1, test_name)
    
    def extract_from_html_tables(self, content: str):
        """Fallback method: Extract keywords from HTML table structure."""
        # This is a simpler fallback that looks for keyword patterns in HTML
        # Robot Framework log.html has keywords in expandable rows
        
        # Pattern for keyword rows: class="kw" or data-type="keyword"
        keyword_pattern = r'<tr[^>]*(?:class|data-type)="kw"[^>]*>.*?<td[^>]*>.*?<a[^>]*>(.*?)</a>.*?</tr>'
        matches = re.finditer(keyword_pattern, content, re.DOTALL | re.IGNORECASE)
        
        level_stack = [0]
        parent_stack = ['']
        
        for match in matches:
            keyword_name = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            
            if keyword_name:
                self.execution_order += 1
                keyword_info = {
                    'name': keyword_name,
                    'type': 'keyword',
                    'library': '',
                    'level': level_stack[-1],
                    'parent': parent_stack[-1],
                    'test_name': '',
                    'start_time': '',
                    'end_time': '',
                    'status': 'UNKNOWN',
                    'arguments': [],
                    'return_values': [],
                    'execution_order': self.execution_order
                }
                self.keywords.append(keyword_info)
    
    def extract_keywords(self) -> List[Dict[str, Any]]:
        """Extract all keywords from the log.html file."""
        self.parse_file()
        return self.keywords
    
    def print_keywords(self, show_details: bool = False, filter_status: str = None):
        """Print the extracted keywords in execution order."""
        if not self.keywords:
            print("No keywords found in the log.html file.")
            return
        
        filtered_keywords = self.keywords
        if filter_status:
            filtered_keywords = [k for k in self.keywords 
                               if k['status'].upper() == filter_status.upper()]
        
        print(f"\nFound {len(filtered_keywords)} keywords in execution order:\n")
        print("=" * 80)
        
        for i, keyword in enumerate(filtered_keywords, 1):
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
                print()
    
    def export_to_csv(self, output_file: str):
        """Export keywords to CSV file."""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['execution_order', 'name', 'type', 'library', 'level', 
                         'parent', 'test_name', 'status', 'start_time', 'end_time', 
                         'arguments', 'return_values']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for keyword in self.keywords:
                keyword_copy = keyword.copy()
                keyword_copy['arguments'] = '; '.join(keyword['arguments'])
                keyword_copy['return_values'] = '; '.join(keyword['return_values'])
                writer.writerow(keyword_copy)
        
        print(f"Keywords exported to {output_file}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract Robot Framework keywords from log.html in execution order"
    )
    parser.add_argument(
        'log_file',
        help='Path to the Robot Framework log.html file'
    )
    parser.add_argument(
        '-d', '--details',
        action='store_true',
        help='Show detailed information for each keyword'
    )
    parser.add_argument(
        '-s', '--status',
        choices=['PASS', 'FAIL', 'SKIP'],
        help='Filter keywords by status'
    )
    parser.add_argument(
        '-o', '--output',
        help='Export keywords to CSV file'
    )
    
    args = parser.parse_args()
    
    extractor = LogHTMLExtractor(args.log_file)
    extractor.extract_keywords()
    
    extractor.print_keywords(show_details=args.details, filter_status=args.status)
    
    if args.output:
        extractor.export_to_csv(args.output)
    
    print(f"\nSummary: {len(extractor.keywords)} keywords found in execution order.")


if __name__ == "__main__":
    main()
