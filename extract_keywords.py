import json
import argparse
import re
import os
from pathlib import Path
from xml.etree import ElementTree as ET


def normalize_keyword(keyword_name, library_name):
    """Normalize keyword name and create full keyword with library prefix."""
    if not keyword_name:
        return None
    # Replace one or more whitespace characters with a single underscore
    keyword_name = re.sub(r"\s+", "_", keyword_name.lower().strip())
    if library_name:
        library_name = library_name.lower().strip()
        full_keyword = f"{library_name}.{keyword_name}"
    else:
        full_keyword = keyword_name
    return full_keyword


def extract_keywords_from_output(xml_path):
    """Extract test names and their keyword sequences from Robot Framework output.xml.

    Includes suite setup keywords at the beginning and suite teardown keywords at the end
    of each test case sequence.

    Uses streaming XML parsing for memory efficiency.

    Args:
        xml_path: Path to Robot Framework output.xml file

    Returns:
        Tuple of (list of dicts with 'test_name' and 'keywords' keys, metadata dict)
        Metadata contains: {'has_suite_setup': bool, 'has_suite_teardown': bool}
    """
    test_data = []
    # Store tests temporarily per suite so we can add suite teardown later
    suite_tests_map = {}  # Maps suite_id -> [list of test dicts]
    current_test_name = None
    keyword_sequence = []

    # Suite-level keywords (persist across all tests in the suite)
    # Use a dict to track suite keywords per suite (in case of nested suites)
    suite_keywords_map = {}  # Maps suite_id -> {"setup": [...], "teardown": [...]}
    current_suite_id = None

    # Track if we're inside suite setup/teardown (NOT test setup/teardown)
    in_suite_setup = False
    in_suite_teardown = False
    suite_setup_depth = 0
    suite_teardown_depth = 0
    current_suite_setup_keywords = []
    current_suite_teardown_keywords = []
    suite_setup_keyword_name = None  # Track the suite setup keyword name
    suite_teardown_keyword_name = None  # Track the suite teardown keyword name

    # Track if we're inside test setup/teardown (part of test keywords)
    in_test_setup = False
    in_test_teardown = False
    test_setup_depth = 0
    test_teardown_depth = 0

    # Check if file exists before parsing
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    try:
        # Use iterparse with optimized memory management
        for event, element in ET.iterparse(xml_path, events=("start", "end")):
            if event == "start":
                if element.tag == "suite":
                    # New suite - track suite ID and initialize keywords
                    current_suite_id = element.attrib.get(
                        "id", f"suite_{len(suite_keywords_map)}"
                    )
                    if current_suite_id not in suite_keywords_map:
                        suite_keywords_map[current_suite_id] = {
                            "setup": [],
                            "teardown": [],
                        }
                elif element.tag == "test":
                    current_test_name = element.attrib.get("name", "UnnamedTest")
                    keyword_sequence = []
                    # Reset test-level setup/teardown tracking for new test
                    in_test_setup = False
                    in_test_teardown = False
                    test_setup_depth = 0
                    test_teardown_depth = 0
                elif element.tag == "kw":
                    keyword_name = element.attrib.get("name", "")
                    library_name = element.attrib.get("library")
                    kw_type = element.attrib.get("type", "").upper()
                    normalized_name = keyword_name.lower().strip()

                    # Distinguish between suite-level and test-level setup/teardown
                    # Detection is GENERIC - based only on type attribute and context, NOT keyword names
                    # Suite setup/teardown: type="SETUP"/"TEARDOWN" AND NOT inside a test
                    # Test setup/teardown: type="SETUP"/"TEARDOWN" AND inside a test
                    # Only detect suite setup/teardown if we're not already inside one
                    is_suite_setup = (
                        not in_suite_setup
                        and not in_suite_teardown
                        and kw_type == "SETUP"
                        and not current_test_name
                    )
                    is_suite_teardown = (
                        not in_suite_setup
                        and not in_suite_teardown
                        and kw_type == "TEARDOWN"
                        and not current_test_name
                    )
                    is_test_setup = (
                        kw_type == "SETUP"
                        and current_test_name
                        and not in_test_setup
                        and not in_test_teardown
                    )
                    is_test_teardown = (
                        kw_type == "TEARDOWN"
                        and current_test_name
                        and not in_test_setup
                        and not in_test_teardown
                    )

                    if is_suite_setup:
                        # Suite-level setup (applies to all tests in suite)
                        in_suite_setup = True
                        suite_setup_depth = 0
                        current_suite_setup_keywords = []
                        suite_setup_keyword_name = (
                            normalized_name  # Store the keyword name
                        )
                    elif is_suite_teardown:
                        # Suite-level teardown (applies to all tests in suite)
                        in_suite_teardown = True
                        suite_teardown_depth = 0
                        current_suite_teardown_keywords = []
                        suite_teardown_keyword_name = (
                            normalized_name  # Store the keyword name
                        )
                        # Debug: print(f"DEBUG: Starting suite teardown collection (suite_id: {current_suite_id}, kw_name: {keyword_name}, kw_type: {kw_type}, current_test_name: {current_test_name})")
                    elif is_test_setup:
                        # Test-level setup (part of this test's keywords)
                        in_test_setup = True
                        test_setup_depth = 0
                        # Test setup keywords are added to keyword_sequence
                    elif is_test_teardown:
                        # Test-level teardown (part of this test's keywords)
                        in_test_teardown = True
                        test_teardown_depth = 0
                        # Test teardown keywords are added to keyword_sequence
                    elif in_suite_setup:
                        # We're inside suite setup, collect ALL keywords (not just depth 1)
                        suite_setup_depth += 1
                        # Collect keywords at any depth within suite setup
                        full_keyword = normalize_keyword(keyword_name, library_name)
                        if full_keyword:
                            current_suite_setup_keywords.append(full_keyword)
                    elif in_suite_teardown:
                        # We're inside suite teardown, collect ALL keywords (not just depth 1)
                        suite_teardown_depth += 1
                        # Collect keywords at any depth within suite teardown
                        full_keyword = normalize_keyword(keyword_name, library_name)
                        if full_keyword:
                            current_suite_teardown_keywords.append(full_keyword)
                    elif current_test_name:
                        # Regular test keyword OR test setup/teardown keyword
                        # Collect ALL keywords within test (including test setup/teardown)
                        if in_test_setup:
                            test_setup_depth += 1
                        elif in_test_teardown:
                            test_teardown_depth += 1

                        full_keyword = normalize_keyword(keyword_name, library_name)
                        if full_keyword:
                            keyword_sequence.append(full_keyword)

            elif event == "end":
                if element.tag == "test":
                    if current_test_name:
                        # Combine: suite setup + test keywords + suite teardown
                        combined_keywords = []

                        # Get suite keywords for current suite
                        suite_setup_keywords = []
                        suite_teardown_keywords = []
                        if current_suite_id and current_suite_id in suite_keywords_map:
                            suite_setup_keywords = suite_keywords_map[current_suite_id][
                                "setup"
                            ]
                            suite_teardown_keywords = suite_keywords_map[
                                current_suite_id
                            ]["teardown"]

                        if suite_setup_keywords:
                            combined_keywords.extend(suite_setup_keywords)
                        if keyword_sequence:
                            combined_keywords.extend(keyword_sequence)
                        if suite_teardown_keywords:
                            combined_keywords.extend(suite_teardown_keywords)

                        if combined_keywords:
                            test_dict = {
                                "test_name": current_test_name,
                                "keywords": combined_keywords,
                                "suite_id": current_suite_id,  # Store for later update
                            }
                            # Store test temporarily (we'll finalize when suite ends or teardown is found)
                            if current_suite_id:
                                if current_suite_id not in suite_tests_map:
                                    suite_tests_map[current_suite_id] = []
                                suite_tests_map[current_suite_id].append(test_dict)
                            else:
                                # No suite ID, add directly
                                test_data.append(test_dict)
                    current_test_name = None
                    keyword_sequence = []
                    # Clear element to free memory immediately
                    element.clear()
                elif element.tag == "suite":
                    # Suite ended - finalize all tests in this suite with latest suite teardown
                    if current_suite_id and current_suite_id in suite_tests_map:
                        suite_teardown_keywords = suite_keywords_map.get(
                            current_suite_id, {}
                        ).get("teardown", [])
                        # Debug: print(f"DEBUG: Suite ending, finalizing {len(suite_tests_map[current_suite_id])} tests with teardown: {len(suite_teardown_keywords)} keywords")
                        for test_dict in suite_tests_map[current_suite_id]:
                            # Update with latest suite teardown if not already included
                            keywords = test_dict["keywords"]
                            if suite_teardown_keywords:
                                # Check if teardown already at end (safely)
                                if len(keywords) >= len(suite_teardown_keywords):
                                    if (
                                        keywords[-len(suite_teardown_keywords) :]
                                        != suite_teardown_keywords
                                    ):
                                        keywords.extend(suite_teardown_keywords)
                                        test_dict["keywords"] = keywords
                                        # Debug: print(f"DEBUG: Added {len(suite_teardown_keywords)} teardown keywords to test {test_dict['test_name']} (now {len(keywords)} total)")
                                else:
                                    # Test has fewer keywords than teardown, just append
                                    keywords.extend(suite_teardown_keywords)
                                    test_dict["keywords"] = keywords
                                    # Debug: print(f"DEBUG: Added {len(suite_teardown_keywords)} teardown keywords to test {test_dict['test_name']} (now {len(keywords)} total)")
                            # Remove suite_id before adding
                            test_dict.pop("suite_id", None)
                            test_data.append(test_dict)
                        # Clear processed tests
                        del suite_tests_map[current_suite_id]
                    # Reset current suite tracking
                    current_suite_id = None
                elif element.tag == "kw":
                    keyword_name = element.attrib.get("name", "")
                    kw_type = element.attrib.get("type", "").upper()
                    normalized_name = (
                        keyword_name.lower().strip() if keyword_name else ""
                    )

                    # Check if this is the suite setup/teardown keyword ending
                    # Detection is GENERIC - based on stored keyword name match OR type attribute
                    is_suite_setup_end = (
                        in_suite_setup
                        and suite_setup_depth == 0
                        and (
                            normalized_name == suite_setup_keyword_name
                            or (kw_type == "SETUP" and not current_test_name)
                        )
                    )
                    is_suite_teardown_end = (
                        in_suite_teardown
                        and suite_teardown_depth == 0
                        and (
                            normalized_name == suite_teardown_keyword_name
                            or (kw_type == "TEARDOWN" and not current_test_name)
                        )
                    )
                    is_test_setup = kw_type == "SETUP" and current_test_name
                    is_test_teardown = kw_type == "TEARDOWN" and current_test_name

                    if is_suite_setup_end:
                        # Suite setup completed - save the keywords for all tests in this suite
                        if current_suite_id:
                            suite_keywords_map[current_suite_id][
                                "setup"
                            ] = current_suite_setup_keywords.copy()
                            # Debug: print(f"DEBUG: Suite setup collected: {len(current_suite_setup_keywords)} keywords")
                        in_suite_setup = False
                        suite_setup_depth = 0
                        current_suite_setup_keywords = []
                        suite_setup_keyword_name = None
                    elif is_suite_teardown_end:
                        # Suite teardown completed - save the keywords for all tests in this suite
                        # Debug: print(f"DEBUG: Suite teardown ending (suite_id: {current_suite_id}, collected {len(current_suite_teardown_keywords)} keywords)")
                        if current_suite_id:
                            suite_keywords_map[current_suite_id][
                                "teardown"
                            ] = current_suite_teardown_keywords.copy()
                            # Update all already-processed tests in this suite with teardown keywords
                            if current_suite_id in suite_tests_map:
                                for test_dict in suite_tests_map[current_suite_id]:
                                    # Add teardown if not already present at the end
                                    keywords = test_dict["keywords"]
                                    teardown = current_suite_teardown_keywords.copy()
                                    if teardown:
                                        # Check if teardown already at end (safely)
                                        if len(keywords) >= len(teardown):
                                            if keywords[-len(teardown) :] != teardown:
                                                keywords.extend(teardown)
                                                test_dict["keywords"] = keywords
                                                # Debug: print(f"DEBUG: Updated test {test_dict['test_name']} with {len(teardown)} teardown keywords (when teardown ended)")
                                        else:
                                            # Test has fewer keywords than teardown, just append
                                            keywords.extend(teardown)
                                            test_dict["keywords"] = keywords
                                            # Debug: print(f"DEBUG: Updated test {test_dict['test_name']} with {len(teardown)} teardown keywords (when teardown ended)")
                            # Debug: print(f"DEBUG: Suite teardown saved: {len(current_suite_teardown_keywords)} keywords for suite {current_suite_id}")
                        in_suite_teardown = False
                        suite_teardown_depth = 0
                        current_suite_teardown_keywords = []
                        suite_teardown_keyword_name = None
                    elif is_test_setup and in_test_setup:
                        # Test setup completed
                        in_test_setup = False
                        test_setup_depth = 0
                    elif is_test_teardown and in_test_teardown:
                        # Test teardown completed
                        in_test_teardown = False
                        test_teardown_depth = 0
                    elif in_suite_setup and suite_setup_depth > 0:
                        suite_setup_depth -= 1
                    elif in_suite_teardown and suite_teardown_depth > 0:
                        suite_teardown_depth -= 1
                    elif in_test_setup and test_setup_depth > 0:
                        test_setup_depth -= 1
                    elif in_test_teardown and test_teardown_depth > 0:
                        test_teardown_depth -= 1

        # Finalize any remaining tests (in case suite didn't close properly)
        for suite_id, tests in suite_tests_map.items():
            suite_teardown_keywords = suite_keywords_map.get(suite_id, {}).get(
                "teardown", []
            )
            for test_dict in tests:
                if suite_teardown_keywords:
                    keywords = test_dict["keywords"]
                    if (
                        keywords[-len(suite_teardown_keywords) :]
                        != suite_teardown_keywords
                    ):
                        keywords.extend(suite_teardown_keywords)
                        test_dict["keywords"] = keywords
                test_dict.pop("suite_id", None)
                test_data.append(test_dict)

        # Check if suite setup/teardown were collected (generic check)
        has_suite_setup = any(
            len(suite_keywords_map.get(sid, {}).get("setup", [])) > 0
            for sid in suite_keywords_map.keys()
        )
        has_suite_teardown = any(
            len(suite_keywords_map.get(sid, {}).get("teardown", [])) > 0
            for sid in suite_keywords_map.keys()
        )

        metadata = {
            "has_suite_setup": has_suite_setup,
            "has_suite_teardown": has_suite_teardown,
        }

        return test_data, metadata

    except (FileNotFoundError, OSError):
        # Re-raise file system errors so they can be caught by tests
        raise
    except ET.ParseError as e:
        print(f"XML parsing error in {xml_path}: {e}")
        return [], {"has_suite_setup": False, "has_suite_teardown": False}
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return [], {"has_suite_setup": False, "has_suite_teardown": False}


