# Dataset Generation and Training Flow

This document explains how the dataset is generated, how it's used for training, and how duplicates and old data are handled.

## 📊 Dataset Generation Flow

### Step 1: Extract Keywords (`extract_keywords.py`)

**What it does:**
- Scans all XML files in the specified folder (recursively)
- Extracts test case names and their keyword sequences from Robot Framework `output.xml` files
- Includes suite setup keywords (at the beginning) and suite teardown keywords (at the end) of each test
- Normalizes keyword names (lowercase, replace spaces with underscores)
- Outputs JSON file with structure: `[{"test_name": "...", "keywords": ["kw1", "kw2", ...]}, ...]`

**Current Behavior in Jenkins:**
```groovy
extract_keywords.py --folder ${XML_FOLDER} --output ${DATASET_OUTPUT}
```
- **⚠️ OVERWRITES** the dataset file each time
- **No `--append` or `--merge` flags** - old data is **completely replaced**

**Available Options (not currently used in Jenkins):**
- `--append`: Append new data to existing file (may create duplicates)
- `--merge`: Merge new data with existing, automatically remove duplicates based on `(test_name, keywords)` tuple

### Step 2: Clean Dataset (`clean_keyword_dataset.py`)

**What it does:**
- Filters out blacklisted keywords (e.g., `builtin.*`, `seleniumlibrary.*`)
- Applies whitelist (only keeps keywords from allowed libraries like `login1.*`, `policy1.*`, etc.)
- Removes common junk keywords (`sleep`, `log`, `log_to_console`, etc.)
- **Deduplicates consecutive repeated keywords** (from retry mechanisms)
- **Removes duplicate sequences** - if two test cases have the exact same keyword sequence, only one is kept
- Filters out sequences shorter than `MIN_SEQUENCE_LENGTH` (default: 2)

**Duplicate Handling:**
```python
# Line 116-122 in clean_keyword_dataset.py
seen_sequences = set()  # stores tuples of keywords (normalized) to dedupe

# For each sequence:
seq_key = tuple(cleaned_seq)
if seq_key in seen_sequences:
    duplicates_skipped += 1
    removed_counters["duplicate_sequence"] += 1
    continue  # Skip this duplicate
seen_sequences.add(seq_key)
```

**Current Behavior in Jenkins:**
```groovy
clean_keyword_dataset.py --input ${DATASET_OUTPUT} --output ${CLEANED_DATASET}
```
- **⚠️ OVERWRITES** the cleaned dataset file each time
- **No `--append` flag** - old cleaned data is **completely replaced**

**Available Options (not currently used in Jenkins):**
- `--append`: Load existing cleaned dataset, clean new data, merge and deduplicate

### Step 3: Train Model (`train_keyword_predictor.py`)

**What it does:**
- Loads all sequences from the cleaned dataset JSON file
- Builds or loads tokenizer (converts keywords to numbers)
- Creates training samples: uses last `context_size` (default: 2) keywords to predict the next keyword
- Trains LSTM model from scratch (or continues training if `--continue-training` is used)
- Saves model and tokenizer

**Current Behavior in Jenkins:**
```groovy
train_keyword_predictor.py --input ${CLEANED_DATASET} \
    --model-output ${MODEL_DIR}/keyword_predictor_v${VERSION}_${TIMESTAMP}.keras \
    --tokenizer-output ${TOKENIZER_OUTPUT}
```
- **⚠️ Trains from scratch** each time (no `--continue-training` flag)
- **⚠️ Builds new tokenizer** each time (no existing tokenizer loaded)
- Model is saved with timestamp, but training always starts fresh

**Available Options (not currently used in Jenkins):**
- `--continue-training`: Load existing model and continue training
- `--existing-tokenizer-path`: Load existing tokenizer and extend vocabulary

