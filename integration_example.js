/**
 * Integration Example for Robot Framework Keyword Recommender
 * 
 * This file shows how to integrate the recommendation system
 * into your browser-based test creation tool.
 */

// Configuration
const RECOMMENDER_API_URL = 'http://localhost:5000/api';

/**
 * Autocomplete Integration Example
 * Use this when user types in a keyword input field
 */
async function setupAutocomplete(inputElement, onSelectCallback) {
    let debounceTimeout;
    
    inputElement.addEventListener('input', async function() {
        const value = this.value.trim();
        
        clearTimeout(debounceTimeout);
        
        if (value.length < 2) {
            hideAutocomplete();
            return;
        }
        
        debounceTimeout = setTimeout(async () => {
            try {
                const suggestions = await getAutocompleteSuggestions(value);
                showAutocomplete(suggestions, inputElement, onSelectCallback);
            } catch (error) {
                console.error('Autocomplete error:', error);
            }
        }, 300); // 300ms debounce
    });
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (!inputElement.contains(e.target)) {
            hideAutocomplete();
        }
    });
}

/**
 * Get autocomplete suggestions from API
 */
async function getAutocompleteSuggestions(partialKeyword, library = null) {
    const response = await fetch(`${RECOMMENDER_API_URL}/autocomplete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            keyword: partialKeyword,
            library: library
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.suggestions;
}

/**
 * Display autocomplete dropdown
 */
function showAutocomplete(suggestions, inputElement, onSelectCallback) {
    // Remove existing dropdown if any
    hideAutocomplete();
    
    if (suggestions.length === 0) {
        return;
    }
    
    // Create dropdown element
    const dropdown = document.createElement('div');
    dropdown.className = 'rf-autocomplete-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        max-height: 300px;
        overflow-y: auto;
        z-index: 1000;
    `;
    
    // Add suggestions
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'rf-autocomplete-item';
        item.style.cssText = `
            padding: 10px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        `;
        item.innerHTML = `
            <strong>${highlightMatch(suggestion.keyword, inputElement.value)}</strong>
            <span style="color: #666; font-size: 0.9em; margin-left: 10px;">
                ${suggestion.library} (${suggestion.frequency} uses)
            </span>
        `;
        
        item.addEventListener('click', () => {
            inputElement.value = suggestion.keyword;
            hideAutocomplete();
            if (onSelectCallback) {
                onSelectCallback(suggestion);
            }
            // Trigger recommendations if needed
            getRecommendations(suggestion.keyword);
        });
        
        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f0f0f0';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
        });
        
        dropdown.appendChild(item);
    });
    
    // Position and show dropdown
    inputElement.parentElement.style.position = 'relative';
    inputElement.parentElement.appendChild(dropdown);
}

/**
 * Hide autocomplete dropdown
 */
function hideAutocomplete() {
    const dropdown = document.querySelector('.rf-autocomplete-dropdown');
    if (dropdown) {
        dropdown.remove();
    }
}

/**
 * Highlight matching text in suggestions
 */
function highlightMatch(text, query) {
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

/**
 * Get keyword recommendations
 */
async function getRecommendations(currentKeyword, context = '', maxResults = 10) {
    try {
        const response = await fetch(`${RECOMMENDER_API_URL}/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: currentKeyword,
                context: context,
                max_recommendations: maxResults
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.recommendations;
    } catch (error) {
        console.error('Error fetching recommendations:', error);
        return [];
    }
}

/**
 * Get context-based recommendations
 */
async function getContextRecommendations(contextKeywords, maxResults = 10) {
    try {
        const response = await fetch(`${RECOMMENDER_API_URL}/context`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keywords: contextKeywords,
                max_recommendations: maxResults
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.recommendations;
    } catch (error) {
        console.error('Error fetching context recommendations:', error);
        return [];
    }
}

/**
 * Display recommendations in your UI
 */
function displayRecommendations(recommendations, containerElement) {
    if (recommendations.length === 0) {
        containerElement.innerHTML = '<p>No recommendations available</p>';
        return;
    }
    
    containerElement.innerHTML = recommendations.map(rec => `
        <div class="recommendation-item" style="
            padding: 12px;
            margin-bottom: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
        " onclick="selectRecommendedKeyword('${rec.keyword}')">
            <div style="display: flex; justify-content: space-between;">
                <strong>${rec.keyword}</strong>
                <span style="
                    background: #667eea;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.85em;
                ">${(rec.confidence * 100).toFixed(0)}%</span>
            </div>
            <div style="color: #666; font-size: 0.9em; margin-top: 4px;">
                ${rec.library} • Used ${rec.usage_count} times
            </div>
        </div>
    `).join('');
}

/**
 * Example: Setup for a Robot Framework test case editor
 */
function setupRobotFrameworkEditor() {
    // Find your keyword input field (adjust selector as needed)
    const keywordInput = document.querySelector('#keyword-input');
    
    if (!keywordInput) {
        console.warn('Keyword input field not found');
        return;
    }
    
    // Setup autocomplete
    setupAutocomplete(keywordInput, (suggestion) => {
        console.log('Selected keyword:', suggestion);
        // Add keyword to test case
        addKeywordToTestCase(suggestion.keyword);
        
        // Get and show recommendations for next keyword
        getRecommendations(suggestion.keyword).then(recommendations => {
            const recommendationsContainer = document.querySelector('#recommendations-container');
            if (recommendationsContainer) {
                displayRecommendations(recommendations, recommendationsContainer);
            }
        });
    });
    
    // Get recommendations when keyword is entered
    keywordInput.addEventListener('blur', async function() {
        const keyword = this.value.trim();
        if (keyword) {
            // Get previous keywords as context
            const previousKeywords = getPreviousKeywords();
            
            const recommendations = await getContextRecommendations(previousKeywords);
            const recommendationsContainer = document.querySelector('#recommendations-container');
            if (recommendationsContainer) {
                displayRecommendations(recommendations, recommendationsContainer);
            }
        }
    });
}

/**
 * Helper function to get previous keywords from your test case structure
 * Adjust this based on your actual test case data structure
 */
function getPreviousKeywords() {
    // Example: Get keywords from a list/array in your test case
    // Adjust this based on your actual implementation
    const testCase = getCurrentTestCase(); // Your function to get current test case
    return testCase.keywords ? testCase.keywords.map(kw => kw.name) : [];
}

/**
 * Select a recommended keyword and add it to test case
 */
function selectRecommendedKeyword(keyword) {
    // Your function to add keyword to test case
    addKeywordToTestCase(keyword);
    
    // Clear and refresh recommendations
    getRecommendations(keyword).then(recommendations => {
        const recommendationsContainer = document.querySelector('#recommendations-container');
        if (recommendationsContainer) {
            displayRecommendations(recommendations, recommendationsContainer);
        }
    });
}

/**
 * Add keyword to test case (implement based on your structure)
 */
function addKeywordToTestCase(keyword) {
    // Implement this based on your test case structure
    console.log('Adding keyword to test case:', keyword);
}

/**
 * Initialize when DOM is ready
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupRobotFrameworkEditor);
} else {
    setupRobotFrameworkEditor();
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getAutocompleteSuggestions,
        getRecommendations,
        getContextRecommendations,
        setupAutocomplete,
        displayRecommendations
    };
}
