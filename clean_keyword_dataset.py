#!/usr/bin/env python3
"""
Streaming cleaning script (optimized):
 - normalizes keywords (lowercase + strip)
 - applies blacklist, blacklist prefixes, auto-remove common keywords
 - supports optional whitelist (if empty -> whitelist disabled)
 - writes output incrementally (streaming) to avoid memory blowup
 - prints counts for diagnostics
 - PRESERVES whitelisted keywords even when sequences become short after 
   filtering out blacklisted keywords (e.g., login1. keywords in sequences 
   with builtin. keywords will be preserved)
 - DEDUPLICATES consecutive repeated keywords (from retry mechanisms like
   wait_until_keyword_succeeds) to prevent frequency inflation
 - HANDLES conditional keywords (run_keyword_if/else): Only the executed branch
   appears in XML, so we correctly preserve the actual execution path
"""

import ijson
import json
import argparse
from pathlib import Path
from collections import Counter

DEFAULT_INPUT_FILE = "keyword_dataset.json"
DEFAULT_OUTPUT_FILE = "keyword_dataset_cleaned.json"

# -----------------------------
# CONFIGURATIONS (edit as needed)
# -----------------------------

# WHITELIST: if both are empty, whitelist is treated as disabled (keep-all unless blacklisted)
ALLOWED_KEYWORDS = set()  # examples: {"connect to ap", "configure ssid"}
#ALLOWED_LIBRARIES_PREFIX = tuple()  # examples: ("wifilibrary.", "networklibrary.")
ALLOWED_LIBRARIES_PREFIX = tuple(
        [            
        "login1.",
        "policy1.",
        "tntmgt1.",
        "radius1.",
        "persona1.",
        "certificate1.",
        "dpsk1.",
        "workflow1.",
        "venue1.",
        "macreg1.",
        "property1.",
        "utils1.",
        "wifi1.",
        ]
        )

# BLACKLIST exact keywords (normalize to lowercase)
BLACKLIST_KEYWORDS = {
    "sleep", "log", "log_to_console", "comment", "no_operation"
}

# BLACKLIST prefix (library names) - case-insensitive, provide canonical prefix strings
BLACKLIST_PREFIXES = (
    "builtin.",        # e.g. builtin.log, builtin.sleep
    "seleniumlibrary.",
    "operatingsystem.",
)

# AUTO-REMOVE frequently-occurring junk
AUTO_REMOVE_COMMON = {
    "sleep", "log", "log_to_console", "run_keyword", "set_variable"
}

MIN_SEQUENCE_LENGTH = 2  # drop sequences shorter than this

# -----------------------------
# Utility helpers
# -----------------------------
def normalize_keyword(keyword):
    """Normalize keyword to lowercase and strip whitespace."""
    if keyword is None:
        return ""
    return keyword.strip().lower()

def any_prefix_matches(keyword, prefixes):
    """Check if keyword matches any of the given prefixes (case-insensitive)."""
    keyword_lower = keyword.lower()
    for prefix in prefixes:
        if keyword_lower.startswith(prefix.lower()):
            return True
    return False

