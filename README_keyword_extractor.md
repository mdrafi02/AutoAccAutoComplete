# Robot Framework Keyword Extractor

A Python script that reads Robot Framework `output.xml` files and lists all keywords used in the order of execution, including their hierarchy, timing, and status information.

## Features

- **Execution Order**: Lists keywords in the exact order they were executed
- **Hierarchy Support**: Shows keyword nesting levels and parent relationships
- **Detailed Information**: Includes timing, status, arguments, and return values
- **Filtering**: Filter keywords by status (PASS, FAIL, SKIP)
- **Export Support**: Export results to CSV format
- **Command Line Interface**: Easy-to-use CLI with various options

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Usage

### Command Line Interface

```bash
# Basic usage - list all keywords in execution order
python robot_keyword_extractor.py output.xml

# Show detailed information for each keyword
python robot_keyword_extractor.py output.xml -d

# Filter only failed keywords
python robot_keyword_extractor.py output.xml -s FAIL

# Export to CSV file
python robot_keyword_extractor.py output.xml -o keywords.csv

# Combine options
python robot_keyword_extractor.py output.xml -d -s FAIL -o failed_keywords.csv
```

### Command Line Options

- `output_file`: Path to the Robot Framework output.xml file (required)
- `-d, --details`: Show detailed information for each keyword
- `-s, --status`: Filter keywords by status (PASS, FAIL, SKIP)
- `-o, --output`: Export keywords to CSV file
- `-h, --help`: Show help message

### Programmatic Usage

```python
from robot_keyword_extractor import RobotKeywordExtractor

# Initialize extractor
extractor = RobotKeywordExtractor("output.xml")

# Extract keywords
keywords = extractor.extract_keywords()

# Print keywords
extractor.print_keywords(show_details=True)

# Export to CSV
extractor.export_to_csv("keywords.csv")
```

## Output Format

### Basic Output
```
Found 25 keywords in execution order:

================================================================================
  1. Open Browser
  2.   Go To
  3.   Click Element
  4.   Input Text
  5.   Click Button
  6.   Wait Until Element Is Visible
  7.   Get Text
  8. Close Browser
```

### Detailed Output
```
  1. Open Browser
     Type: keyword
     Library: SeleniumLibrary
     Parent: Test Case 1
     Test: Test Case 1
     Status: PASS
     Start: 20240101 10:00:00.000
     End: 20240101 10:00:01.500
     Arguments: http://example.com, chrome
     Returns: 
```

## CSV Export Format

The CSV export includes the following columns:
- `execution_order`: Order of execution (1, 2, 3, ...)
- `name`: Keyword name
- `type`: Keyword type (keyword, setup, teardown, etc.)
- `library`: Library name (empty for built-in keywords)
- `level`: Nesting level (0 for top-level, 1 for nested, etc.)
- `parent`: Parent keyword name
- `test_name`: Test case name
- `status`: Execution status (PASS, FAIL, SKIP)
- `start_time`: Start timestamp
- `end_time`: End timestamp
- `arguments`: Semicolon-separated list of arguments
- `return_values`: Semicolon-separated list of return values

## Examples

### Example 1: Basic Keyword Listing
```bash
python robot_keyword_extractor.py output.xml
```

### Example 2: Find All Failed Keywords
```bash
python robot_keyword_extractor.py output.xml -s FAIL -d
```

### Example 3: Export All Keywords to CSV
```bash
python robot_keyword_extractor.py output.xml -o all_keywords.csv
```

### Example 4: Custom Analysis
```python
from robot_keyword_extractor import RobotKeywordExtractor

extractor = RobotKeywordExtractor("output.xml")
keywords = extractor.extract_keywords()

# Find keywords from specific library
selenium_keywords = [k for k in keywords if k['library'] == 'SeleniumLibrary']
print(f"SeleniumLibrary keywords: {len(selenium_keywords)}")

# Find keywords with arguments
with_args = [k for k in keywords if k['arguments']]
print(f"Keywords with arguments: {len(with_args)}")
```

## Error Handling

The script includes comprehensive error handling for:
- Missing or invalid XML files
- Malformed XML structure
- File access issues
- Missing required elements

## Limitations

- Requires Robot Framework output.xml file (not log.html or report.html)
- Only processes keywords, not test cases or test suites directly
- Timing information depends on Robot Framework version and configuration

## Troubleshooting

### Common Issues

1. **"No robot element found"**: The XML file might not be a valid Robot Framework output file
2. **"File not found"**: Check the path to your output.xml file
3. **"No keywords found"**: The test suite might not contain any keywords or the XML structure is unexpected

### Debug Tips

- Use `-d` flag to see detailed information about each keyword
- Check that your output.xml file is from a recent Robot Framework run
- Verify the XML file is not corrupted by opening it in a text editor

## License

This script is provided as-is for educational and testing purposes.
