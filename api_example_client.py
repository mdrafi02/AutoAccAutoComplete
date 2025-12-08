#!/usr/bin/env python3
"""
Example client for the Keyword Predictor API.
Demonstrates how to use the API endpoints.
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:8000"


def check_health():
    """Check if API is running and model is loaded."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print("✅ API Health Check:")
        print(f"   Status: {data['status']}")
        print(f"   Model Loaded: {data['model_loaded']}")
        print(f"   Context Size: {data['context_size']}")
        print(f"   Message: {data['message']}")
        return data["model_loaded"]
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API. Is the server running?")
        print(f"   Try: python api_keyword_predictor.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def predict_next_keywords(keywords: list, top_k: int = 3):
    """
    Predict next keywords based on a sequence.

    Args:
        keywords: List of keywords (sequence)
        top_k: Number of predictions to return

    Returns:
        Response data or None if error
    """
    try:
        payload = {"keywords": keywords, "top_k": top_k}

        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def get_model_info():
    """Get model information."""
    try:
        response = requests.get(f"{API_BASE_URL}/model/info")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Example usage of the API."""
    print("=" * 70)
    print(" " * 20 + "📡 Keyword Predictor API Client")
    print("=" * 70)

    # Check health
    print("\n1. Checking API health...")
    if not check_health():
        sys.exit(1)

    # Get model info
    print("\n2. Getting model information...")
    model_info = get_model_info()
    if model_info:
        print(f"   Context Size: {model_info['context_size']}")
        print(f"   Input Shape: {model_info['input_shape']}")
        print(f"   Vocabulary Size: {model_info['vocab_size']}")

    # Example 1: Start with 2 keywords
    print("\n3. Example: Predicting from initial keywords...")
    keywords = ["login1.login_user", "login1.authenticate"]
    print(f"   Input sequence: {keywords}")

    result = predict_next_keywords(keywords, top_k=3)
    if result:
        print(f"\n   ✅ Predictions (using context: {result['context_used']}):")
        for i, pred in enumerate(result["predictions"], 1):
            print(f"      {i}. {pred['keyword']:50s} ({pred['probability']*100:.2f}%)")

    # Example 2: Continue with longer sequence
    print("\n4. Example: Continuing with longer sequence...")
    keywords = ["login1.login_user", "login1.authenticate", "login1.logout"]
    print(f"   Input sequence: {keywords}")

    result = predict_next_keywords(keywords, top_k=3)
    if result:
        print(f"\n   ✅ Predictions (using context: {result['context_used']}):")
        print(
            f"   Note: Model uses last {result['context_size']} keywords from sequence"
        )
        for i, pred in enumerate(result["predictions"], 1):
            print(f"      {i}. {pred['keyword']:50s} ({pred['probability']*100:.2f}%)")

    print("\n" + "=" * 70)
    print("✅ API client example completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