## 🔄 Current Data Flow (Jenkins Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│ Week 1: First Training Run                                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Extract Keywords                                          │
│    Input:  XML files in folder                               │
│    Output: keyword_dataset.json (1000 test cases)            │
│    Status: ✅ Created                                         │
│                                                               │
│ 2. Clean Dataset                                             │
│    Input:  keyword_dataset.json (1000 test cases)            │
│    Output: keyword_dataset_cleaned.json (800 sequences)     │
│    Status: ✅ Removed 200 duplicates/short sequences         │
│                                                               │
│ 3. Train Model                                               │
│    Input:  keyword_dataset_cleaned.json (800 sequences)      │
│    Output: keyword_predictor_v1_20250101_020000.keras       │
│    Status: ✅ Trained from scratch                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Week 2: Second Training Run (NEW DATA ARRIVES)              │
├─────────────────────────────────────────────────────────────┤
│ 1. Extract Keywords                                          │
│    Input:  XML files in folder (now has 200 new test cases)   │
│    Output: keyword_dataset.json (200 test cases) ⚠️         │
│    Status: ❌ OLD DATA LOST! Only new data extracted         │
│                                                               │
│ 2. Clean Dataset                                             │
│    Input:  keyword_dataset.json (200 test cases)             │
│    Output: keyword_dataset_cleaned.json (150 sequences)     │
│    Status: ❌ OLD CLEANED DATA LOST!                        │
│                                                               │
│ 3. Train Model                                               │
│    Input:  keyword_dataset_cleaned.json (150 sequences)     │
│    Output: keyword_predictor_v2_20250108_020000.keras       │
│    Status: ❌ Model trained on ONLY new data (150 vs 800)    │
│            Model quality may degrade!                        │
└─────────────────────────────────────────────────────────────┘
```

## ⚠️ Current Issues

### 1. **Old Data is Removed**
- **Problem**: Each Jenkins run **overwrites** the dataset files
- **Impact**: If new XML files are added to the folder, old data is lost
- **Solution Needed**: Use `--merge` flag in `extract_keywords.py` to preserve old data

### 2. **No Incremental Training**
- **Problem**: Model is trained from scratch each time
- **Impact**: 
  - Longer training time
  - Previous learned patterns may be lost
  - Model doesn't benefit from accumulated knowledge
- **Solution Needed**: Use `--continue-training` flag in `train_keyword_predictor.py`

### 3. **Dataset Size May Shrink**
- **Problem**: If XML folder only contains new files (not all files), dataset shrinks
- **Impact**: Model trained on less data than before
- **Solution Needed**: Ensure XML folder contains ALL files (old + new), or use merge mode

## ✅ Duplicate Handling (Already Working)

### Sequence-Level Deduplication
- **Location**: `clean_keyword_dataset.py` lines 216-222
- **Method**: Uses a set to track seen sequences (as tuples)
- **Result**: If two test cases have identical keyword sequences, only one is kept
- **Example**:
  ```json
  // Input:
  [{"keywords": ["login1.login", "policy1.create"]},
   {"keywords": ["login1.login", "policy1.create"]}]  // Duplicate
  
  // Output:
  [{"keywords": ["login1.login", "policy1.create"]}]  // Only one kept
  ```

### Consecutive Duplicate Removal
- **Location**: `clean_keyword_dataset.py` lines 178-193
- **Method**: Removes consecutive repeated keywords in the same sequence
- **Purpose**: Prevents retry mechanisms from inflating keyword frequencies
- **Example**:
  ```json
  // Input:
  {"keywords": ["login1.login", "login1.login", "login1.login", "policy1.create"]}
  
  // Output:
  {"keywords": ["login1.login", "policy1.create"]}  // Consecutive duplicates removed
  ```

## 🔧 Recommended Improvements

### Option 1: Preserve All Data (Recommended)

**Modify Jenkinsfile to use merge mode:**

```groovy
stage('Extract Keywords') {
    echo "📊 Extracting keywords from XML files..."
    sh """
        ${env.PYTHON} extract_keywords.py --folder ${env.XML_FOLDER} \
            --output ${env.DATASET_OUTPUT} --merge || {
            echo "❌ ERROR: Keyword extraction failed!"
            exit 1
        }
    """
}

