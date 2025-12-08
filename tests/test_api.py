"""
Unit tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api_keyword_predictor import app
import json
import os


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def client_with_model(
    mock_model, sample_tokenizer, temp_model_file, temp_tokenizer_file
):
    """Create a test client with loaded model."""
    # Import here to avoid circular imports
    import api_keyword_predictor

    # Save original state (if any)
    original_model = getattr(api_keyword_predictor, "model", None)
    original_tokenizer = getattr(api_keyword_predictor, "tokenizer", None)
    original_context_size = getattr(api_keyword_predictor, "context_size", None)

    # Load the model into the API's global variables using the API's load_model function
    api_keyword_predictor.load_model(temp_model_file, temp_tokenizer_file)

    yield TestClient(app)

    # Cleanup: Reset global state after test
    api_keyword_predictor.model = original_model
    api_keyword_predictor.tokenizer = original_tokenizer
    api_keyword_predictor.context_size = original_context_size


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns health status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data

    def test_model_info_endpoint(self, client):
        """Test /model/info endpoint."""
        response = client.get("/model/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data


class TestPredictEndpoint:
    """Tests for /predict endpoint."""

    def test_predict_without_model_returns_error(self, client):
        """Test that prediction without loaded model returns error."""
        response = client.post(
            "/predict",
            json={
                "keywords": ["login1.login_user", "login1.authenticate"],
                "top_k": 3,
                "depth": 1,
            },
        )
        # Should return 500 or 503 if model not loaded
        assert response.status_code in [500, 503]

    def test_predict_with_model_returns_results(self, client_with_model):
        """Test prediction with loaded model."""
        response = client_with_model.post(
            "/predict",
            json={
                "keywords": ["login1.login_user", "login1.authenticate"],
                "top_k": 3,
                "depth": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "context_used" in data
        assert "context_size" in data
        assert len(data["predictions"]) == 3

    def test_predict_with_depth_2(self, client_with_model):
        """Test prediction with depth=2 returns hierarchical results."""
        response = client_with_model.post(
            "/predict",
            json={
                "keywords": ["login1.login_user", "login1.authenticate"],
                "top_k": 2,
                "depth": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        # Check hierarchical structure
        for pred in data["predictions"]:
            assert "keyword" in pred
            assert "probability" in pred
            assert "next_predictions" in pred
            assert isinstance(pred["next_predictions"], list)

    def test_predict_empty_keywords_returns_error(self, client_with_model):
        """Test that empty keywords list returns error."""
        response = client_with_model.post("/predict", json={"keywords": [], "top_k": 3})
        assert response.status_code in [400, 422]

    def test_predict_invalid_depth_returns_error(self, client_with_model):
        """Test that invalid depth returns error."""
        response = client_with_model.post(
            "/predict",
            json={
                "keywords": ["login1.login_user"],
                "top_k": 3,
                "depth": 10,  # Too high
            },
        )
        assert response.status_code in [400, 422]

    def test_predict_negative_depth_returns_error(self, client_with_model):
        """Test that negative depth returns error."""
        response = client_with_model.post(
            "/predict",
            json={"keywords": ["login1.login_user"], "top_k": 3, "depth": -1},
        )
        assert response.status_code in [400, 422]

    def test_predict_missing_keywords_returns_error(self, client_with_model):
        """Test that missing keywords field returns error."""
        response = client_with_model.post("/predict", json={"top_k": 3})
        assert response.status_code == 422  # Validation error

    def test_predict_default_top_k(self, client_with_model):
        """Test that default top_k is used when not specified."""
        response = client_with_model.post(
            "/predict", json={"keywords": ["login1.login_user", "login1.authenticate"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 3  # Default top_k=3

    def test_predict_custom_top_k(self, client_with_model):
        """Test that custom top_k is respected."""
        response = client_with_model.post(
            "/predict",
            json={"keywords": ["login1.login_user", "login1.authenticate"], "top_k": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 5


class TestPredictResponseFormat:
    """Tests for response format validation."""

    def test_predict_response_structure(self, client_with_model):
        """Test that response has correct structure."""
        response = client_with_model.post(
            "/predict",
            json={
                "keywords": ["login1.login_user", "login1.authenticate"],
                "top_k": 2,
                "depth": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Validate structure
        assert "predictions" in data
        assert "context_used" in data
        assert "context_size" in data
        assert "full_sequence_length" in data

        # Validate predictions structure
        for pred in data["predictions"]:
            assert "keyword" in pred
            assert "probability" in pred
            assert isinstance(pred["keyword"], str)
            assert isinstance(pred["probability"], float)
            assert 0 <= pred["probability"] <= 1

        # Validate context
        assert isinstance(data["context_used"], list)
        assert isinstance(data["context_size"], int)
        assert isinstance(data["full_sequence_length"], int)
