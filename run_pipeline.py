#!/usr/bin/env python3
"""
Master pipeline script that orchestrates the entire ML workflow:
1. Extract keywords from XML files
2. Inspect the dataset
3. Clean the dataset
4. Train the LSTM model
5. (Optional) Test the model

This script provides the convenience of a single entry point while
maintaining the modularity of individual scripts.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\n❌ Error in {description}")
        sys.exit(1)

    print(f"✅ {description} completed successfully\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run the complete ML pipeline for keyword prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with defaults
  python run_pipeline.py --xml-folder /path/to/xml/files

  # Run specific steps only
  python run_pipeline.py --xml-folder /path/to/xml --steps extract,clean,train

  # Skip inspection and testing
  python run_pipeline.py --xml-folder /path/to/xml --skip-steps inspect,test

  # Custom file paths
  python run_pipeline.py --xml-folder /path/to/xml \\
      --output-dataset my_dataset.json \\
      --cleaned-dataset my_cleaned.json \\
      --model-output my_model.keras
        """,
    )

    # Input/Output paths
    parser.add_argument(
        "--xml-folder",
        "-x",
        type=str,
        required=True,
        help="Folder containing Robot Framework XML files",
    )
    parser.add_argument(
        "--output-dataset",
        "-o",
        type=str,
        default="keyword_dataset.json",
        help="Output path for extracted dataset",
    )
    parser.add_argument(
        "--cleaned-dataset",
        "-c",
        type=str,
        default="keyword_dataset_cleaned.json",
        help="Output path for cleaned dataset",
    )
    parser.add_argument(
        "--model-output",
        "-m",
        type=str,
        default="keyword_predictor.keras",
        help="Output path for trained model",
    )
    parser.add_argument(
        "--tokenizer-output",
        "-t",
        type=str,
        default="tokenizer.json",
        help="Output path for tokenizer",
    )

    # Pipeline control
    parser.add_argument(
        "--steps",
        type=str,
        default="all",
        help="Comma-separated steps to run: extract,inspect,clean,train,test (default: all)",
    )
    parser.add_argument(
        "--skip-steps",
        type=str,
        default="",
        help="Comma-separated steps to skip: extract,inspect,clean,train,test",
    )

    # Training parameters
    parser.add_argument(
        "--context-size",
        type=int,
        default=2,
        help="Number of previous keywords for prediction",
    )
    parser.add_argument(
        "--batch-size", type=int, default=512, help="Training batch size"
    )
    parser.add_argument(
        "--epochs", type=int, default=30, help="Number of training epochs"
    )
    parser.add_argument(
        "--validation-split", type=float, default=0.2, help="Validation split ratio"
    )

    # Flags
    parser.add_argument(
        "--interactive-test",
        action="store_true",
        help="Run interactive CLI test after training",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )

    args = parser.parse_args()

    # Determine which steps to run
    all_steps = ["extract", "inspect", "clean", "train", "test"]

    if args.steps.lower() == "all":
        steps_to_run = all_steps.copy()
    else:
        steps_to_run = [s.strip() for s in args.steps.split(",")]
        # Validate steps
        invalid = [s for s in steps_to_run if s not in all_steps]
        if invalid:
            print(f"❌ Invalid steps: {invalid}")
            print(f"Valid steps: {', '.join(all_steps)}")
            sys.exit(1)

    # Remove skipped steps
    if args.skip_steps:
        skip_list = [s.strip() for s in args.skip_steps.split(",")]
        steps_to_run = [s for s in steps_to_run if s not in skip_list]

    if not steps_to_run:
        print("❌ No steps to run after filtering!")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("ML PIPELINE EXECUTION PLAN")
    print(f"{'='*60}")
    print(f"Steps to execute: {', '.join(steps_to_run)}")
    print(f"XML folder: {args.xml_folder}")
    print(f"Output dataset: {args.output_dataset}")
    print(f"Cleaned dataset: {args.cleaned_dataset}")
    print(f"Model output: {args.model_output}")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("DRY RUN MODE - No actual execution")
        return

    # Check if XML folder exists
    if "extract" in steps_to_run:
        if not os.path.exists(args.xml_folder):
            print(f"❌ XML folder not found: {args.xml_folder}")
            sys.exit(1)

    # Step 1: Extract keywords
    if "extract" in steps_to_run:
        cmd = [
            sys.executable,
            "extract_keywords.py",
            "--folder",
            args.xml_folder,
            "--output",
            args.output_dataset,
        ]
        run_command(cmd, "Extracting keywords from XML files")

    # Step 2: Inspect dataset
    if "inspect" in steps_to_run:
        cmd = [
            sys.executable,
            "inspect_keyword_dataset.py",
            "--file",
            args.output_dataset,
        ]
        run_command(cmd, "Inspecting dataset statistics")

    # Step 3: Clean dataset
    if "clean" in steps_to_run:
        cmd = [
            sys.executable,
            "clean_keyword_dataset.py",
            "--input",
            args.output_dataset,
            "--output",
            args.cleaned_dataset,
        ]
        run_command(cmd, "Cleaning dataset")

    # Step 4: Train model
    if "train" in steps_to_run:
        # Check if cleaned dataset exists
        if not os.path.exists(args.cleaned_dataset):
            print(f"❌ Cleaned dataset not found: {args.cleaned_dataset}")
            print("   Run 'clean' step first or provide existing cleaned dataset")
            sys.exit(1)

        cmd = [
            sys.executable,
            "train_keyword_predictor.py",
            "--input",
            args.cleaned_dataset,
            "--context-size",
            str(args.context_size),
            "--batch-size",
            str(args.batch_size),
            "--epochs",
            str(args.epochs),
            "--validation-split",
            str(args.validation_split),
            "--model-output",
            args.model_output,
            "--tokenizer-output",
            args.tokenizer_output,
        ]
        run_command(cmd, "Training keyword predictor model")

    # Step 5: Test model (interactive)
    if "test" in steps_to_run or args.interactive_test:
        # Check if model exists
        if not os.path.exists(args.model_output):
            print(f"❌ Model not found: {args.model_output}")
            print("   Run 'train' step first")
            sys.exit(1)

        cmd = [
            sys.executable,
            "predict_keywords.py",
            "--model",
            args.model_output,
            "--tokenizer",
            args.tokenizer_output,
        ]
        print(f"\n{'='*60}")
        print("STEP: Interactive Model Testing")
        print(f"{'='*60}")
        print("Starting interactive CLI...\n")
        subprocess.run(cmd)

    print(f"\n{'='*60}")
    print("✅ PIPELINE COMPLETED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"Model saved to: {args.model_output}")
    print(f"Tokenizer saved to: {args.tokenizer_output}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
