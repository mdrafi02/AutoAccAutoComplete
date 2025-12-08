#!/usr/bin/env python3
import ijson
import argparse
from collections import Counter

DEFAULT_FILE = "keyword_dataset.json"


def extract_library(keyword: str):
    """Extract library prefix e.g., 'builtin.log' → 'builtin.'"""
    if "." in keyword:
        return keyword.split(".")[0].lower() + "."
    return "<unknown>"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect keyword dataset statistics")
    parser.add_argument(
        "--file", "-f", type=str, default=DEFAULT_FILE, help="Input JSON dataset file"
    )
    args = parser.parse_args()

    FILE = args.file
    print(f"Inspecting dataset (streaming): {FILE}…")

    # Counters
    total_items = 0
    empty_items = 0
    duplicate_sequences = 0

    keyword_freq = Counter()
    library_freq = Counter()
    seq_length_freq = Counter()

    seen_sequences = set()

    with open(FILE, "r", encoding="utf-8") as f:
        for item in ijson.items(f, "item"):
            total_items += 1
            raw_keywords = item.get("keywords", [])

            if not raw_keywords:
                empty_items += 1
                continue

            # Normalize
            keywords = [k.strip().lower() for k in raw_keywords if k.strip()]

            # Detect duplicates
            seq_key = tuple(keywords)
            if seq_key in seen_sequences:
                duplicate_sequences += 1
            else:
                seen_sequences.add(seq_key)

            # Sequence length distribution
            seq_length_freq[len(keywords)] += 1

            # Keyword + library frequency
            for kw in keywords:
                keyword_freq[kw] += 1
                lib = extract_library(kw)
                library_freq[lib] += 1

            if total_items % 10000 == 0:
                print(f"Processed {total_items:,} items…")

    # ======================================================================
    #                          REPORT SECTION
    # ======================================================================

    print("\n========== DATASET SUMMARY ==========\n")
    print(f"Total sequences:       {total_items:,}")
    print(f"Empty sequences:       {empty_items:,}")
    print(f"Duplicate sequences:   {duplicate_sequences:,}")
    print(f"Unique sequences:      {len(seen_sequences):,}")

    # ----------------------------------------------------------------------
    print("\n========== MOST USED LIBRARIES (TOP 20) ==========\n")
    for lib, count in library_freq.most_common(20):
        print(f"{lib:30} {count:,}")

    print("\n========== LEAST USED LIBRARIES (BOTTOM 20) ==========\n")
    for lib, count in library_freq.most_common()[-20:]:
        print(f"{lib:30} {count:,}")

    # ----------------------------------------------------------------------
    print("\n========== MOST USED KEYWORDS (TOP 50) ==========\n")
    for kw, count in keyword_freq.most_common(50):
        print(f"{kw:50} {count:,}")

    print("\n========== LEAST USED KEYWORDS (BOTTOM 50) ==========\n")
    for kw, count in keyword_freq.most_common()[-50:]:
        print(f"{kw:50} {count:,}")

    # ----------------------------------------------------------------------
    print("\n========== SEQUENCE LENGTH DISTRIBUTION ==========\n")
    for length, count in sorted(seq_length_freq.items()):
        print(f"Length {length:3} → {count:,} sequences")
