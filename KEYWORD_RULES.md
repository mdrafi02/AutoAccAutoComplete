# Keyword Rules Configuration

This document explains how to configure keyword sequence rules to enforce domain constraints on top of ML model predictions.

## Overview

The rule-based system allows you to specify:
- **Required following**: Keywords that MUST follow a given keyword
- **Preferred following**: Keywords that should be boosted in probability
- **Blocked following**: Keywords that should NEVER follow a given keyword
- **Sequence patterns**: Complex multi-keyword sequence rules

## Configuration File

Rules are defined in `keyword_rules.json`. The file structure is:

```json
{
  "description": "Keyword sequence rules",
  "version": "1.0.0",
  
  "required_following": {
    "rules": {
      "keyword1": ["required_keyword1", "required_keyword2"]
    }
  },
  
  "preferred_following": {
    "rules": {
      "keyword1": ["preferred_keyword1", "preferred_keyword2"]
    }
  },
  
  "blocked_following": {
    "rules": {
      "keyword1": ["blocked_keyword1", "blocked_keyword2"]
    }
  },
  
  "sequence_patterns": {
    "patterns": [
      {
        "after": ["keyword1", "keyword2"],
        "then": "required_next_keyword",
        "boost": ["boosted_keyword1"],
        "boost_factor": 2.0,
        "block": ["blocked_keyword1"]
      }
    ]
  }
}
```

## Rule Types

### 1. Required Following

Keywords that **MUST** follow a given keyword. If the required keyword is not in the model's predictions, it will be added with high probability (0.9).

**Example:**
```json
"required_following": {
  "rules": {
    "login1.login_user": ["login1.authenticate"],
    "db1.connect": ["db1.execute_query"]
  }
}
```

**Behavior:**
- After `login1.login_user`, `login1.authenticate` will always be in the top predictions
- If the model doesn't predict it, it will be added with 0.9 probability

### 2. Preferred Following

Keywords that should be **boosted** in probability when following a given keyword. The boost factor (default 1.5x) multiplies the probability.

**Example:**
```json
"preferred_following": {
  "rules": {
    "login1.authenticate": ["login1.verify_session", "login1.check_permissions"],
    "db1.execute_query": ["db1.validate_result"]
  }
}
```

**Behavior:**
- After `login1.authenticate`, `login1.verify_session` and `login1.check_permissions` will have their probabilities multiplied by 1.5
- They will move up in the ranking if they were already predicted

### 3. Blocked Following

Keywords that should **NEVER** follow a given keyword. These will be removed from predictions.

**Example:**
```json
"blocked_following": {
  "rules": {
    "login1.logout": ["login1.login_user"],
    "db1.disconnect": ["db1.execute_query"]
  }
}
```

**Behavior:**
- After `login1.logout`, `login1.login_user` will never appear in predictions
- After `db1.disconnect`, `db1.execute_query` will be filtered out

### 4. Sequence Patterns

Complex multi-keyword sequence rules that match patterns at the end of the context.

**Example:**
```json
"sequence_patterns": {
  "patterns": [
    {
      "after": ["login1.login_user", "login1.authenticate"],
      "then": "login1.verify_session",
      "comment": "After login and authenticate, always verify session"
    },
    {
      "after": ["db1.connect"],
      "boost": ["db1.execute_query", "db1.prepare_statement"],
      "boost_factor": 2.0,
      "block": ["db1.disconnect"],
      "comment": "After connecting to DB, prefer query operations"
    }
  ]
}
```

**Pattern Fields:**
- `after`: List of keywords that must appear in sequence at the end of context
- `then`: Required keyword to follow (added with high probability if not predicted)
- `boost`: List of keywords to boost in probability
- `boost_factor`: Multiplier for boosted keywords (default: 1.5)
- `block`: List of keywords to remove from predictions

## How Rules Are Applied

1. **Model Prediction**: The ML model generates initial predictions
2. **Required Following**: Required keywords are added/moved to top
3. **Preferred Following**: Preferred keywords get probability boost
4. **Blocked Following**: Blocked keywords are removed
5. **Sequence Patterns**: Complex patterns are matched and applied
6. **Re-sorting**: Final predictions are sorted by probability (descending)

## Usage

### In API

The API automatically loads rules from `keyword_rules.json` (or path specified by `KEYWORD_RULES_FILE` environment variable).

```bash
# Use default rules file
python api_keyword_predictor.py --model model.keras --tokenizer tokenizer.json

# Use custom rules file
KEYWORD_RULES_FILE=my_rules.json python api_keyword_predictor.py --model model.keras --tokenizer tokenizer.json
```

### In Python Code

```python
from keyword_rules import KeywordRules, apply_rules_to_predictions
from predict_keywords_siva import predict_next_keyword

# Load model and tokenizer
model, tokenizer = load_model_and_tokenizer("model.keras", "tokenizer.json")

# Get predictions
predictions = predict_next_keyword(model, tokenizer, ["login1.login_user"], top_k=5)

# Apply rules
rules = KeywordRules("keyword_rules.json")
filtered_predictions = rules.apply_rules(predictions, ["login1.login_user"])

# Or use convenience function
filtered_predictions = apply_rules_to_predictions(
    predictions, 
    ["login1.login_user"],
    rules_file="keyword_rules.json"
)
```

## Best Practices

1. **Start Small**: Begin with a few critical rules and expand gradually
2. **Test Thoroughly**: Test rules with various keyword sequences
3. **Use Required Sparingly**: Only use required rules for critical sequences
4. **Prefer Boost Over Required**: Use preferred/boost for suggestions, required for hard constraints
5. **Document Rules**: Add comments explaining why each rule exists
6. **Version Control**: Keep rules file in version control and document changes

## Example: Complete Rules File

```json
{
  "description": "Robot Framework keyword sequence rules",
  "version": "1.0.0",
  
  "required_following": {
    "rules": {
      "login1.login_user": ["login1.authenticate"],
      "db1.connect": ["db1.execute_query"]
    }
  },
  
  "preferred_following": {
    "rules": {
      "login1.authenticate": ["login1.verify_session"],
      "api1.send_request": ["api1.verify_response"]
    }
  },
  
  "blocked_following": {
    "rules": {
      "login1.logout": ["login1.login_user"],
      "db1.disconnect": ["db1.execute_query", "db1.prepare_statement"]
    }
  },
  
  "sequence_patterns": {
    "patterns": [
      {
        "after": ["login1.login_user", "login1.authenticate"],
        "then": "login1.verify_session",
        "comment": "After login and authenticate, always verify session"
      }
    ]
  }
}
```

## Troubleshooting

### Rules Not Applied

- Check that `keyword_rules.json` exists in the working directory
- Verify JSON syntax is valid (use a JSON validator)
- Check API logs for rule loading messages

### Unexpected Behavior

- Verify keyword names match exactly (case-sensitive)
- Check that rules are being applied in the correct order
- Test with a simple rule first to isolate issues

### Performance

- Rules are applied in-memory, so large rule sets may impact performance
- Consider using sequence patterns for complex rules instead of many individual rules