# -----------------------------
# Main cleaning function
# -----------------------------
def clean_dataset(input_file, output_file):
    """Clean the dataset with streaming processing."""
    
    # Use configured auto-remove set
    AUTO_REMOVE_KEYWORDS_FINAL = {normalize_keyword(kw) for kw in AUTO_REMOVE_COMMON}
    
    # Normalize config sets / prefixes for comparisons (do once)
    BLACKLIST_KEYWORDS_NORMALIZED = {normalize_keyword(kw) for kw in BLACKLIST_KEYWORDS}
    ALLOWED_KEYWORDS_NORMALIZED = {normalize_keyword(kw) for kw in ALLOWED_KEYWORDS}
    BLACKLIST_PREFIXES_NORMALIZED = tuple(p.lower() for p in BLACKLIST_PREFIXES)
    ALLOWED_LIB_PREFIXES_NORMALIZED = tuple(p.lower() for p in ALLOWED_LIBRARIES_PREFIX)
    
    whitelist_enabled = bool(ALLOWED_KEYWORDS_NORMALIZED or ALLOWED_LIB_PREFIXES_NORMALIZED)
    
    # Counters for diagnostics
    removed_counters = Counter()   # reasons for removing entire sequence (not per-keyword)
    per_keyword_removed = Counter()
    kept_count = 0
    skipped_short = 0
    duplicates_skipped = 0
    processed = 0
    
    seen_sequences = set()  # stores tuples of keywords (normalized) to dedupe
    
    print("Streaming cleaning + writing output...")
    
    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8") as f_out:
        
        f_out.write("[\n")
        first_out = True

        for item in ijson.items(f_in, "item"):
            processed += 1
            raw_keywords = item.get("keywords", [])
            cleaned_seq = []
            removed_reasons_for_seq = set()

            has_whitelisted_keyword = False  # Track if sequence contains whitelisted keywords
            
            for raw_keyword in raw_keywords:
                normalized_keyword = normalize_keyword(raw_keyword)
                if not normalized_keyword:
                    per_keyword_removed["empty"] += 1
                    continue

                # blacklist exact
                if normalized_keyword in BLACKLIST_KEYWORDS_NORMALIZED:
                    per_keyword_removed["blacklist_exact"] += 1
                    continue

                # blacklist prefix
                if any_prefix_matches(normalized_keyword, BLACKLIST_PREFIXES_NORMALIZED):
                    per_keyword_removed["blacklist_prefix"] += 1
                    continue

                # auto remove (common)
                if normalized_keyword in AUTO_REMOVE_KEYWORDS_FINAL:
                    per_keyword_removed["auto_remove_common"] += 1
                    continue

                # whitelist logic: if enabled only allow whitelisted items
                if whitelist_enabled:
                    is_allowed = False
                    if normalized_keyword in ALLOWED_KEYWORDS_NORMALIZED:
                        is_allowed = True
                        has_whitelisted_keyword = True
                    if any_prefix_matches(normalized_keyword, ALLOWED_LIB_PREFIXES_NORMALIZED):
                        is_allowed = True
                        has_whitelisted_keyword = True
                    if not is_allowed:
                        per_keyword_removed["whitelist_excluded"] += 1
                        continue

                # if passed all filters, keep it
                cleaned_seq.append(normalized_keyword)

            # Deduplicate consecutive repeated keywords (from retry mechanisms like wait_until_keyword_succeeds)
            # This prevents retry artifacts from inflating keyword frequencies
            # Note: For conditional keywords (run_keyword_if/else), only the executed branch appears
            # in the XML, so both branches are never extracted together. The extraction preserves
            # whichever branch actually executed (IF or ELSE), and we keep it after removing builtin.*
            if cleaned_seq:
                deduplicated_seq = []
                prev_keyword = None
                for keyword in cleaned_seq:
                    if keyword != prev_keyword:
                        deduplicated_seq.append(keyword)
                        prev_keyword = keyword
                    else:
                        # Count consecutive duplicates for diagnostics
                        per_keyword_removed["consecutive_duplicate"] += 1
                cleaned_seq = deduplicated_seq

            # drop too-short sequences, BUT preserve sequences with whitelisted keywords
            # even if they become short after filtering out blacklisted keywords
            # This is important for nested keywords:
            # - When builtin.wait_until_keyword_succeeds contains login1.login_user, we remove builtin.* but keep login1.*
            # - When builtin.run_keyword_if contains login1.login_user (in IF or ELSE branch), we remove builtin.* but keep login1.*
            # Note: For conditionals, only the executed branch appears in XML, so we correctly preserve the actual execution path
            min_required_length = MIN_SEQUENCE_LENGTH
            if whitelist_enabled and has_whitelisted_keyword:
                # If sequence contains whitelisted keywords, allow it even if short
                # (minimum 1 keyword to avoid empty sequences)
                # This preserves nested whitelisted keywords that appear after blacklisted ones
                min_required_length = 1
                if len(cleaned_seq) < min_required_length:
                    skipped_short += 1
                    removed_counters["too_short_whitelisted"] += 1
                    continue
            elif len(cleaned_seq) < min_required_length:
                skipped_short += 1
                removed_counters["too_short"] += 1
                continue

            # dedupe sequence (exact match)
            seq_key = tuple(cleaned_seq)
            if seq_key in seen_sequences:
                duplicates_skipped += 1
                removed_counters["duplicate_sequence"] += 1
                continue
            seen_sequences.add(seq_key)

            # write to output incrementally
            out_obj = {"keywords": cleaned_seq}
            if not first_out:
                f_out.write(",\n")
            first_out = False
            json.dump(out_obj, f_out, ensure_ascii=False)
            kept_count += 1

            # progress print
            if processed % 10000 == 0:
                print(f"Processed {processed:,} items - kept {kept_count:,}")

        f_out.write("\n]\n")
    
    # -----------------------------
    # Final summary
    # -----------------------------
    print("\nCLEANING SUMMARY")
    print(f"Total processed: {processed:,}")
    print(f"Total kept: {kept_count:,}")
    print(f"Skipped (too short): {skipped_short:,}")
    print(f"Duplicates skipped: {duplicates_skipped:,}")
    print(f"Per-keyword removals sample: {per_keyword_removed.most_common(10)}")
    print(f"Sequence removal reasons: {removed_counters.most_common()}")
    
    print(f"\n✅ Saved cleaned dataset -> {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean keyword dataset")
    parser.add_argument("--input", "-i", type=str, default=DEFAULT_INPUT_FILE,
                       help="Input JSON dataset file")
    parser.add_argument("--output", "-o", type=str, default=DEFAULT_OUTPUT_FILE,
                       help="Output cleaned JSON dataset file")
    parser.add_argument("--append", "-a", action="store_true",
                       help="Append cleaned data to existing output file (removes duplicates)")
    
    args = parser.parse_args()
    
    try:
        if args.append and Path(args.output).exists():
            # Merge mode: load existing, clean new, merge and dedupe
            print(f"📂 Loading existing cleaned dataset: {args.output}")
            existing_sequences = set()
            existing_data = []
            
            try:
                with open(args.output, "r", encoding="utf-8") as f:
                    for item in ijson.items(f, "item"):
                        seq = tuple(item.get("keywords", []))
                        if seq:
                            existing_sequences.add(seq)
                            existing_data.append(item)
                print(f"   Found {len(existing_data)} existing sequences")
            except Exception as e:
                print(f"⚠️  Warning: Could not load existing file: {e}")
                existing_sequences = set()
                existing_data = []
            
            # Clean new data
            temp_output = args.output + ".tmp"
            clean_dataset(args.input, temp_output)
            
            # Merge cleaned new data with existing
            print("🔄 Merging with existing cleaned data...")
            new_count = 0
            with open(temp_output, "r", encoding="utf-8") as f:
                for item in ijson.items(f, "item"):
                    seq = tuple(item.get("keywords", []))
                    if seq and seq not in existing_sequences:
                        existing_data.append(item)
                        existing_sequences.add(seq)
                        new_count += 1
            
            # Write merged data
            with open(args.output, "w", encoding="utf-8") as f_out:
                f_out.write("[\n")
                for idx, item in enumerate(existing_data):
                    if idx > 0:
                        f_out.write(",\n")
                    json.dump(item, f_out, ensure_ascii=False)
                f_out.write("\n]\n")
            
            # Clean up temp file
            Path(temp_output).unlink()
            print(f"✅ Merged: {new_count} new sequences added, {len(existing_data)} total")
        else:
            clean_dataset(args.input, args.output)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

