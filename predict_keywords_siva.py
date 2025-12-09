import json
import numpy as np
import tensorflow as tf
import argparse
import os
from tensorflow.keras.preprocessing.text import tokenizer_from_json
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keyword_rules import KeywordRules

DEFAULT_MODEL_PATH = "keyword_predictor.keras"
DEFAULT_TOKENIZER_PATH = "tokenizer.json"
DEFAULT_RULES_FILE = "keyword_rules.json"


def load_model_and_tokenizer(model_path, tokenizer_path):
    """Load model and tokenizer with error handling."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(tokenizer_path):
        raise FileNotFoundError(f"Tokenizer file not found: {tokenizer_path}")

    try:
        model = tf.keras.models.load_model(model_path)
        with open(tokenizer_path, "r", encoding="utf-8") as f:
            tokenizer_data = json.load(f)
            tokenizer = tokenizer_from_json(json.dumps(tokenizer_data))
        return model, tokenizer
    except Exception as e:
        raise RuntimeError(f"Error loading model/tokenizer: {e}")


def predict_next_keyword(model, tokenizer, context_keywords, top_k=3):
    """
    Predict next keyword(s) based on previous keywords.
    Automatically handles context size from model input shape.

    Args:
        model: Trained Keras model
        tokenizer: Fitted tokenizer
        context_keywords: List of previous keywords
        top_k: Number of top predictions to return

    Returns:
        List of tuples (keyword, probability) sorted by probability
    """
    if not context_keywords:
        raise ValueError("At least one keyword must be provided")

    # Get context size from model
    context_size = model.input_shape[1]
    index_to_word = {v: k for k, v in tokenizer.word_index.items()}

    # Ensure exactly context_size keywords
    if len(context_keywords) > context_size:
        context_keywords = context_keywords[-context_size:]  # Take last N
    elif len(context_keywords) < context_size:
        # Pad with empty strings (will be converted to 0 by tokenizer)
        context_keywords = [""] * (
            context_size - len(context_keywords)
        ) + context_keywords

    try:
        token_sequence = tokenizer.texts_to_sequences([context_keywords])[0]
        token_sequence = pad_sequences(
            [token_sequence], maxlen=context_size, padding="pre"
        )
        predictions = model.predict(token_sequence, verbose=0)[0]

        # Get top_k indices, excluding 0 (padding token) and invalid indices
        # Create list of (index, probability) for valid indices only
        # Valid indices are those in the tokenizer's word_index (1-based)
        valid_predictions = [
            (idx, float(predictions[idx]))
            for idx in range(1, len(predictions))  # Skip 0 (padding)
            if idx in index_to_word
        ]

        if not valid_predictions:
            # If no valid predictions, return empty list
            # This shouldn't happen with a properly trained model, but handle gracefully
            return []

        # Sort by probability descending and take top_k
        valid_predictions.sort(key=lambda x: x[1], reverse=True)
        top_predictions = valid_predictions[:top_k]

        # Convert to (keyword, probability) tuples
        results = [(index_to_word[idx], prob) for idx, prob in top_predictions]

        # Ensure results are sorted by probability (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    except Exception as e:
        raise RuntimeError(f"Error during prediction: {e}")


def predict_next_keyword_with_depth(
    model, tokenizer, context_keywords, top_k=3, depth=1
):
    """
    Predict next keywords with hierarchical depth-based prediction.
    For each prediction at level N, predicts top_k keywords at level N+1 up to specified depth.

    Args:
        model: Trained Keras model
        tokenizer: Fitted tokenizer
        context_keywords: List of previous keywords (initial context)
        top_k: Number of top predictions to return at each level
        depth: Number of levels deep to predict (0 = no prediction, 1 = current level only)

    Returns:
        List of dictionaries, each containing:
        - keyword: str
        - probability: float
        - next_predictions: List (if depth > 1) of same structure recursively
    """
    if depth < 0:
        raise ValueError("Depth must be >= 0")

    if depth == 0:
        return []

    # Get current level predictions
    current_predictions = predict_next_keyword(
        model, tokenizer, context_keywords, top_k=top_k
    )

    # Get context size for building next context
    context_size = model.input_shape[1]

    results = []
    for keyword, probability in current_predictions:
        result = {"keyword": keyword, "probability": probability}

        # If depth > 1, recursively predict next level
        if depth > 1:
            # Build new context: append current keyword to existing context
            new_context = context_keywords.copy()
            if len(new_context) >= context_size:
                new_context = new_context[
                    -context_size + 1 :
                ]  # Keep last (context_size-1)
            new_context.append(keyword)

            # Recursively get next predictions
            next_predictions = predict_next_keyword_with_depth(
                model, tokenizer, new_context, top_k=top_k, depth=depth - 1
            )
            result["next_predictions"] = next_predictions

        results.append(result)

    return results


def apply_rules_to_hierarchical_predictions(hierarchical_data, context_keywords, rules):
    """Apply rules to hierarchical predictions recursively."""
    if not rules:
        return hierarchical_data

    results = []
    for pred in hierarchical_data:
        # Apply rules to current level
        current_predictions = [(pred["keyword"], pred["probability"])]
        modified = rules.apply_rules(current_predictions, context_keywords)

        result = {
            "keyword": modified[0][0] if modified else pred["keyword"],
            "probability": modified[0][1] if modified else pred["probability"],
        }

        # Recursively apply to next level
        if "next_predictions" in pred and pred["next_predictions"]:
            new_context = context_keywords + [result["keyword"]]
            result["next_predictions"] = apply_rules_to_hierarchical_predictions(
                pred["next_predictions"], new_context, rules
            )

        results.append(result)
    return results


def display_hierarchical_predictions(predictions, level=0, max_level=None):
    """
    Display hierarchical predictions in a tree-like format.

    Args:
        predictions: List of prediction dictionaries from predict_next_keyword_with_depth
        level: Current depth level (for indentation)
        max_level: Maximum level to display (None = all levels)
    """
    if max_level is not None and level >= max_level:
        return

    indent = "  " * level
    prefix = "├─" if level > 0 else ""

    for i, pred in enumerate(predictions):
        keyword = pred["keyword"]
        probability = pred["probability"]
        bar_length = int(probability * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)

        if level == 0:
            print(
                f"{indent}{prefix} {i+1}. {keyword:45s} {bar} {probability*100:5.1f}%"
            )
        else:
            print(f"{indent}{prefix} {keyword:45s} {bar} {probability*100:5.1f}%")

        # Display next level predictions if they exist
        if "next_predictions" in pred and pred["next_predictions"]:
            display_hierarchical_predictions(
                pred["next_predictions"], level + 1, max_level
            )


def cli_loop(model, tokenizer, depth=1, rules_file=None):
    """Interactive CLI loop for keyword prediction with sequence history and depth-based prediction."""
    context_size = model.input_shape[1]
    sequence_history = (
        []
    )  # Store the full sequence of keywords for sequential prediction
    current_predictions = []  # Store current predictions for user selection

    # Load keyword rules if available
    keyword_rules = None
    try:
        keyword_rules = KeywordRules(rules_file)
        if (
            keyword_rules.required_following
            or keyword_rules.preferred_following
            or keyword_rules.blocked_following
        ):
            print("✅ Keyword rules loaded and will be applied to predictions")
    except Exception:
        # Rules file not found or invalid - continue without rules
        pass

    print("=" * 70)
    print(" " * 15 + "🤖 Neural Keyword Predictor")
    print("=" * 70)
    print(f"\n📋 How it works:")
    print(f"   1. Start with 2 keywords (comma-separated)")
    print(f"   2. Model predicts the next keyword(s) with depth {depth}")
    print(f"   3. Select a prediction (1-{depth}) or add your own keyword")
    print(f"   4. Model uses ALL keywords in sequence for next prediction")
    if depth > 1:
        print(f"   5. Each prediction shows next {depth} levels of predictions")
    print(f"\n💡 Commands: 'clear' to reset | 'history' to view | 'exit' to quit")
    print(f"💡 Depth: {depth} level(s) - shows hierarchical predictions")
    print("=" * 70)

    while True:
        try:
            # Show current sequence status
            print("\n" + "-" * 70)
            if sequence_history:
                print(f"📜 CURRENT SEQUENCE ({len(sequence_history)} keywords):")
                print(f"   {' → '.join(sequence_history)}")
                context_keywords = (
                    sequence_history[-context_size:]
                    if len(sequence_history) >= context_size
                    else sequence_history
                )
                print(
                    f"\n🎯 CONTEXT USED (last {len(context_keywords)}): {' → '.join(context_keywords)}"
                )
                if len(sequence_history) > context_size:
                    print(
                        f"   ⚠️  Note: Model uses only last {context_size} keywords (input shape limitation)"
                    )
                    print(
                        f"   ℹ️  Model learned patterns from longer sequences during training"
                    )
            else:
                print("📜 CURRENT SEQUENCE: [empty]")
                print("\n💡 REQUEST: Enter 2 keywords to start (comma-separated)")
                print("   Example: login1.login_user, login1.authenticate")

            print("-" * 70)
            line = input("\n👉 YOUR INPUT: ").strip()

            if line.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!\n")
                break

            if line.lower() in ["clear", "reset"]:
                sequence_history = []
                current_predictions = []
                print("\n✅ Sequence cleared. Starting fresh!\n")
                continue

            if line.lower() in ["history", "seq"]:
                if sequence_history:
                    print(f"\n📜 FULL SEQUENCE ({len(sequence_history)} keywords):")
                    print(f"   {' → '.join(sequence_history)}")
                    context_keywords = (
                        sequence_history[-context_size:]
                        if len(sequence_history) >= context_size
                        else sequence_history
                    )
                    print(
                        f"\n🎯 CONTEXT FOR NEXT PREDICTION (last {len(context_keywords)}):"
                    )
                    print(f"   {' → '.join(context_keywords)}")
                else:
                    print("\n📜 Sequence is empty.")
                print()
                continue

            if not line:
                if sequence_history:
                    print("\n⚠️  Please select a prediction (1-3) or type a keyword.\n")
                else:
                    print(
                        "\n⚠️  Please provide 2 keywords to start (comma-separated).\n"
                    )
                continue

            # Handle initial state: require 2 keywords to start
            if len(sequence_history) == 0:
                # Parse initial keywords
                initial_keywords = [x.strip() for x in line.split(",") if x.strip()]
                if len(initial_keywords) < 2:
                    print(
                        f"\n❌ ERROR: Please provide at least 2 keywords (comma-separated).\n"
                    )
                    continue

                # Add first 2 keywords to sequence
                sequence_history.extend(initial_keywords[:2])
                print(f"\n✅ REQUEST RECEIVED: Added initial keywords")
                print(f"   Sequence: {' → '.join(sequence_history)}")

                # Predict next keyword based on the 2 initial keywords
                context_keywords = (
                    sequence_history[-context_size:]
                    if len(sequence_history) >= context_size
                    else sequence_history
                )
                print(
                    f"\n🔄 MODEL PROCESSING: Predicting next keyword(s) with depth {depth}..."
                )

                if depth > 1:
                    hierarchical_predictions = predict_next_keyword_with_depth(
                        model, tokenizer, context_keywords, top_k=3, depth=depth
                    )
                    # Apply rules if available
                    if keyword_rules:
                        hierarchical_predictions = (
                            apply_rules_to_hierarchical_predictions(
                                hierarchical_predictions,
                                context_keywords,
                                keyword_rules,
                            )
                        )
                    current_predictions = [
                        (p["keyword"], p["probability"])
                        for p in hierarchical_predictions
                    ]

                    print(
                        f"\n📊 MODEL RESPONSE - Top {len(current_predictions)} predictions (depth {depth}):"
                    )
                    print("   " + "-" * 66)
                    display_hierarchical_predictions(hierarchical_predictions)
                    print("   " + "-" * 66)
                else:
                    current_predictions = predict_next_keyword(
                        model, tokenizer, context_keywords
                    )
                    # Apply rules if available
                    if keyword_rules:
                        current_predictions = keyword_rules.apply_rules(
                            current_predictions, context_keywords
                        )
                    print(
                        f"\n📊 MODEL RESPONSE - Top {len(current_predictions)} predictions:"
                    )
                    print("   " + "-" * 66)
                    for i, (keyword, probability) in enumerate(current_predictions, 1):
                        bar_length = int(probability * 30)
                        bar = "█" * bar_length + "░" * (30 - bar_length)
                        print(f"   {i}. {keyword:45s} {bar} {probability*100:5.1f}%")
                    print("   " + "-" * 66)

                print(
                    f"\n💡 NEXT STEP: Type '1', '2', or '3' to select, or type your own keyword"
                )
                continue

            # Handle selection from predictions (1, 2, or 3)
            if line.isdigit() and 1 <= int(line) <= len(current_predictions):
                selected_index = int(line) - 1
                selected_keyword = current_predictions[selected_index][0]
                sequence_history.append(selected_keyword)
                print(f"\n✅ REQUEST RECEIVED: Selected prediction #{line}")
                print(f"   Selected: '{selected_keyword}'")
                print(f"   Updated sequence: {' → '.join(sequence_history)}")

                # Predict next based on updated sequence
                context_keywords = (
                    sequence_history[-context_size:]
                    if len(sequence_history) >= context_size
                    else sequence_history
                )
                print(
                    f"\n🔄 MODEL PROCESSING: Predicting next keyword(s) with depth {depth}..."
                )

                if depth > 1:
                    hierarchical_predictions = predict_next_keyword_with_depth(
                        model, tokenizer, context_keywords, top_k=3, depth=depth
                    )
                    # Apply rules if available
                    if keyword_rules:
                        hierarchical_predictions = (
                            apply_rules_to_hierarchical_predictions(
                                hierarchical_predictions,
                                context_keywords,
                                keyword_rules,
                            )
                        )
                    current_predictions = [
                        (p["keyword"], p["probability"])
                        for p in hierarchical_predictions
                    ]

                    print(
                        f"\n📊 MODEL RESPONSE - Top {len(current_predictions)} predictions (depth {depth}):"
                    )
                    print("   " + "-" * 66)
                    display_hierarchical_predictions(hierarchical_predictions)
                    print("   " + "-" * 66)
                else:
                    current_predictions = predict_next_keyword(
                        model, tokenizer, context_keywords
                    )
                    # Apply rules if available
                    if keyword_rules:
                        current_predictions = keyword_rules.apply_rules(
                            current_predictions, context_keywords
                        )
                    print(
                        f"\n📊 MODEL RESPONSE - Top {len(current_predictions)} predictions:"
                    )
                    print("   " + "-" * 66)
                    for i, (keyword, probability) in enumerate(current_predictions, 1):
                        bar_length = int(probability * 30)
                        bar = "█" * bar_length + "░" * (30 - bar_length)
                        print(f"   {i}. {keyword:45s} {bar} {probability*100:5.1f}%")
                    print("   " + "-" * 66)

                print(
                    f"\n💡 NEXT STEP: Type '1', '2', or '3' to select, or type your own keyword"
                )
                continue

            # Handle custom keyword input (not a number, not a command)
            # User is adding their own keyword that wasn't in predictions
            custom_keyword = line.strip()
            if custom_keyword:
                sequence_history.append(custom_keyword)
                print(f"\n✅ REQUEST RECEIVED: Added custom keyword")
                print(f"   Added: '{custom_keyword}'")
                print(f"   Updated sequence: {' → '.join(sequence_history)}")

                # Predict next based on updated sequence
                context_keywords = (
                    sequence_history[-context_size:]
                    if len(sequence_history) >= context_size
                    else sequence_history
                )
                print(
                    f"\n🔄 MODEL PROCESSING: Predicting next keyword(s) with depth {depth}..."
                )

                if depth > 1:
                    hierarchical_predictions = predict_next_keyword_with_depth(
                        model, tokenizer, context_keywords, top_k=3, depth=depth
                    )
                    # Apply rules if available
                    if keyword_rules:
                        hierarchical_predictions = (
                            apply_rules_to_hierarchical_predictions(
                                hierarchical_predictions,
                                context_keywords,
                                keyword_rules,
                            )
                        )
                    current_predictions = [
                        (p["keyword"], p["probability"])
                        for p in hierarchical_predictions
                    ]

                    print(
                        f"\n📊 MODEL RESPONSE - Top {len(current_predictions)} predictions (depth {depth}):"
                    )
                    print("   " + "-" * 66)
                    display_hierarchical_predictions(hierarchical_predictions)
                    print("   " + "-" * 66)
                else:
                    current_predictions = predict_next_keyword(
                        model, tokenizer, context_keywords
                    )
                    # Apply rules if available
                    if keyword_rules:
                        current_predictions = keyword_rules.apply_rules(
                            current_predictions, context_keywords
                        )
                    print(
                        f"\n📊 MODEL RESPONSE - Top {len(current_predictions)} predictions:"
                    )
                    print("   " + "-" * 66)
                    for i, (keyword, probability) in enumerate(current_predictions, 1):
                        bar_length = int(probability * 30)
                        bar = "█" * bar_length + "░" * (30 - bar_length)
                        print(f"   {i}. {keyword:45s} {bar} {probability*100:5.1f}%")
                    print("   " + "-" * 66)

                print(
                    f"\n💡 NEXT STEP: Type '1', '2', or '3' to select, or type your own keyword"
                )
                continue

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ ERROR: {e}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test LSTM keyword prediction model")
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help="Path to trained model file",
    )
    parser.add_argument(
        "--tokenizer",
        "-t",
        type=str,
        default=DEFAULT_TOKENIZER_PATH,
        help="Path to tokenizer JSON file",
    )
    parser.add_argument(
        "--depth",
        "-d",
        type=int,
        default=1,
        help="Depth for hierarchical prediction (default: 1, shows only current level)",
    )
    parser.add_argument(
        "--rules",
        "-r",
        type=str,
        default=DEFAULT_RULES_FILE,
        help="Path to keyword rules JSON file (optional)",
    )

    args = parser.parse_args()

    if args.depth < 1:
        print("❌ Error: Depth must be >= 1")
        exit(1)

    try:
        print("Loading model and tokenizer...")
        model, tokenizer = load_model_and_tokenizer(args.model, args.tokenizer)
        print("✅ Model and tokenizer loaded successfully!\n")
        cli_loop(model, tokenizer, depth=args.depth, rules_file=args.rules)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
