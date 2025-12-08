import json
import numpy as np
import ijson
import argparse
import os
from math import ceil

# Set TensorFlow log level to reduce verbose output (keep warnings for important issues)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "1"  # Only show WARNING and ERROR

import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer, tokenizer_from_json
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split


# ---------------------------
# OPTIMIZED DATA LOADING
# ---------------------------
def load_and_prepare_sequences(file_path, context_size=2):
    """Load keyword sequences from JSON file and filter valid sequences.

    Args:
        file_path: Path to JSON file containing keyword sequences
        context_size: Minimum sequence length required (context_size + 1)

    Returns:
        List of keyword sequences (each is a list of keywords)
    """
    print("Loading and preparing sequences...")
    all_sequences = []

    with open(file_path, "rb") as f:
        parser = ijson.items(f, "item")
        for test_case in parser:
            keyword_sequence = test_case.get("keywords", [])
            if keyword_sequence and len(keyword_sequence) >= context_size + 1:
                all_sequences.append(keyword_sequence)

    print(f"✅ Loaded {len(all_sequences)} valid sequences")
    return all_sequences


def create_training_samples(sequences, tokenizer, context_size=2):
    """Convert keyword sequences to (X, y) training pairs.

    Args:
        sequences: List of keyword sequences
        tokenizer: Fitted tokenizer
        context_size: Number of previous keywords to use as context

    Returns:
        Tuple of (X, y) numpy arrays for training
    """
    X_samples, y_samples = [], []

    for keyword_sequence in sequences:
        token_sequence = tokenizer.texts_to_sequences([keyword_sequence])[0]
        # Create training pairs: use context_size previous keywords to predict next
        for i in range(context_size, len(token_sequence)):
            X_samples.append(token_sequence[i - context_size : i])
            y_samples.append(token_sequence[i])

    return np.array(X_samples), np.array(y_samples)


# ---------------------------
# OPTIMIZED DATA GENERATOR (for large datasets)
# ---------------------------
def data_generator_cached(X, y, batch_size=512, shuffle=True):
    """Efficient generator from cached data."""
    indices = np.arange(len(X))
    if shuffle:
        np.random.shuffle(indices)

    while True:
        for start_idx in range(0, len(X), batch_size):
            end_idx = min(start_idx + batch_size, len(X))
            batch_indices = indices[start_idx:end_idx]
            yield X[batch_indices], y[batch_indices]