stage('Clean Dataset') {
    echo "🧹 Cleaning dataset..."
    sh """
        ${env.PYTHON} clean_keyword_dataset.py --input ${env.DATASET_OUTPUT} \
            --output ${env.CLEANED_DATASET} --append || {
            echo "❌ ERROR: Dataset cleaning failed!"
            exit 1
        }
    """
}
```

**Benefits:**
- ✅ Old data preserved when new XML files arrive
- ✅ Dataset grows over time (accumulates knowledge)
- ✅ Duplicates automatically removed
- ✅ Model trained on all available data

### Option 2: Incremental Training

**Modify Jenkinsfile to continue training:**

```groovy
stage('Train Model') {
    echo "🏋️  Training LSTM model..."
    sh """
        ${env.PYTHON} train_keyword_predictor.py \
            --input ${env.CLEANED_DATASET} \
            --model-output ${env.MODEL_DIR}/${env.MODEL_NAME}_v${env.MODEL_VERSION}_${env.MODEL_TIMESTAMP}.keras \
            --tokenizer-output ${env.TOKENIZER_OUTPUT} \
            --continue-training \
            --existing-model-path ${env.MODEL_DIR}/${env.MODEL_NAME}_latest.keras \
            --existing-tokenizer-path ${env.MODEL_DIR}/${env.TOKENIZER_NAME}_latest.json || {
            echo "❌ ERROR: Model training failed!"
            exit 1
        }
    """
}
```

**Benefits:**
- ✅ Faster training (continues from previous weights)
- ✅ Vocabulary expands incrementally
- ✅ Preserves learned patterns

### Option 3: Full Incremental Pipeline (Best)

**Combine both approaches:**
- Use `--merge` in extraction
- Use `--append` in cleaning
- Use `--continue-training` in training

**Result:**
- Dataset accumulates over time
- Model improves incrementally
- No data loss
- Faster training

## 📈 Data Accumulation Strategy

### Current (Overwrite):
```
Week 1: 1000 test cases → 800 sequences → Model v1
Week 2: 200 new test cases → 150 sequences → Model v2 (trained on 150 only!)
Week 3: 300 new test cases → 250 sequences → Model v3 (trained on 250 only!)
```

### With Merge (Accumulate):
```
Week 1: 1000 test cases → 800 sequences → Model v1
Week 2: +200 new → 1000 total (800 old + 200 new) → 950 sequences → Model v2
Week 3: +300 new → 1300 total (1000 old + 300 new) → 1200 sequences → Model v3
```

## 🎯 Summary

| Aspect | Current Behavior | Recommended Behavior |
|--------|------------------|---------------------|
| **Old Data** | ❌ Removed (overwritten) | ✅ Preserved (merged) |
| **Duplicates** | ✅ Removed (in cleaning) | ✅ Removed (in cleaning) |
| **Training** | ❌ From scratch | ✅ Incremental (optional) |
| **Dataset Size** | ⚠️ May shrink | ✅ Grows over time |
| **Model Quality** | ⚠️ May degrade | ✅ Improves over time |

## 🔍 How to Verify Current Behavior

1. **Check dataset file size:**
   ```bash
   ls -lh keyword_dataset.json keyword_dataset_cleaned.json
   ```
   If size decreases between runs, old data is being lost.

2. **Check dataset count:**
   ```bash
   python -c "import json; data=json.load(open('keyword_dataset_cleaned.json')); print(len(data))"
   ```
   If count decreases, sequences are being lost.

3. **Check Jenkins logs:**
   Look for:
   - "Extracted X test cases" - should grow if using merge
   - "Merged: X new test cases added" - confirms merge is working
   - "Total kept: X" - should grow over time

