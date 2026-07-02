#!/usr/bin/env python3
"""
CLI tool to load and use the trained keyword recommendation model.

Usage:
    python3 use_model.py --model data/models/robot_keyword_model.pkl --next-keywords "Log To Console" "Sleep"
    python3 use_model.py --model data/models/robot_keyword_model.pkl --autocomplete "Log"
    python3 use_model.py --model data/models/robot_keyword_model.pkl --stats
"""

import sys
import os
import argparse
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_models.robot_keyword_recommender import RobotKeywordRecommender


def print_suggestions(suggestions, title="Suggestions"):
    """Print suggestions in a formatted way."""
    if not suggestions:
        print(f"\n{title}: No suggestions available")
        return
    
    print(f"\n{title}:")
    print("=" * 80)
    
    for i, sug in enumerate(suggestions, 1):
        if 'keyword' in sug and 'library' in sug:
            # Format: library.keyword
            keyword_str = f"{sug['library']}.{sug['keyword']}"
            print(f"{i:2d}. {keyword_str}")
            
            if 'confidence' in sug:
                print(f"    Confidence: {sug['confidence']*100:.1f}%" if sug['confidence'] < 1 
                      else f"    Confidence: {sug['confidence']:.1f}%")
            if 'usage_count' in sug:
                print(f"    Used: {sug['usage_count']} times")
            elif 'frequency' in sug:
                print(f"    Frequency: {sug['frequency']} times")
            if 'next_keywords' in sug and sug['next_keywords']:
                print(f"    Often followed by: {', '.join(sug['next_keywords'][:3])}")
        else:
            # Fallback for other formats
            print(f"{i:2d}. {sug}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Load and use trained Robot Framework keyword recommendation model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get next keyword suggestions
  python3 use_model.py --model data/models/robot_keyword_model.pkl \\
    --next-keywords "Log To Console" "Sleep"

  # Get autocomplete suggestions
  python3 use_model.py --model data/models/robot_keyword_model.pkl \\
    --autocomplete "Log"

  # Show model statistics
  python3 use_model.py --model data/models/robot_keyword_model.pkl --stats

  # Get popular keywords
  python3 use_model.py --model data/models/robot_keyword_model.pkl \\
    --popular --limit 10

  # Get recommendations for a keyword
  python3 use_model.py --model data/models/robot_keyword_model.pkl \\
    --recommend "Log To Console" --max 5
        """
    )
    
    parser.add_argument(
        '--model', '-m',
        default='data/models/robot_keyword_model.pkl',
        help='Path to trained model file (default: data/models/robot_keyword_model.pkl)'
    )
    
    parser.add_argument(
        '--next-keywords', '-n',
        nargs='+',
        metavar='KEYWORD',
        help='Get next keyword suggestions based on previous keywords'
    )
    
    parser.add_argument(
        '--max',
        type=int,
        default=3,
        help='Maximum number of suggestions (default: 3)'
    )
    
    parser.add_argument(
        '--autocomplete', '-a',
        metavar='PARTIAL',
        help='Get autocomplete suggestions for partial keyword'
    )
    
    parser.add_argument(
        '--library', '-l',
        help='Filter by library name (for autocomplete)'
    )
    
    parser.add_argument(
        '--recommend', '-r',
        metavar='KEYWORD',
        help='Get recommendations for a specific keyword'
    )
    
    parser.add_argument(
        '--popular', '-p',
        action='store_true',
        help='Show popular keywords'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Limit for popular keywords (default: 20)'
    )
    
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show model statistics'
    )
    
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output as JSON'
    )
    
    args = parser.parse_args()
    
    # Load model
    if not os.path.exists(args.model):
        print(f"ERROR: Model file not found: {args.model}")
        print(f"\nTrain a model first:")
        print(f"  python3 train_with_new_data.py")
        sys.exit(1)
    
    print(f"Loading model from: {args.model}")
    try:
        recommender = RobotKeywordRecommender(args.model)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"ERROR: Failed to load model: {e}")
        sys.exit(1)
    
    # Show statistics
    if args.stats:
        stats = recommender.get_library_statistics()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("\n" + "=" * 80)
            print("Model Statistics")
            print("=" * 80)
            print(f"\nTotal Libraries: {len(stats)}")
            
            total_keywords = sum(data['keyword_count'] for data in stats.values())
            print(f"Total Keywords: {total_keywords}")
            
            print("\nTop Libraries:")
            sorted_libs = sorted(stats.items(), 
                               key=lambda x: x[1]['keyword_count'], 
                               reverse=True)[:10]
            for lib, data in sorted_libs:
                print(f"  {lib:30s} - {data['keyword_count']:4d} keywords, "
                      f"{data['total_usage']:6d} total usage")
            
            print("\nTop Keywords by Library:")
            for lib, data in sorted_libs[:5]:
                print(f"\n  {lib}:")
                for kw_data in data['top_keywords'][:5]:
                    print(f"    - {kw_data['keyword']} ({kw_data['count']} uses)")
    
    # Get next keyword suggestions
    if args.next_keywords:
        recommendations = recommender.get_context_recommendations(
            args.next_keywords, 
            args.max
        )
        
        if args.json:
            # Format as library.keyword for JSON output
            formatted = []
            for rec in recommendations:
                formatted.append({
                    'keyword': f"{rec['library']}.{rec['keyword']}",
                    'library': rec['library'],
                    'keyword_name': rec['keyword'],
                    'confidence': rec['confidence'],
                    'usage_count': rec['usage_count']
                })
            print(json.dumps({'suggestions': formatted}, indent=2))
        else:
            # Format as library.keyword
            formatted = []
            for rec in recommendations:
                formatted.append({
                    'keyword': rec['keyword'],
                    'library': rec['library'],
                    'confidence': rec['confidence'],
                    'usage_count': rec['usage_count'],
                    'next_keywords': rec.get('next_keywords', [])
                })
            
            context_str = " -> ".join(args.next_keywords)
            print_suggestions(formatted, f"Next keyword suggestions after: {context_str}")
    
    # Autocomplete
    if args.autocomplete:
        suggestions = recommender.get_autocomplete(args.autocomplete, args.library)
        
        if args.json:
            formatted = []
            for sug in suggestions[:args.max]:
                formatted.append({
                    'keyword': f"{sug['library']}.{sug['keyword']}",
                    'library': sug['library'],
                    'keyword_name': sug['keyword'],
                    'frequency': sug['frequency']
                })
            print(json.dumps({'suggestions': formatted}, indent=2))
        else:
            formatted = []
            for sug in suggestions[:args.max]:
                formatted.append({
                    'keyword': sug['keyword'],
                    'library': sug['library'],
                    'frequency': sug['frequency']
                })
            print_suggestions(formatted, f"Autocomplete for '{args.autocomplete}'")
    
    # Get recommendations for a keyword
    if args.recommend:
        recommendations = recommender.get_recommendations(args.recommend, "", args.max)
        
        if args.json:
            formatted = []
            for rec in recommendations:
                formatted.append({
                    'keyword': f"{rec['library']}.{rec['keyword']}",
                    'library': rec['library'],
                    'keyword_name': rec['keyword'],
                    'confidence': rec['confidence'],
                    'usage_count': rec['usage_count']
                })
            print(json.dumps({'recommendations': formatted}, indent=2))
        else:
            formatted = []
            for rec in recommendations:
                formatted.append({
                    'keyword': rec['keyword'],
                    'library': rec['library'],
                    'confidence': rec['confidence'],
                    'usage_count': rec['usage_count'],
                    'next_keywords': rec.get('next_keywords', [])
                })
            print_suggestions(formatted, f"Recommendations for '{args.recommend}'")
    
    # Popular keywords
    if args.popular:
        popular = recommender.get_popular_keywords(None, args.limit)
        
        if args.json:
            formatted = []
            for kw in popular:
                formatted.append({
                    'keyword': f"{kw['library']}.{kw['keyword']}",
                    'library': kw['library'],
                    'keyword_name': kw['keyword'],
                    'frequency': kw['frequency']
                })
            print(json.dumps({'keywords': formatted}, indent=2))
        else:
            formatted = []
            for kw in popular:
                formatted.append({
                    'keyword': kw['keyword'],
                    'library': kw['library'],
                    'frequency': kw['frequency']
                })
            print_suggestions(formatted, f"Most Popular Keywords (Top {args.limit})")


if __name__ == "__main__":
    main()

