# Understanding the LSTM Model Architecture

## 🔍 Why Only the Last 2 Keywords Are Used?

### Model Architecture Limitation

Your model was trained with `context_size=2`, which means:

1. **Input Shape is Fixed**: The model's input layer is hardcoded to accept exactly 2 keywords
   ```python
   Embedding(vocab_size, embedding_dim, input_length=context_size)  # context_size=2
   ```

2. **Training Process**: During training, the model learned patterns from pairs of 2 keywords:
   ```
   Training examples:
   [keyword1, keyword2] → predict keyword3
   [keyword2, keyword3] → predict keyword4
   [keyword3, keyword4] → predict keyword5
   ```

3. **Prediction Limitation**: At prediction time, the model can only accept 2 keywords as input because that's how it was trained.

## 📊 How It Actually Works

### Example Sequence:
```
Full sequence: [kw1, kw2, kw3, kw4, kw5, kw6]
```

### What the Model Sees:
```
Step 1: [kw1, kw2] → predict kw3
Step 2: [kw2, kw3] → predict kw4  (kw1 is "forgotten" at input level)
Step 3: [kw3, kw4] → predict kw5  (kw1, kw2 are "forgotten" at input level)
Step 4: [kw4, kw5] → predict kw6  (kw1, kw2, kw3 are "forgotten" at input level)
```

### Important: LSTM Internal Memory

Even though only 2 keywords are fed as input, the LSTM layer has **internal memory**:

1. **Hidden State**: The LSTM maintains a hidden state that can carry information forward
2. **Pattern Learning**: During training, the model learned that certain 2-keyword patterns lead to specific next keywords
3. **Indirect Long-term Patterns**: The model indirectly learns longer patterns because:
   - It sees many sequences during training
   - Patterns like "kw1→kw2→kw3" are learned through multiple training examples
   - The embedding layer captures semantic relationships

## 🎯 What This Means for Your Use Case

### Current Behavior:
```
Your sequence: [macreg1.create_pool, macreg1.get_id_from_response, macreg1.update_pool]
Model input:   [macreg1.get_id_from_response, macreg1.update_pool]  (last 2 only)
```

### Why Previous Keywords Seem "Lost":
- The model's **input layer** can only accept 2 keywords
- However, the model **did learn** patterns during training that include longer sequences
- The LSTM's internal state can help, but it's limited by the input shape

## 🔧 How to Use Longer Context

### Option 1: Retrain with Larger Context Size (Recommended)

If you want the model to consider more keywords directly:

```bash
python train_keyword_predictor.py \
    --input keyword_dataset_cleaned.json \
    --context-size 5 \  # Use last 5 keywords instead of 2
    --model-output keyword_predictor_v2.keras
```

**Trade-offs:**
- ✅ Model can see more context directly
- ✅ Better for longer sequences
- ❌ Requires more training data
- ❌ Larger model (more parameters)
- ❌ Longer training time

### Option 2: Current Approach (Sliding Window)

The current implementation uses a "sliding window" approach:
- Always uses the last `context_size` keywords
- As sequence grows, older keywords slide out of the window
- This is actually how the model was trained!

## 📈 Understanding the Training Process

### How Training Samples Are Created:

For a sequence: `[A, B, C, D, E]` with `context_size=2`:

```python
Training samples created:
1. Input: [A, B] → Target: C
2. Input: [B, C] → Target: D
3. Input: [C, D] → Target: E
```

The model learns:
- "A followed by B" often leads to "C"
- "B followed by C" often leads to "D"
- "C followed by D" often leads to "E"

### What the Model Actually Learns:

The model learns **transition patterns**:
- It doesn't remember the full sequence
- It learns: "Given these 2 keywords, what's likely next?"
- It learns patterns from millions of such transitions

## 💡 Key Insights

1. **Input Limitation**: The model can only accept 2 keywords at a time (because it was trained that way)

2. **Pattern Learning**: The model learned patterns from all sequences during training, so it indirectly "knows" about longer patterns

3. **Sliding Window**: Using the last 2 keywords is correct - this matches how the model was trained

4. **LSTM Memory**: The LSTM has internal memory, but it's limited by the input shape

5. **For Longer Context**: You need to retrain with a larger `context_size`

## 🎓 Summary

**Question**: "Does the model consider the previous sequence?"

**Answer**: 
- **Directly**: No - only the last 2 keywords are fed as input
- **Indirectly**: Yes - the model learned patterns from longer sequences during training
- **The model predicts based on**: The last 2 keywords + patterns learned from training data

The model is working as designed! It uses a sliding window approach that matches how it was trained.



