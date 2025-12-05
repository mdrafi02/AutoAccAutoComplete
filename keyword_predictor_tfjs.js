/**
 * TensorFlow.js Keyword Predictor
 * 
 * This module provides keyword prediction functionality using TensorFlow.js
 * in the browser. It loads the converted Keras model and tokenizer.
 * 
 * Usage:
 *   const predictor = await KeywordPredictor.load('tfjs_model', 'tokenizer_js.json');
 *   const predictions = await predictor.predict(['login1.login_user', 'login1.authenticate'], 3);
 */

class KeywordPredictor {
    constructor(model, tokenizer) {
        this.model = model;
        this.tokenizer = tokenizer;
        // Get context size from model input shape (handle both [null, 2] and [2] formats)
        const inputShape = model.inputs[0].shape;
        this.contextSize = inputShape[inputShape.length - 1] || inputShape[1] || 2;
        // Get vocabulary size from model output shape
        const outputShape = model.outputs[0].shape;
        this.vocabSize = outputShape[outputShape.length - 1] || outputShape[1];
    }

    /**
     * Load model and tokenizer from files
     * @param {string} modelPath - Path to TensorFlow.js model directory (contains model.json)
     * @param {string} tokenizerPath - Path to tokenizer JSON file
     * @returns {Promise<KeywordPredictor>}
     */
    static async load(modelPath, tokenizerPath) {
        console.log('Loading TensorFlow.js model...');
        const model = await tf.loadLayersModel(`${modelPath}/model.json`);
        
        console.log('Loading tokenizer...');
        const tokenizerResponse = await fetch(tokenizerPath);
        const tokenizer = await tokenizerResponse.json();
        
        console.log('✅ Model and tokenizer loaded successfully!');
        return new KeywordPredictor(model, tokenizer);
    }

    /**
     * Normalize keyword name
     * @param {string} keyword - Keyword name
     * @returns {string} Normalized keyword
     */
    normalizeKeyword(keyword) {
        if (!keyword) return null;
        return keyword.toLowerCase().trim().replace(/\s+/g, '_');
    }

    /**
     * Convert keywords to token sequence
     * @param {string[]} keywords - Array of keyword strings
     * @returns {number[]} Token sequence
     */
    keywordsToSequence(keywords) {
        const sequence = [];
        for (const keyword of keywords) {
            const normalized = this.normalizeKeyword(keyword);
            if (normalized) {
                const token = this.tokenizer.word_index[normalized] || 0;
                sequence.push(token);
            }
        }
        return sequence;
    }

    /**
     * Pad sequence to required length
     * @param {number[]} sequence - Token sequence
     * @param {number} maxlen - Maximum length
     * @returns {number[]} Padded sequence
     */
    padSequence(sequence, maxlen) {
        const padded = [...sequence];
        while (padded.length < maxlen) {
            padded.unshift(0); // Pad with zeros at the beginning
        }
        if (padded.length > maxlen) {
            return padded.slice(-maxlen); // Take last maxlen tokens
        }
        return padded;
    }

    /**
     * Predict next keyword(s)
     * @param {string[]} contextKeywords - Array of previous keywords
     * @param {number} topK - Number of top predictions to return (default: 3)
     * @returns {Promise<Array<{keyword: string, probability: number}>>}
     */
    async predict(contextKeywords, topK = 3) {
        if (!contextKeywords || contextKeywords.length === 0) {
            throw new Error('At least one keyword must be provided');
        }

        // Prepare input sequence
        let sequence = this.keywordsToSequence(contextKeywords);
        sequence = this.padSequence(sequence, this.contextSize);

        // Convert to tensor
        const inputTensor = tf.tensor2d([sequence], [1, this.contextSize]);

        // Make prediction
        const prediction = this.model.predict(inputTensor);
        const probabilities = await prediction.data();
        
        // Clean up tensors
        inputTensor.dispose();
        prediction.dispose();

        // Get top K predictions
        const indexedProbs = Array.from(probabilities)
            .map((prob, idx) => ({ index: idx, probability: prob }))
            .sort((a, b) => b.probability - a.probability)
            .slice(0, topK);

        // Convert indices to keywords
        const results = indexedProbs.map(({ index, probability }) => {
            const keyword = this.tokenizer.index_word[String(index)] || '<OOV>';
            return {
                keyword: keyword,
                probability: probability
            };
        });

        return results;
    }

    /**
     * Predict next keywords with hierarchical depth
     * @param {string[]} contextKeywords - Array of previous keywords
     * @param {number} topK - Number of top predictions at each level
     * @param {number} depth - Number of levels deep to predict
     * @returns {Promise<Array>} Hierarchical predictions
     */
    async predictWithDepth(contextKeywords, topK = 3, depth = 1) {
        if (depth < 1) {
            return [];
        }

        // Get current level predictions
        const currentPredictions = await this.predict(contextKeywords, topK);

        if (depth === 1) {
            return currentPredictions.map(p => ({
                keyword: p.keyword,
                probability: p.probability
            }));
        }

        // Recursively get next level predictions
        const results = [];
        for (const pred of currentPredictions) {
            const result = {
                keyword: pred.keyword,
                probability: pred.probability
            };

            if (depth > 1) {
                // Build new context: append current keyword
                const newContext = [...contextKeywords];
                if (newContext.length >= this.contextSize) {
                    newContext.splice(0, newContext.length - this.contextSize + 1);
                }
                newContext.push(pred.keyword);

                // Recursively get next predictions
                const nextPredictions = await this.predictWithDepth(newContext, topK, depth - 1);
                result.next_predictions = nextPredictions;
            }

            results.push(result);
        }

        return results;
    }

    /**
     * Get model information
     * @returns {Object} Model metadata
     */
    getModelInfo() {
        return {
            contextSize: this.contextSize,
            vocabSize: this.vocabSize,
            inputShape: this.model.inputs[0].shape,
            outputShape: this.model.outputs[0].shape
        };
    }

    /**
     * Dispose of model and free memory
     */
    dispose() {
        if (this.model) {
            this.model.dispose();
        }
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeywordPredictor;
}

