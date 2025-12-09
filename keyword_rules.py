#!/usr/bin/env python3
"""
Rule-based keyword prediction constraints.
Enforces domain knowledge rules on top of ML model predictions.
"""

import json
import os
from typing import List, Tuple, Dict, Optional, Set
from pathlib import Path


class KeywordRules:
    """
    Manages keyword sequence rules to enforce domain constraints.

    Rules can specify:
    - required_following: Keywords that MUST follow a given keyword
    - preferred_following: Keywords that should be boosted in probability
    - blocked_following: Keywords that should NEVER follow a given keyword
    - sequence_patterns: Multi-keyword sequence patterns
    """

    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize keyword rules from a JSON file.

        Args:
            rules_file: Path to JSON rules file. If None, uses default location.
        """
        self.required_following: Dict[str, List[str]] = {}
        self.preferred_following: Dict[str, List[str]] = {}
        self.blocked_following: Dict[str, List[str]] = {}
        self.sequence_patterns: List[Dict] = []

        if rules_file is None:
            # Default location: same directory as this file
            rules_file = str(Path(__file__).parent / "keyword_rules.json")

        if os.path.exists(rules_file):
            self.load_rules(rules_file)
        else:
            print(f"⚠️  Rules file not found: {rules_file}")
            print("   Using empty rules. Create a rules file to enforce constraints.")

    def load_rules(self, rules_file: str):
        """Load rules from JSON file."""
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules_data = json.load(f)

            # Support both old format (direct keys) and new format (nested in "rules"/"patterns")
            required_data = rules_data.get("required_following", {})
            preferred_data = rules_data.get("preferred_following", {})
            blocked_data = rules_data.get("blocked_following", {})
            patterns_data = rules_data.get("sequence_patterns", [])

            # Handle nested structure (new format)
            if isinstance(required_data, dict) and "rules" in required_data:
                self.required_following = required_data["rules"]
            else:
                self.required_following = (
                    required_data if isinstance(required_data, dict) else {}
                )

            if isinstance(preferred_data, dict) and "rules" in preferred_data:
                self.preferred_following = preferred_data["rules"]
            else:
                self.preferred_following = (
                    preferred_data if isinstance(preferred_data, dict) else {}
                )

            if isinstance(blocked_data, dict) and "rules" in blocked_data:
                self.blocked_following = blocked_data["rules"]
            else:
                self.blocked_following = (
                    blocked_data if isinstance(blocked_data, dict) else {}
                )

            if isinstance(patterns_data, dict) and "patterns" in patterns_data:
                self.sequence_patterns = patterns_data["patterns"]
            else:
                self.sequence_patterns = (
                    patterns_data if isinstance(patterns_data, list) else []
                )

            print(
                f"✅ Loaded {len(self.required_following)} required, "
                f"{len(self.preferred_following)} preferred, "
                f"{len(self.blocked_following)} blocked rules"
            )
        except Exception as e:
            print(f"❌ Error loading rules file: {e}")
            raise

    def get_last_keyword(self, context_keywords: List[str]) -> Optional[str]:
        """Get the last non-empty keyword from context."""
        for keyword in reversed(context_keywords):
            if keyword and keyword.strip():
                return keyword.strip()
        return None

    def apply_rules(
        self,
        predictions: List[Tuple[str, float]],
        context_keywords: List[str],
        boost_factor: float = 1.5,
    ) -> List[Tuple[str, float]]:
        """
        Apply rules to predictions, reordering and filtering as needed.

        Args:
            predictions: List of (keyword, probability) tuples from model
            context_keywords: Previous keywords in sequence
            boost_factor: Multiplier for preferred keywords (default: 1.5)

        Returns:
            Modified list of (keyword, probability) tuples
        """
        if not predictions:
            return predictions

        last_keyword = self.get_last_keyword(context_keywords)
        if not last_keyword:
            return predictions

        # Convert to list for modification
        result = list(predictions)

        # 1. Check for required following keywords
        required = self.required_following.get(last_keyword, [])
        if required:
            # Move required keywords to top, even if not in predictions
            required_found = []
            required_not_found = []

            for req_kw in required:
                found = False
                for i, (kw, prob) in enumerate(result):
                    if kw == req_kw:
                        required_found.append((kw, prob))
                        result.pop(i)
                        found = True
                        break
                if not found:
                    required_not_found.append(req_kw)

            # Add required keywords with high probability if not found
            for req_kw in required_not_found:
                required_found.append((req_kw, 0.9))  # High probability for required

            # Prepend required keywords to results
            result = required_found + result

        # 2. Boost preferred keywords
        preferred = self.preferred_following.get(last_keyword, [])
        if preferred:
            for i, (kw, prob) in enumerate(result):
                if kw in preferred:
                    result[i] = (kw, min(1.0, prob * boost_factor))

        # 3. Remove blocked keywords
        blocked = self.blocked_following.get(last_keyword, [])
        if blocked:
            result = [(kw, prob) for kw, prob in result if kw not in blocked]

        # 4. Check sequence patterns
        result = self._apply_sequence_patterns(result, context_keywords)

        # Re-sort by probability (descending)
        result.sort(key=lambda x: x[1], reverse=True)

        return result

    def _apply_sequence_patterns(
        self,
        predictions: List[Tuple[str, float]],
        context_keywords: List[str],
    ) -> List[Tuple[str, float]]:
        """
        Apply multi-keyword sequence patterns.

        Sequence patterns can specify:
        - after: List of keywords that must appear in sequence
        - then: Required following keyword
        - boost: Keywords to boost
        - block: Keywords to block
        """
        if not self.sequence_patterns:
            return predictions

        result = list(predictions)

        for pattern in self.sequence_patterns:
            after = pattern.get("after", [])
            if not after:
                continue

            # Check if context matches the "after" pattern
            context_str = " ".join(context_keywords)
            pattern_str = " ".join(after)

            # Check if pattern appears at the end of context
            if context_keywords[-len(after) :] == after:
                # Apply pattern rules
                then_kw = pattern.get("then")
                if then_kw:
                    # Move "then" keyword to top
                    found = False
                    for i, (kw, prob) in enumerate(result):
                        if kw == then_kw:
                            result.pop(i)
                            result.insert(0, (kw, prob))
                            found = True
                            break
                    if not found:
                        result.insert(0, (then_kw, 0.9))

                # Boost keywords
                boost_kws = pattern.get("boost", [])
                boost_factor = pattern.get("boost_factor", 1.5)
                for i, (kw, prob) in enumerate(result):
                    if kw in boost_kws:
                        result[i] = (kw, min(1.0, prob * boost_factor))

                # Block keywords
                block_kws = pattern.get("block", [])
                if block_kws:
                    result = [(kw, prob) for kw, prob in result if kw not in block_kws]

        return result

    def validate_sequence(self, keywords: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate if a sequence of keywords follows the rules.

        Returns:
            (is_valid, error_message)
        """
        for i in range(len(keywords) - 1):
            current = keywords[i]
            next_kw = keywords[i + 1]

            # Check required following
            required = self.required_following.get(current, [])
            if required and next_kw not in required:
                return (
                    False,
                    f"After '{current}', one of {required} is required, but got '{next_kw}'",
                )

            # Check blocked following
            blocked = self.blocked_following.get(current, [])
            if next_kw in blocked:
                return False, f"After '{current}', '{next_kw}' is not allowed"

        return True, None


def apply_rules_to_predictions(
    predictions: List[Tuple[str, float]],
    context_keywords: List[str],
    rules_file: Optional[str] = None,
    boost_factor: float = 1.5,
) -> List[Tuple[str, float]]:
    """
    Convenience function to apply rules to predictions.

    Args:
        predictions: List of (keyword, probability) tuples
        context_keywords: Previous keywords in sequence
        rules_file: Path to rules JSON file (optional)
        boost_factor: Multiplier for preferred keywords

    Returns:
        Modified predictions with rules applied
    """
    rules = KeywordRules(rules_file)
    return rules.apply_rules(predictions, context_keywords, boost_factor)
