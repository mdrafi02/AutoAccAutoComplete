#!/usr/bin/env python3
"""
Convert Keras model to TensorFlow.js format for use in JavaScript frontend.

This script converts:
1. The Keras model (.keras) to TensorFlow.js format
2. Exports tokenizer data in a JavaScript-compatible format
"""

import json
import argparse
import os
import warnings

# Set TensorFlow log level (keep warnings for debugging)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "1"  # Only show WARNING and ERROR

# Suppress harmless warnings
warnings.filterwarnings(
    "ignore", message=".*failed to lookup keras version.*", category=UserWarning
)
# Suppress HDF5 deprecation warning when loading old model files
# This warning appears when loading models saved in HDF5 format before our fixes.
# The warning will disappear once a new model is trained with the updated code.
warnings.filterwarnings(
    "ignore",
    message=".*You are saving your model as an HDF5 file.*",
    category=UserWarning,
)
# Also suppress absl logging warnings (TensorFlow uses absl for logging)
import logging

logging.getLogger("absl").setLevel(logging.ERROR)

import tensorflow as tf
from tensorflow.keras.preprocessing.text import tokenizer_from_json

DEFAULT_MODEL_PATH = "keyword_predictor.keras"
DEFAULT_TOKENIZER_PATH = "tokenizer.json"
DEFAULT_OUTPUT_DIR = "tfjs_model"


def convert_model_to_tfjs(model_path, output_dir, tfjs_module):
    """Convert Keras model to TensorFlow.js format.

    Uses native Keras format (.keras) which is the recommended format
    and works better with TensorFlow.js conversion.

    Note: If the model file is in HDF5 format (old format), TensorFlow will
    show a warning when loading. This is harmless - the model will still load
    and convert correctly. The warning will disappear once a new model is
    trained with the updated code that saves in native Keras format.
    """
    print(f"Loading model from {model_path}...")
    # Load model - if it's an old HDF5 format model (despite .keras extension),
    # TensorFlow will show a deprecation warning, but it will still load correctly.
    # The 'failed to lookup keras version' warning is also harmless.
    # These warnings will disappear once a new model is trained with the updated code.
    model = tf.keras.models.load_model(model_path)

    print(f"Converting model to TensorFlow.js format...")
    print(f"Output directory: {output_dir}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Convert model to TensorFlow.js
    # This creates model.json and sharded weight files
    tfjs_module.converters.save_keras_model(model, output_dir)

    # Fix InputLayer configuration for TensorFlow.js compatibility
    model_json_path = os.path.join(output_dir, "model.json")
    with open(model_json_path, "r", encoding="utf-8") as f:
        model_data = json.load(f)

    # Fix InputLayer config: convert batch_shape to inputShape
    layers = (
        model_data.get("modelTopology", {})
        .get("model_config", {})
        .get("config", {})
        .get("layers", [])
    )
    for layer in layers:
        if layer.get("class_name") == "InputLayer":
            config = layer.get("config", {})
            if "batch_shape" in config and "inputShape" not in config:
                batch_shape = config.pop("batch_shape")
                # Convert [null, 2] to [2] (remove batch dimension)
                if batch_shape and len(batch_shape) > 1:
                    config["inputShape"] = batch_shape[1:]
                elif batch_shape:
                    config["inputShape"] = batch_shape
                print(f"   Fixed InputLayer: converted batch_shape to inputShape")

    # Save fixed model.json
    with open(model_json_path, "w", encoding="utf-8") as f:
        json.dump(model_data, f, indent=2)

    print(f"✅ Model converted successfully!")
    print(f"   Model files saved to: {output_dir}/")
    print(f"   Main file: {output_dir}/model.json")

    return output_dir


def export_tokenizer_for_js(tokenizer_path, output_path):
    """Export tokenizer in JavaScript-compatible format."""
    print(f"Loading tokenizer from {tokenizer_path}...")

    # Load tokenizer using Keras to properly extract word_index
    from tensorflow.keras.preprocessing.text import tokenizer_from_json

    with open(tokenizer_path, "r", encoding="utf-8") as f:
        tokenizer_json = f.read()

    # Load tokenizer object
    tokenizer = tokenizer_from_json(tokenizer_json)

    # Extract word_index and create index_word mapping
    word_index = tokenizer.word_index
    index_word = {str(v): k for k, v in word_index.items()}

    # Create JavaScript-compatible tokenizer export
    js_tokenizer = {
        "word_index": word_index,
        "index_word": index_word,
        "config": {
            "oov_token": (
                tokenizer.oov_token if hasattr(tokenizer, "oov_token") else "<OOV>"
            ),
            "num_words": (
                tokenizer.num_words if hasattr(tokenizer, "num_words") else None
            ),
        },
    }

    # Save as JSON (JavaScript can import this)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(js_tokenizer, f, indent=2, ensure_ascii=False)

    print(f"✅ Tokenizer exported successfully!")
    print(f"   Tokenizer file: {output_path}")
    print(f"   Vocabulary size: {len(word_index)}")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Keras model to TensorFlow.js format"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help="Path to Keras model file (.keras)",
    )
    parser.add_argument(
        "--tokenizer",
        "-t",
        type=str,
        default=DEFAULT_TOKENIZER_PATH,
        help="Path to tokenizer JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for TensorFlow.js model",
    )
    parser.add_argument(
        "--tokenizer-output",
        type=str,
        default="tokenizer_js.json",
        help="Output path for JavaScript-compatible tokenizer",
    )

    args = parser.parse_args()

    try:
        # Check if tensorflowjs is installed
        try:
            import tensorflowjs as tfjs
        except ImportError:
            print("❌ Error: tensorflowjs package is not installed.")
            print("   Install it with: pip install tensorflowjs")
            exit(1)

        # Convert model
        model_dir = convert_model_to_tfjs(args.model, args.output, tfjs)

        # Export tokenizer
        tokenizer_path = export_tokenizer_for_js(args.tokenizer, args.tokenizer_output)

        print("\n" + "=" * 70)
        print("✅ Conversion Complete!")
        print("=" * 70)
        print(f"\n📁 Files created:")
        print(f"   - TensorFlow.js model: {model_dir}/model.json")
        print(f"   - Tokenizer data: {tokenizer_path}")
        print(f"\n📝 Next steps:")
        print(f"   1. Copy the '{model_dir}' directory to your web server")
        print(f"   2. Copy '{tokenizer_path}' to your web server")
        print(
            f"   3. Use the JavaScript prediction code (see keyword_predictor_tfjs.js)"
        )
        print("=" * 70)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
