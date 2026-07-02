/**
 * Robot Framework Keyword Suggestions - JavaScript Integration
 * 
 * This module provides keyword suggestions for Robot Framework test case editors.
 * Returns top 3 suggestions in "library.keyword" format based on previous keywords.
 * 
 * Usage:
 *   const suggester = new KeywordSuggester('http://localhost:5000/api');
 *   const suggestions = await suggester.getNextKeywords(['Log To Console', 'Sleep']);
 *   // Returns: [{keyword: "BuiltIn.Wait Until Keyword Succeeds", library: "BuiltIn", ...}, ...]
 */

class KeywordSuggester {
    /**
     * Initialize the keyword suggester
     * @param {string} apiUrl - Base URL of the recommendation API (default: 'http://localhost:5000/api')
     */
    constructor(apiUrl = 'http://localhost:5000/api') {
        this.apiUrl = apiUrl.replace(/\/$/, ''); // Remove trailing slash
    }

    /**
     * Get next keyword suggestions based on previous keywords
     * @param {string[]} previousKeywords - Array of previous keywords in the test case
     * @param {number} maxSuggestions - Maximum number of suggestions (default: 3)
     * @returns {Promise<Array>} Array of suggestions in format:
     *   [
     *     {
     *       keyword: "BuiltIn.Log To Console",  // library.keyword format
     *       library: "BuiltIn",
     *       keyword_name: "Log To Console",
     *       confidence: 45.2,  // percentage
     *       usage_count: 242
     *     },
     *     ...
     *   ]
     */
    async getNextKeywords(previousKeywords = [], maxSuggestions = 3) {
        if (!Array.isArray(previousKeywords)) {
            throw new Error('previousKeywords must be an array');
        }

        try {
            const response = await fetch(`${this.apiUrl}/next-keywords`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keywords: previousKeywords,
                    max: maxSuggestions
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.suggestions || [];
        } catch (error) {
            console.error('Error fetching keyword suggestions:', error);
            return []; // Return empty array on error
        }
    }

    /**
     * Get suggestions for a single previous keyword
     * @param {string} previousKeyword - The previous keyword
     * @param {number} maxSuggestions - Maximum number of suggestions (default: 3)
     * @returns {Promise<Array>} Array of suggestions
     */
    async getNextKeywordAfter(previousKeyword, maxSuggestions = 3) {
        return this.getNextKeywords([previousKeyword], maxSuggestions);
    }

    /**
     * Get autocomplete suggestions for partial keyword input
     * @param {string} partialKeyword - Partially typed keyword
     * @param {string|null} libraryFilter - Optional library filter
     * @returns {Promise<Array>} Array of autocomplete suggestions
     */
    async getAutocomplete(partialKeyword, libraryFilter = null) {
        try {
            const response = await fetch(`${this.apiUrl}/autocomplete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keyword: partialKeyword,
                    library: libraryFilter
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.suggestions || [];
        } catch (error) {
            console.error('Error fetching autocomplete:', error);
            return [];
        }
    }
}

// Export for use in modules (Node.js/ES6)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeywordSuggester;
}

// Also available globally if loaded via script tag
if (typeof window !== 'undefined') {
    window.KeywordSuggester = KeywordSuggester;
}


