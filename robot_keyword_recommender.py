#!/usr/bin/env python3
"""
Robot Framework Keyword Recommendation System

This system analyzes keyword usage patterns from Robot Framework output.xml files
and provides intelligent recommendations for next keywords with autocomplete functionality.
"""

import json
import pickle
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set, Optional
import re
from dataclasses import dataclass
from robot_keyword_extractor import RobotKeywordExtractor


@dataclass
class KeywordRecommendation:
    """Represents a keyword recommendation with confidence score and context."""
    keyword: str
    library: str
    confidence: float
    context: str
    usage_count: int
    next_keywords: List[str]


class KeywordPatternAnalyzer:
    """Analyzes keyword usage patterns and builds recommendation models."""
    
    def __init__(self):
        self.keyword_sequences = []  # List of keyword execution sequences
        self.keyword_transitions = defaultdict(Counter)  # keyword -> next_keyword -> count
        self.keyword_contexts = defaultdict(set)  # keyword -> set of contexts
        self.library_keywords = defaultdict(set)  # library -> set of keywords
        self.keyword_frequencies = Counter()
        self.keyword_libraries = {}  # keyword -> library mapping
        
    def analyze_output_file(self, output_file: str):
        """Analyze a Robot Framework output.xml file and extract patterns."""
        extractor = RobotKeywordExtractor(output_file)
        keywords = extractor.extract_keywords()
        
        # Extract sequences and patterns
        current_sequence = []
        current_context = ""
        
        for keyword in keywords:
            keyword_name = keyword['name']
            library = keyword['library'] or 'BuiltIn'
            level = keyword['level']
            
            # Update context based on nesting level
            if level == 0:
                current_context = keyword_name
            elif level == 1:
                current_context = f"{current_context}.{keyword_name}"
            
            # Store keyword information
            self.keyword_libraries[keyword_name] = library
            self.library_keywords[library].add(keyword_name)
            self.keyword_frequencies[keyword_name] += 1
            self.keyword_contexts[keyword_name].add(current_context)
            
            # Build transition patterns
            if current_sequence:
                prev_keyword = current_sequence[-1]
                self.keyword_transitions[prev_keyword][keyword_name] += 1
            
            current_sequence.append(keyword_name)
            
            # Reset sequence on test case boundaries
            if keyword['type'] in ['SETUP', 'TEARDOWN'] and level == 0:
                if len(current_sequence) > 1:
                    self.keyword_sequences.append(current_sequence)
                current_sequence = [keyword_name]
        
        # Add final sequence
        if current_sequence:
            self.keyword_sequences.append(current_sequence)
    
    def get_recommendations(self, current_keyword: str, context: str = "", 
                          max_recommendations: int = 10) -> List[KeywordRecommendation]:
        """Get keyword recommendations based on current keyword and context."""
        recommendations = []
        
        # Get direct transitions
        if current_keyword in self.keyword_transitions:
            transitions = self.keyword_transitions[current_keyword]
            total_count = sum(transitions.values())
            
            for next_keyword, count in transitions.most_common(max_recommendations):
                confidence = count / total_count
                library = self.keyword_libraries.get(next_keyword, 'BuiltIn')
                
                # Get common next keywords for this recommendation
                next_keywords = []
                if next_keyword in self.keyword_transitions:
                    next_keywords = [kw for kw, _ in 
                                   self.keyword_transitions[next_keyword].most_common(3)]
                
                recommendation = KeywordRecommendation(
                    keyword=next_keyword,
                    library=library,
                    confidence=confidence,
                    context=context,
                    usage_count=count,
                    next_keywords=next_keywords
                )
                recommendations.append(recommendation)
        
        # If no direct transitions, suggest popular keywords from same library
        if not recommendations and current_keyword in self.keyword_libraries:
            current_library = self.keyword_libraries[current_keyword]
            library_keywords = self.library_keywords.get(current_library, set())
            
            for keyword in library_keywords:
                if keyword != current_keyword:
                    confidence = 0.1  # Lower confidence for library-based suggestions
                    recommendation = KeywordRecommendation(
                        keyword=keyword,
                        library=current_library,
                        confidence=confidence,
                        context=context,
                        usage_count=self.keyword_frequencies[keyword],
                        next_keywords=[]
                    )
                    recommendations.append(recommendation)
        
        # Sort by confidence and usage count
        recommendations.sort(key=lambda x: (x.confidence, x.usage_count), reverse=True)
        return recommendations[:max_recommendations]
    
    def get_autocomplete_suggestions(self, partial_keyword: str, 
                                   library_filter: str = None) -> List[Dict]:
        """Get autocomplete suggestions for partial keyword input."""
        suggestions = []
        partial_lower = partial_keyword.lower()
        
        for keyword, library in self.keyword_libraries.items():
            if library_filter and library != library_filter:
                continue
                
            if partial_lower in keyword.lower():
                suggestions.append({
                    'keyword': keyword,
                    'library': library,
                    'frequency': self.keyword_frequencies[keyword],
                    'contexts': list(self.keyword_contexts[keyword])
                })
        
        # Sort by frequency and relevance
        suggestions.sort(key=lambda x: (x['frequency'], len(x['keyword'])), reverse=True)
        return suggestions[:20]  # Return top 20 suggestions
    
    def get_context_recommendations(self, context_keywords: List[str], 
                                  max_recommendations: int = 10) -> List[KeywordRecommendation]:
        """Get recommendations based on multiple context keywords."""
        if not context_keywords:
            return []
        
        # Find sequences that contain all context keywords
        matching_sequences = []
        for sequence in self.keyword_sequences:
            if all(kw in sequence for kw in context_keywords):
                matching_sequences.append(sequence)
        
        if not matching_sequences:
            return []
        
        # Find common next keywords after the context
        next_keyword_counts = Counter()
        for sequence in matching_sequences:
            # Find the position after the last context keyword
            last_context_pos = max(sequence.index(kw) for kw in context_keywords)
            if last_context_pos + 1 < len(sequence):
                next_keyword = sequence[last_context_pos + 1]
                next_keyword_counts[next_keyword] += 1
        
        recommendations = []
        total_count = sum(next_keyword_counts.values())
        
        for keyword, count in next_keyword_counts.most_common(max_recommendations):
            confidence = count / total_count
            library = self.keyword_libraries.get(keyword, 'BuiltIn')
            
            recommendation = KeywordRecommendation(
                keyword=keyword,
                library=library,
                confidence=confidence,
                context=" -> ".join(context_keywords),
                usage_count=count,
                next_keywords=[]
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def save_model(self, filepath: str):
        """Save the trained model to a file."""
        model_data = {
            'keyword_transitions': dict(self.keyword_transitions),
            'keyword_contexts': {k: list(v) for k, v in self.keyword_contexts.items()},
            'library_keywords': {k: list(v) for k, v in self.library_keywords.items()},
            'keyword_frequencies': dict(self.keyword_frequencies),
            'keyword_libraries': self.keyword_libraries,
            'keyword_sequences': self.keyword_sequences
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load a trained model from a file."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.keyword_transitions = defaultdict(Counter, model_data['keyword_transitions'])
        self.keyword_contexts = defaultdict(set, 
            {k: set(v) for k, v in model_data['keyword_contexts'].items()})
        self.library_keywords = defaultdict(set, 
            {k: set(v) for k, v in model_data['library_keywords'].items()})
        self.keyword_frequencies = Counter(model_data['keyword_frequencies'])
        self.keyword_libraries = model_data['keyword_libraries']
        self.keyword_sequences = model_data['keyword_sequences']


class RobotKeywordRecommender:
    """Main recommendation system with autocomplete functionality."""
    
    def __init__(self, model_file: str = None):
        self.analyzer = KeywordPatternAnalyzer()
        if model_file:
            self.analyzer.load_model(model_file)
    
    def train_on_output_files(self, output_files: List[str], save_model: str = None):
        """Train the recommendation system on multiple output files."""
        print(f"Training on {len(output_files)} output files...")
        
        for i, output_file in enumerate(output_files, 1):
            print(f"Processing file {i}/{len(output_files)}: {output_file}")
            try:
                self.analyzer.analyze_output_file(output_file)
            except Exception as e:
                print(f"Error processing {output_file}: {e}")
        
        print(f"Training complete. Analyzed {len(self.analyzer.keyword_sequences)} sequences.")
        
        if save_model:
            self.analyzer.save_model(save_model)
            print(f"Model saved to {save_model}")
    
    def get_recommendations(self, current_keyword: str, context: str = "", 
                          max_recommendations: int = 10) -> List[Dict]:
        """Get keyword recommendations in a user-friendly format."""
        recommendations = self.analyzer.get_recommendations(
            current_keyword, context, max_recommendations
        )
        
        return [
            {
                'keyword': rec.keyword,
                'library': rec.library,
                'confidence': round(rec.confidence, 3),
                'context': rec.context,
                'usage_count': rec.usage_count,
                'next_keywords': rec.next_keywords
            }
            for rec in recommendations
        ]
    
    def get_autocomplete(self, partial_keyword: str, library_filter: str = None) -> List[Dict]:
        """Get autocomplete suggestions."""
        return self.analyzer.get_autocomplete_suggestions(partial_keyword, library_filter)
    
    def get_context_recommendations(self, context_keywords: List[str], 
                                  max_recommendations: int = 10) -> List[Dict]:
        """Get recommendations based on context keywords."""
        recommendations = self.analyzer.get_context_recommendations(
            context_keywords, max_recommendations
        )
        
        return [
            {
                'keyword': rec.keyword,
                'library': rec.library,
                'confidence': round(rec.confidence, 3),
                'context': rec.context,
                'usage_count': rec.usage_count,
                'next_keywords': rec.next_keywords
            }
            for rec in recommendations
        ]
    
    def get_popular_keywords(self, library: str = None, limit: int = 20) -> List[Dict]:
        """Get most popular keywords, optionally filtered by library."""
        keywords = self.analyzer.keyword_frequencies.most_common(limit * 2)
        
        result = []
        for keyword, count in keywords:
            keyword_library = self.analyzer.keyword_libraries.get(keyword, 'BuiltIn')
            if library is None or keyword_library == library:
                result.append({
                    'keyword': keyword,
                    'library': keyword_library,
                    'frequency': count
                })
                if len(result) >= limit:
                    break
        
        return result
    
    def get_library_statistics(self) -> Dict:
        """Get statistics about keyword libraries."""
        stats = {}
        for library, keywords in self.analyzer.library_keywords.items():
            total_usage = sum(self.analyzer.keyword_frequencies[kw] for kw in keywords)
            stats[library] = {
                'keyword_count': len(keywords),
                'total_usage': total_usage,
                'top_keywords': [
                    {'keyword': kw, 'count': self.analyzer.keyword_frequencies[kw]}
                    for kw, _ in Counter({kw: self.analyzer.keyword_frequencies[kw] 
                                        for kw in keywords}).most_common(5)
                ]
            }
        return stats


def main():
    """Example usage of the recommendation system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robot Framework Keyword Recommendation System")
    parser.add_argument('--train', nargs='+', help='Train on output.xml files')
    parser.add_argument('--model', help='Path to saved model file')
    parser.add_argument('--save-model', help='Save trained model to file')
    parser.add_argument('--recommend', help='Get recommendations for a keyword')
    parser.add_argument('--autocomplete', help='Get autocomplete suggestions for partial keyword')
    parser.add_argument('--context', nargs='+', help='Get context-based recommendations')
    parser.add_argument('--popular', help='Get popular keywords from library')
    parser.add_argument('--stats', action='store_true', help='Show library statistics')
    
    args = parser.parse_args()
    
    recommender = RobotKeywordRecommender(args.model)
    
    if args.train:
        recommender.train_on_output_files(args.train, args.save_model)
    
    if args.recommend:
        recommendations = recommender.get_recommendations(args.recommend)
        print(f"\nRecommendations for '{args.recommend}':")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i:2d}. {rec['keyword']} ({rec['library']}) - "
                  f"Confidence: {rec['confidence']:.3f}, Usage: {rec['usage_count']}")
    
    if args.autocomplete:
        suggestions = recommender.get_autocomplete(args.autocomplete)
        print(f"\nAutocomplete suggestions for '{args.autocomplete}':")
        for i, sug in enumerate(suggestions, 1):
            print(f"{i:2d}. {sug['keyword']} ({sug['library']}) - "
                  f"Frequency: {sug['frequency']}")
    
    if args.context:
        recommendations = recommender.get_context_recommendations(args.context)
        print(f"\nContext-based recommendations for: {' -> '.join(args.context)}")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i:2d}. {rec['keyword']} ({rec['library']}) - "
                  f"Confidence: {rec['confidence']:.3f}")
    
    if args.popular:
        popular = recommender.get_popular_keywords(args.popular)
        print(f"\nPopular keywords in {args.popular}:")
        for i, kw in enumerate(popular, 1):
            print(f"{i:2d}. {kw['keyword']} - Frequency: {kw['frequency']}")
    
    if args.stats:
        stats = recommender.get_library_statistics()
        print("\nLibrary Statistics:")
        for library, data in stats.items():
            print(f"\n{library}:")
            print(f"  Keywords: {data['keyword_count']}")
            print(f"  Total Usage: {data['total_usage']}")
            print(f"  Top Keywords: {', '.join([kw['keyword'] for kw in data['top_keywords']])}")


if __name__ == "__main__":
    main()

