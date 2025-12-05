# Production-Ready Naming Conventions

## File Naming

All Python files follow descriptive, production-ready naming:

| Old Name | New Name | Purpose |
|----------|----------|---------|
| `train_lstm_model2.py` | `train_keyword_predictor.py` | Train the keyword prediction model |
| `test_lstm_cli.py` | `predict_keywords.py` | Interactive keyword prediction CLI |
| `extract_keywords.py` | ✅ (kept) | Extract keywords from XML files |
| `inspect_keyword_dataset.py` | ✅ (kept) | Analyze dataset statistics |
| `clean_keyword_dataset.py` | ✅ (kept) | Clean and filter dataset |
| `run_pipeline.py` | ✅ (kept) | Orchestrate full pipeline |

## Variable Naming Improvements

### Before → After

| Old | New | Context |
|-----|-----|---------|
| `kw` | `keyword` | Single keyword |
| `k` | `normalized_keyword` | Normalized keyword |
| `seq` | `keyword_sequence` | Sequence of keywords |
| `ctx` | `context_keywords` | Context for prediction |
| `test` | `test_case` | Test case object |
| `elem` | `element` | XML element |
| `X, y` | `X_samples, y_samples` | Training data |
| `preds` | `predictions` | Model predictions |
| `index_word` | `index_to_word` | Token index mapping |
| `token_list` | `token_sequence` | Tokenized sequence |
| `kw_name` | `keyword_name` | Keyword name |
| `lib_name` | `library_name` | Library name |
| `full_kw` | `full_keyword` | Complete keyword with library |
| `current_test` | `current_test_name` | Current test name |
| `keywords` | `keyword_sequence` | List of keywords |

### Constants

All constants follow `UPPER_SNAKE_CASE`:
- `DEFAULT_MODEL_PATH`
- `DEFAULT_TOKENIZER_PATH`
- `DEFAULT_INPUT_FILE`
- `DEFAULT_OUTPUT_FILE`
- `BLACKLIST_KEYWORDS`
- `ALLOWED_KEYWORDS`
- `MIN_SEQUENCE_LENGTH`

### Normalized Sets

Changed from abbreviated to descriptive:
- `BLACKLIST_KEYWORDS_N` → `BLACKLIST_KEYWORDS_NORMALIZED`
- `ALLOWED_KEYWORDS_N` → `ALLOWED_KEYWORDS_NORMALIZED`
- `BLACKLIST_PREFIXES_N` → `BLACKLIST_PREFIXES_NORMALIZED`
- `ALLOWED_LIB_PREFIXES_N` → `ALLOWED_LIB_PREFIXES_NORMALIZED`

## Function Naming

All functions use descriptive, verb-based names:

| Function | Purpose |
|----------|---------|
| `extract_keywords_from_output()` | Extract from XML |
| `collect_all_tests()` | Aggregate all tests |
| `normalize_keyword()` | Normalize keyword string |
| `any_prefix_matches()` | Check prefix matching |
| `clean_dataset()` | Clean dataset |
| `load_and_prepare_sequences()` | Load sequences |
| `create_training_samples()` | Create training pairs |
| `train_model()` | Train the model |
| `load_model_and_tokenizer()` | Load model/tokenizer |
| `predict_next_keyword()` | Predict next keyword |
| `cli_loop()` | Interactive CLI loop |

## Class Naming

Currently no classes, but if added, they should follow `PascalCase`:
- `KeywordExtractor`
- `DatasetCleaner`
- `ModelTrainer`
- `KeywordPredictor`

## Method Naming

Methods should follow `snake_case` with descriptive verbs:
- `extract()`
- `normalize()`
- `clean()`
- `train()`
- `predict()`
- `load()`
- `save()`

## Best Practices Applied

✅ **Descriptive names**: No abbreviations like `kw`, `seq`, `ctx`  
✅ **Consistent style**: All follow Python PEP 8 conventions  
✅ **Clear intent**: Names explain what they represent  
✅ **No magic numbers**: Constants are named  
✅ **Type hints ready**: Names make types obvious  
✅ **Documentation**: All functions have docstrings  

## Summary

The codebase now follows production-ready naming conventions:
- Files: Descriptive, purpose-based names
- Variables: Full words, no abbreviations
- Functions: Verb-based, descriptive
- Constants: UPPER_SNAKE_CASE
- Clear, maintainable, and self-documenting code