def collect_all_tests(folder_path):
    """Aggregate keyword sequences from all output.xml files."""
    all_tests = []
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    xml_files = list(folder.rglob("*.xml"))
    print(f"Found {len(xml_files)} XML files to process...")

    # Statistics
    total_keywords = 0
    has_suite_setup = False
    has_suite_teardown = False

    for idx, xml_file in enumerate(xml_files, 1):
        if idx % 10 == 0:
            print(f"Processing file {idx}/{len(xml_files)}: {xml_file.name}")
        tests, metadata = extract_keywords_from_output(xml_file)

        # Collect statistics
        for test in tests:
            keywords = test.get("keywords", [])
            total_keywords += len(keywords)

        # Track if any file had suite setup/teardown
        if metadata.get("has_suite_setup"):
            has_suite_setup = True
        if metadata.get("has_suite_teardown"):
            has_suite_teardown = True

        all_tests.extend(tests)

        # Print summary statistics
        if all_tests:
            avg_keywords = total_keywords / len(all_tests)
            print(f"\n📊 Extraction Statistics:")
            print(f"   Total test cases: {len(all_tests)}")
            print(f"   Total keywords extracted: {total_keywords}")
            print(f"   Average keywords per test: {avg_keywords:.1f}")
            # Show sample
            if len(all_tests) > 0:
                sample = all_tests[0]
                sample_keywords = sample.get("keywords", [])
                print(f"\n   Sample test: {sample.get('test_name', 'Unknown')}")
                print(
                    f"   Sample keywords ({len(sample_keywords)}): {sample_keywords[:5]}{'...' if len(sample_keywords) > 5 else ''}"
                )
                # Generic check: Use metadata from extraction (not keyword name patterns)
                print(
                    f"   Suite setup detected: {'Yes ✓' if has_suite_setup else 'No'}"
                )
                print(
                    f"   Suite teardown detected: {'Yes ✓' if has_suite_teardown else 'No'}"
                )

                # If not detected, show first/last keywords for manual verification
                if not has_suite_setup:
                    print(f"   First 5 keywords: {sample_keywords[:5]}")
                if not has_suite_teardown:
                    print(f"   Last 5 keywords: {sample_keywords[-5:]}")

    return all_tests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract keyword sequences from Robot Framework XML logs"
    )
    parser.add_argument(
        "--folder",
        "-f",
        type=str,
        default="/home/administrator/RafiWork/AutoAccAutoComplete/data/xml_files/CLS_ROBOTS_RBAC_XML_FILES",
        help="Folder containing XML files",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="keyword_dataset.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--append",
        "-a",
        action="store_true",
        help="Append to existing output file instead of overwriting",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing file and remove duplicates",
    )

    args = parser.parse_args()

    try:
        new_data = collect_all_tests(args.folder)
        print(f"\n✅ Extracted {len(new_data)} test cases from XML files.")

        # Handle append/merge modes
        if args.append or args.merge:
            existing_data = []
            if Path(args.output).exists():
                try:
                    with open(args.output, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    print(f"📂 Loaded {len(existing_data)} existing test cases")
                except Exception as e:
                    print(f"⚠️  Warning: Could not load existing file: {e}")
                    existing_data = []

            if args.merge:
                # Remove duplicates based on test_name and keywords sequence
                existing_set = {
                    (item.get("test_name", ""), tuple(item.get("keywords", [])))
                    for item in existing_data
                }
                new_set = {
                    (item.get("test_name", ""), tuple(item.get("keywords", [])))
                    for item in new_data
                }

                # Add only truly new items
                added = 0
                for item in new_data:
                    key = (item.get("test_name", ""), tuple(item.get("keywords", [])))
                    if key not in existing_set:
                        existing_data.append(item)
                        added += 1

                all_data = existing_data
                print(
                    f"🔄 Merged: {added} new test cases added, {len(existing_data)} total"
                )
            else:
                # Simple append
                all_data = existing_data + new_data
                print(
                    f"➕ Appended: {len(new_data)} new test cases, {len(all_data)} total"
                )
        else:
            all_data = new_data

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved dataset to {args.output} ({len(all_data)} total test cases)")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
