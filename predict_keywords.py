import json
import numpy as np
import tensorflow as tf
import argparse
import os
from tensorflow.keras.preprocessing.text import tokenizer_from_json
from tensorflow.keras.preprocessing.sequence import pad_sequences

DEFAULT_MODEL_PATH = "keyword_predictor.keras"
DEFAULT_TOKENIZER_PATH = "tokenizer.json"


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
        top_indices = predictions.argsort()[-top_k:][::-1]
        results = [
            (index_to_word.get(idx, "<OOV>"), float(predictions[idx]))
            for idx in top_indices
        ]
        return results
    except Exception as e:
        raise RuntimeError(f"Error during prediction: {e}")


def cli_loop(model, tokenizer):
    """Interactive CLI loop for keyword prediction."""
    context_size = model.input_shape[1]

    print("=" * 60)
    print(" Neural Keyword Predictor (CLI)")
    print("=" * 60)
    print(
        f"Model expects {context_size} previous keywords to predict the next keyword."
    )
    print("Enter comma-separated keywords (e.g., keyword1, keyword2)")
    print(
        f"If you provide more than {context_size}, only the last {context_size} will be used."
    )
    print("Type 'exit' or 'quit' to quit.\n")

    while True:
        try:
            line = input(f"Context ({context_size} keywords) > ").strip()
            if line.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            if not line:
                print("Please provide at least one keyword.\n")
                continue

            context_keywords = [x.strip() for x in line.split(",") if x.strip()]
            if len(context_keywords) == 0:
                print("Please provide at least one keyword.\n")
                continue

            results = predict_next_keyword(model, tokenizer, context_keywords)
            print(
                f"\nTop predictions (based on last {min(len(context_keywords), context_size)} keyword(s)):"
            )
            for keyword, probability in results:
                print(f"  {keyword:50s} ({probability*100:.2f}%)")
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


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

    args = parser.parse_args()

    try:
        print("Loading model and tokenizer...")
        model, tokenizer = load_model_and_tokenizer(args.model, args.tokenizer)
        print("✅ Model and tokenizer loaded successfully!\n")
        cli_loop(model, tokenizer)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