def train_model(
    json_path,
    context_size=2,
    batch_size=512,
    epochs=30,
    validation_split=0.2,
    embedding_dim=64,
    lstm_units=64,
    model_save_path="keyword_predictor.keras",
    tokenizer_save_path="tokenizer.json",
    continue_training=False,
    existing_model_path=None,
    existing_tokenizer_path=None,
):
    """Main training function with support for incremental learning."""

    # ---------------------------
    # STEP 1: Load sequences
    # ---------------------------
    sequences = load_and_prepare_sequences(json_path, context_size)

    if len(sequences) == 0:
        raise ValueError("No valid sequences found in dataset!")

    # ---------------------------
    # STEP 2: Build or load tokenizer
    # ---------------------------
    print("\nBuilding/updating tokenizer vocabulary...")

    if (
        continue_training
        and existing_tokenizer_path
        and os.path.exists(existing_tokenizer_path)
    ):
        # Load existing tokenizer
        print(f"📂 Loading existing tokenizer from {existing_tokenizer_path}")
        with open(existing_tokenizer_path, "r", encoding="utf-8") as f:
            tokenizer_data = json.load(f)
            tokenizer = tokenizer_from_json(json.dumps(tokenizer_data))

        # Extend vocabulary with new sequences
        old_vocab_size = len(tokenizer.word_index) + 1
        tokenizer.fit_on_texts(sequences)  # This extends the vocabulary
        new_vocab_size = len(tokenizer.word_index) + 1

        if new_vocab_size > old_vocab_size:
            print(
                f"📈 Vocabulary expanded: {old_vocab_size} → {new_vocab_size} (+{new_vocab_size - old_vocab_size} new words)"
            )
        else:
            print(f"✅ Vocabulary unchanged: {old_vocab_size} words")

        vocab_size = new_vocab_size
    else:
        # Build new tokenizer
        tokenizer = Tokenizer(oov_token="<OOV>")
        tokenizer.fit_on_texts(sequences)
        vocab_size = len(tokenizer.word_index) + 1
        print(f"✅ Vocabulary size: {vocab_size}")

    # ---------------------------
    # STEP 3: Create training samples
    # ---------------------------
    print("\nCreating training samples...")
    X, y = create_training_samples(sequences, tokenizer, context_size)
    print(f"✅ Created {len(X)} training samples")

    # ---------------------------
    # STEP 4: Split train/validation
    # ---------------------------
    if validation_split > 0:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, shuffle=True
        )
        print(f"✅ Train samples: {len(X_train)}, Validation samples: {len(X_val)}")
    else:
        X_train, X_val, y_train, y_val = X, None, y, None
        print(f"✅ Using all {len(X_train)} samples for training (no validation split)")

    # Pad sequences
    X_train = pad_sequences(X_train, maxlen=context_size, padding="pre")
    if X_val is not None:
        X_val = pad_sequences(X_val, maxlen=context_size, padding="pre")

    # ---------------------------
    # STEP 5: Load or build model
    # ---------------------------
    model = None
    vocab_expanded = False

    if (
        continue_training
        and existing_model_path
        and os.path.exists(existing_model_path)
    ):
        print(f"\n📂 Loading existing model from {existing_model_path}")
        try:
            model = load_model(existing_model_path)

            # Check if vocabulary expanded
            old_vocab_size = model.layers[0].input_dim  # Embedding layer input_dim
            if vocab_size > old_vocab_size:
                print(f"⚠️  Vocabulary expanded ({old_vocab_size} → {vocab_size})")
                print("   Rebuilding model to accommodate new vocabulary...")
                vocab_expanded = True
                # Need to rebuild model with new vocab size
                model = None  # Will rebuild below
            else:
                print(f"✅ Model loaded successfully (vocab size: {old_vocab_size})")
                # Verify context size matches
                if model.input_shape[1] != context_size:
                    print(
                        f"⚠️  Context size mismatch! Model expects {model.input_shape[1]}, got {context_size}"
                    )
                    print("   Rebuilding model with correct context size...")
                    model = None
        except Exception as e:
            print(f"⚠️  Error loading model: {e}")
            print("   Building new model...")
            model = None

    if model is None or vocab_expanded:
        print("\nBuilding model...")
        model = Sequential(
            [
                Embedding(vocab_size, embedding_dim, input_length=context_size),
                LSTM(lstm_units, return_sequences=False),
                Dropout(0.2),
                Dense(vocab_size, activation="softmax"),
            ]
        )
        model.compile(
            loss="sparse_categorical_crossentropy",
            optimizer="adam",
            metrics=["accuracy"],
        )

        # If continuing training and vocab didn't expand, try to load weights
        if (
            continue_training
            and existing_model_path
            and os.path.exists(existing_model_path)
            and not vocab_expanded
        ):
            try:
                old_model = load_model(existing_model_path)
                # Copy weights from compatible layers
                for i, (old_layer, new_layer) in enumerate(
                    zip(old_model.layers, model.layers)
                ):
                    if i == 0:  # Embedding layer - only copy if vocab size matches
                        if old_layer.input_dim == new_layer.input_dim:
                            new_layer.set_weights(old_layer.get_weights())
                            print(
                                f"   ✅ Copied weights from layer {i} ({old_layer.__class__.__name__})"
                            )
                    elif i < len(old_model.layers) - 1:  # Middle layers
                        try:
                            new_layer.set_weights(old_layer.get_weights())
                            print(
                                f"   ✅ Copied weights from layer {i} ({old_layer.__class__.__name__})"
                            )
                        except:
                            print(f"   ⚠️  Could not copy weights from layer {i}")
                print("   ✅ Transferred weights from existing model")
            except Exception as e:
                print(f"   ⚠️  Could not transfer weights: {e}")
                print("   Starting training from scratch")

    model.summary()

    # ---------------------------
    # STEP 6: Training
    # ---------------------------
    print("\nStarting training...")
    callbacks = [
        EarlyStopping(
            monitor="val_loss" if X_val is not None else "loss",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        )
    ]

    # Add checkpointing
    if model_save_path:
        checkpoint = ModelCheckpoint(
            model_save_path.replace(".keras", "_best.keras"),
            monitor="val_loss" if X_val is not None else "loss",
            save_best_only=True,
            verbose=1,
        )
        callbacks.append(checkpoint)

    # Use generator for large datasets, direct arrays for smaller ones
    if len(X_train) > 100000:
        # Use generator for very large datasets
        steps_per_epoch = ceil(len(X_train) / batch_size)
        train_gen = data_generator_cached(
            X_train, y_train, batch_size=batch_size, shuffle=True
        )

        if X_val is not None:
            val_steps = ceil(len(X_val) / batch_size)
            val_gen = data_generator_cached(
                X_val, y_val, batch_size=batch_size, shuffle=False
            )
            history = model.fit(
                train_gen,
                steps_per_epoch=steps_per_epoch,
                validation_data=val_gen,
                validation_steps=val_steps,
                epochs=epochs,
                callbacks=callbacks,
                verbose=1,
            )
        else:
            history = model.fit(
                train_gen,
                steps_per_epoch=steps_per_epoch,
                epochs=epochs,
                callbacks=callbacks,
                verbose=1,
            )
    else:
        # Direct training for smaller datasets (faster)
        if X_val is not None:
            history = model.fit(
                X_train,
                y_train,
                validation_data=(X_val, y_val),
                batch_size=batch_size,
                epochs=epochs,
                callbacks=callbacks,
                verbose=1,
            )
        else:
            history = model.fit(
                X_train,
                y_train,
                batch_size=batch_size,
                epochs=epochs,
                callbacks=callbacks,
                verbose=1,
            )

    # ---------------------------
    # STEP 7: Save model + tokenizer
    # ---------------------------
    print("\nSaving model and tokenizer...")
    # Ensure we use native Keras format (.keras) - this is the recommended format
    # and avoids HDF5 deprecation warnings
    if not model_save_path.endswith(".keras"):
        if model_save_path.endswith((".h5", ".hdf5")):
            # Replace legacy format with .keras
            model_save_path = model_save_path.rsplit(".", 1)[0] + ".keras"
        else:
            # Add .keras extension if no extension provided
            model_save_path = model_save_path + ".keras"

    # Save in native Keras format using tf.keras.saving.save_model
    # This explicitly uses the new format and avoids HDF5 deprecation warnings
    tf.keras.saving.save_model(model, model_save_path)

    with open(tokenizer_save_path, "w", encoding="utf-8") as f:
        f.write(tokenizer.to_json())

    print(f"✅ Model saved to {model_save_path}")
    print(f"✅ Tokenizer saved to {tokenizer_save_path}")
    print("🎉 Model training complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train LSTM model for keyword prediction"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="keyword_dataset_cleaned.json",
        help="Input JSON dataset file",
    )
    parser.add_argument(
        "--context-size",
        "-c",
        type=int,
        default=2,
        help="Number of previous keywords to use for prediction",
    )
    parser.add_argument(
        "--batch-size", "-b", type=int, default=512, help="Batch size for training"
    )
    parser.add_argument(
        "--epochs", "-e", type=int, default=30, help="Number of training epochs"
    )
    parser.add_argument(
        "--validation-split",
        "-v",
        type=float,
        default=0.2,
        help="Validation split ratio (0.0 to disable)",
    )
    parser.add_argument(
        "--embedding-dim", type=int, default=64, help="Embedding dimension"
    )
    parser.add_argument(
        "--lstm-units", type=int, default=64, help="Number of LSTM units"
    )
    parser.add_argument(
        "--model-output",
        "-m",
        type=str,
        default="keyword_predictor.keras",
        help="Output model file path",
    )
    parser.add_argument(
        "--tokenizer-output",
        "-t",
        type=str,
        default="tokenizer.json",
        help="Output tokenizer file path",
    )
    parser.add_argument(
        "--continue-training",
        action="store_true",
        help="Continue training from existing model (incremental learning)",
    )
    parser.add_argument(
        "--existing-model",
        type=str,
        help="Path to existing model to continue training from",
    )
    parser.add_argument(
        "--existing-tokenizer",
        type=str,
        help="Path to existing tokenizer to extend vocabulary from",
    )

    args = parser.parse_args()

    # Auto-detect existing model/tokenizer if continue-training is set
    if args.continue_training:
        if not args.existing_model:
            args.existing_model = args.model_output
        if not args.existing_tokenizer:
            args.existing_tokenizer = args.tokenizer_output

    try:
        train_model(
            json_path=args.input,
            context_size=args.context_size,
            batch_size=args.batch_size,
            epochs=args.epochs,
            validation_split=args.validation_split,
            embedding_dim=args.embedding_dim,
            lstm_units=args.lstm_units,
            model_save_path=args.model_output,
            tokenizer_save_path=args.tokenizer_output,
            continue_training=args.continue_training,
            existing_model_path=args.existing_model,
            existing_tokenizer_path=args.existing_tokenizer,
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
