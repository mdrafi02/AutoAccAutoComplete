"""
Unit tests for prediction functions.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from predict_keywords_siva import (
    predict_next_keyword,
    predict_next_keyword_with_depth,
    load_model_and_tokenizer,
)


class TestPredictNextKeyword:
    """Tests for predict_next_keyword function."""

    def test_predict_with_valid_context(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test prediction with valid context keywords."""
        context = sample_keywords[0][:2]  # First 2 keywords
        results = predict_next_keyword(mock_model, sample_tokenizer, context, top_k=3)

        assert len(results) == 3
        assert all(isinstance(r, tuple) for r in results)
        assert all(len(r) == 2 for r in results)  # (keyword, probability)
        assert all(isinstance(r[0], str) for r in results)  # keyword is string
        assert all(isinstance(r[1], float) for r in results)  # probability is float
        assert all(0 <= r[1] <= 1 for r in results)  # probabilities in [0, 1]

    def test_predict_empty_context_raises_error(self, mock_model, sample_tokenizer):
        """Test that empty context raises ValueError."""
        with pytest.raises(ValueError, match="At least one keyword must be provided"):
            predict_next_keyword(mock_model, sample_tokenizer, [], top_k=3)

    def test_predict_context_longer_than_model_size(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that context longer than model input size is truncated."""
        long_context = sample_keywords[0] * 5  # Much longer than context_size=2
        results = predict_next_keyword(
            mock_model, sample_tokenizer, long_context, top_k=3
        )

        assert len(results) == 3
        # Should use last context_size keywords

    def test_predict_context_shorter_than_model_size(
        self, mock_model, sample_tokenizer
    ):
        """Test that short context is padded correctly."""
        short_context = ["login1.login_user"]  # Only 1 keyword, model expects 2
        results = predict_next_keyword(
            mock_model, sample_tokenizer, short_context, top_k=3
        )

        assert len(results) == 3
        # Should pad with empty strings

    def test_predict_top_k_parameter(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that top_k parameter controls number of results."""
        context = sample_keywords[0][:2]

        results_k1 = predict_next_keyword(
            mock_model, sample_tokenizer, context, top_k=1
        )
        results_k5 = predict_next_keyword(
            mock_model, sample_tokenizer, context, top_k=5
        )

        assert len(results_k1) == 1
        assert len(results_k5) == 5

    def test_predict_results_sorted_by_probability(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that results are sorted by probability (descending)."""
        context = sample_keywords[0][:2]
        results = predict_next_keyword(mock_model, sample_tokenizer, context, top_k=3)

        probabilities = [r[1] for r in results]
        assert probabilities == sorted(probabilities, reverse=True)


class TestPredictNextKeywordWithDepth:
    """Tests for predict_next_keyword_with_depth function."""

    def test_predict_depth_1_returns_flat_structure(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that depth=1 returns flat predictions without next_predictions."""
        context = sample_keywords[0][:2]
        results = predict_next_keyword_with_depth(
            mock_model, sample_tokenizer, context, top_k=3, depth=1
        )

        assert len(results) == 3
        assert all("keyword" in r for r in results)
        assert all("probability" in r for r in results)
        assert all(
            "next_predictions" not in r for r in results
        )  # No nested predictions

    def test_predict_depth_2_returns_hierarchical_structure(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that depth=2 returns hierarchical predictions."""
        context = sample_keywords[0][:2]
        results = predict_next_keyword_with_depth(
            mock_model, sample_tokenizer, context, top_k=2, depth=2
        )

        assert len(results) == 2
        assert all("keyword" in r for r in results)
        assert all("probability" in r for r in results)
        assert all("next_predictions" in r for r in results)
        # Each prediction should have nested predictions
        for result in results:
            assert isinstance(result["next_predictions"], list)
            assert len(result["next_predictions"]) == 2  # top_k=2

    def test_predict_depth_0_returns_empty_list(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that depth=0 returns empty list."""
        context = sample_keywords[0][:2]
        results = predict_next_keyword_with_depth(
            mock_model, sample_tokenizer, context, top_k=3, depth=0
        )

        assert results == []

    def test_predict_depth_negative_raises_error(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that negative depth raises ValueError."""
        context = sample_keywords[0][:2]
        with pytest.raises(ValueError, match="Depth must be >= 0"):
            predict_next_keyword_with_depth(
                mock_model, sample_tokenizer, context, top_k=3, depth=-1
            )

    def test_predict_depth_3_recursive_structure(
        self, mock_model, sample_tokenizer, sample_keywords
    ):
        """Test that depth=3 creates 3 levels of nested predictions."""
        context = sample_keywords[0][:2]
        results = predict_next_keyword_with_depth(
            mock_model, sample_tokenizer, context, top_k=2, depth=3
        )

        assert len(results) == 2
        # Check first level
        assert all("next_predictions" in r for r in results)
        # Check second level
        for result in results:
            for next_pred in result["next_predictions"]:
                assert "next_predictions" in next_pred
                # Check third level
                for third_pred in next_pred["next_predictions"]:
                    assert "next_predictions" not in third_pred  # Last level


class TestLoadModelAndTokenizer:
    """Tests for load_model_and_tokenizer function."""

    def test_load_model_and_tokenizer_success(
        self, temp_model_file, temp_tokenizer_file
    ):
        """Test successful loading of model and tokenizer."""
        model, tokenizer = load_model_and_tokenizer(
            temp_model_file, temp_tokenizer_file
        )

        assert model is not None
        assert tokenizer is not None
        assert hasattr(model, "predict")
        assert hasattr(tokenizer, "word_index")

    def test_load_model_file_not_found(self, temp_tokenizer_file):
        """Test that missing model file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Model file not found"):
            load_model_and_tokenizer("nonexistent_model.keras", temp_tokenizer_file)

    def test_load_tokenizer_file_not_found(self, temp_model_file):
        """Test that missing tokenizer file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Tokenizer file not found"):
            load_model_and_tokenizer(temp_model_file, "nonexistent_tokenizer.json")
