# Incremental Data Update Guide

## Overview

All scripts now support **incremental updates** - you can add new data without losing existing data or retraining from scratch!

## ✅ What's Supported

### 1. **Extract Keywords** (`extract_keywords.py`)
- ✅ **Append mode**: Add new XML files to existing dataset
- ✅ **Merge mode**: Add new data and automatically remove duplicates

### 2. **Clean Dataset** (`clean_keyword_dataset.py`)
- ✅ **Append mode**: Clean new data and merge with existing cleaned dataset

### 3. **Train Model** (`train_lstm_model2.py`)
- ✅ **Continue training**: Load existing model and continue training with new data
- ✅ **Vocabulary expansion**: Automatically handles new keywords
- ✅ **Weight transfer**: Preserves learned weights when possible

## 📖 Usage Examples

### Scenario 1: New XML Files Arrive

```bash
# Extract new XML files and merge with existing dataset (removes duplicates)
python extract_keywords.py --folder /path/to/new/xml/files \
    --output keyword_dataset.json --merge

# Clean the updated dataset (appends to existing cleaned data)
python clean_keyword_dataset.py --input keyword_dataset.json \
    --output keyword_dataset_cleaned.json --append

# Continue training with new data (incremental learning)
python train_lstm_model2.py --input keyword_dataset_cleaned.json \
    --continue-training --epochs 10
```

### Scenario 2: Simple Append (No Deduplication)

```bash
# Just append new data (may have duplicates)
python extract_keywords.py --folder /path/to/new/xml \
    --output keyword_dataset.json --append
```

### Scenario 3: Full Incremental Pipeline

```bash
# One command to do everything incrementally
python run_pipeline.py --xml-folder /path/to/new/xml \
    --steps extract,clean,train \
    --append-extract --append-clean --continue-training
```

## 🔧 Detailed Options

### Extract Keywords

```bash
python extract_keywords.py [OPTIONS]

Options:
  --append, -a          Append to existing file (keeps duplicates)
  --merge               Merge with existing file (removes duplicates)
  
Examples:
  # Overwrite (default behavior)
  python extract_keywords.py --folder /path/to/xml --output dataset.json
  
  # Append (may have duplicates)
  python extract_keywords.py --folder /path/to/xml --output dataset.json --append
  
  # Merge (removes duplicates)
  python extract_keywords.py --folder /path/to/xml --output dataset.json --merge
```

### Clean Dataset

```bash
python clean_keyword_dataset.py [OPTIONS]

Options:
  --append, -a          Append cleaned data to existing cleaned file (removes duplicates)
  
Examples:
  # Overwrite (default)
  python clean_keyword_dataset.py --input dataset.json --output cleaned.json
  
  # Append and merge
  python clean_keyword_dataset.py --input dataset.json --output cleaned.json --append
```

### Train Model (Incremental Learning)

```bash
python train_lstm_model2.py [OPTIONS]

Options:
  --continue-training   Continue training from existing model
  --existing-model      Path to existing model (auto-detected if not specified)
  --existing-tokenizer  Path to existing tokenizer (auto-detected if not specified)
  
Examples:
  # Train from scratch (default)
  python train_lstm_model2.py --input cleaned.json
  
  # Continue training (incremental learning)
  python train_lstm_model2.py --input cleaned.json --continue-training
  
  # Continue with custom paths
  python train_lstm_model2.py --input cleaned.json \
      --continue-training \
      --existing-model old_model.keras \
      --existing-tokenizer old_tokenizer.json \
      --model-output new_model.keras
```

## 🎯 How It Works

### Extraction & Cleaning
- **Append mode**: Simply adds new data to existing file
- **Merge mode**: Uses deduplication based on:
  - Test name + keyword sequence (for extraction)
  - Keyword sequence only (for cleaning)

### Incremental Training
1. **Loads existing model** and tokenizer
2. **Extends vocabulary** if new keywords are found
3. **Handles vocabulary expansion**:
   - If vocab size unchanged → continues training with existing weights
   - If vocab expanded → rebuilds model but transfers compatible layer weights
4. **Continues training** with new data

## ⚠️ Important Notes

1. **Vocabulary Expansion**: When new keywords are added, the model's embedding layer needs to be rebuilt. The script automatically:
   - Transfers weights from compatible layers (LSTM, Dense)
   - Initializes new embedding vectors for new keywords
   - Preserves learned patterns in other layers

2. **Deduplication**: 
   - `--merge` in extraction: removes duplicates based on (test_name, keywords)
   - `--append` in cleaning: removes duplicates based on keywords sequence only

3. **Model Compatibility**:
   - Context size must match (or model will be rebuilt)
   - Architecture should be similar for best weight transfer

4. **Performance**:
   - Incremental training is faster than training from scratch
   - Use fewer epochs for incremental updates (e.g., 5-10 epochs)

## 📊 Recommended Workflow

### Initial Setup (First Time)
```bash
# 1. Extract all XML files
python extract_keywords.py --folder /path/to/xml --output dataset.json

# 2. Inspect
python inspect_keyword_dataset.py --file dataset.json

# 3. Clean
python clean_keyword_dataset.py --input dataset.json --output cleaned.json

# 4. Train
python train_lstm_model2.py --input cleaned.json --epochs 30
```

### Regular Updates (When New Data Arrives)
```bash
# 1. Extract new XML files (merge to avoid duplicates)
python extract_keywords.py --folder /path/to/new/xml \
    --output dataset.json --merge

# 2. Clean new data (append to existing)
python clean_keyword_dataset.py --input dataset.json \
    --output cleaned.json --append

# 3. Continue training (fewer epochs needed)
python train_lstm_model2.py --input cleaned.json \
    --continue-training --epochs 5
```

## 🚀 Benefits

✅ **No data loss**: Old data is preserved  
✅ **Faster updates**: No need to reprocess everything  
✅ **Incremental learning**: Model improves with new data  
✅ **Automatic deduplication**: Prevents duplicate entries  
✅ **Vocabulary expansion**: Handles new keywords automatically  

## 🔍 Troubleshooting

**Q: Model not loading?**  
A: Check that the model file exists and is compatible. The script will rebuild if needed.

**Q: Vocabulary size mismatch?**  
A: This is normal when new keywords are added. The script automatically handles it.

**Q: Duplicates still appearing?**  
A: Use `--merge` flag in extraction, or `--append` in cleaning (which deduplicates).

**Q: Training too slow?**  
A: Use fewer epochs for incremental updates (5-10 instead of 30).

