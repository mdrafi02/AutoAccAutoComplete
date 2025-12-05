#!/usr/bin/env python3
"""
REST API server for keyword prediction using FastAPI.
Provides endpoints for predicting next keywords based on sequence history.
"""

import json
import os
import argparse
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import prediction functions from predict_keywords_siva
from predict_keywords_siva import load_model_and_tokenizer, predict_next_keyword, predict_next_keyword_with_depth

DEFAULT_MODEL_PATH = "keyword_predictor.keras"
DEFAULT_TOKENIZER_PATH = "tokenizer.json"

# Initialize FastAPI app
app = FastAPI(
    title="Keyword Predictor API",
    description="REST API for predicting next keywords in Robot Framework sequences",
    version="1.0.0"
)

# Enable CORS for all origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer
model = None
tokenizer = None
context_size = None


# Request/Response models
class PredictRequest(BaseModel):
    """Request model for prediction endpoint."""
    keywords: List[str]
    top_k: Optional[int] = 3
    depth: Optional[int] = 1
    
    class Config:
        json_schema_extra = {
            "example": {
                "keywords": ["login1.login_user", "login1.authenticate"],
                "top_k": 3,
                "depth": 1
            }
        }


class PredictionResult(BaseModel):
    """Single prediction result."""
    keyword: str
    probability: float
    next_predictions: Optional[List['PredictionResult']] = None


class PredictResponse(BaseModel):
    """Response model for prediction endpoint."""
    predictions: List[PredictionResult]
    context_used: List[str]
    context_size: int
    full_sequence_length: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    context_size: Optional[int]
    message: str


# Update forward references for recursive model
PredictionResult.update_forward_refs()


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="ok",
        model_loaded=model is not None,
        context_size=context_size,
        message="Keyword Predictor API is running" + (" (model loaded)" if model is not None else " (model not loaded)")
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok" if model is not None else "error",
        model_loaded=model is not None,
        context_size=context_size,
        message="Model loaded and ready" if model is not None else "Model not loaded"
    )


def format_hierarchical_predictions(hierarchical_data):
    """Convert hierarchical prediction dictionaries to PredictionResult models."""
    results = []
    for pred in hierarchical_data:
        result = PredictionResult(
            keyword=pred["keyword"],
            probability=pred["probability"]
        )
        if "next_predictions" in pred and pred["next_predictions"]:
            result.next_predictions = format_hierarchical_predictions(pred["next_predictions"])
        results.append(result)
    return results


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Predict next keyword(s) based on a sequence of keywords.
    Supports depth-based hierarchical prediction.
    
    Args:
        request: PredictRequest containing keywords list, top_k, and depth
        
    Returns:
        PredictResponse with predictions and metadata
    """
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please check server logs.")
    
    if not request.keywords:
        raise HTTPException(status_code=400, detail="Keywords list cannot be empty")
    
    if request.top_k < 1 or request.top_k > 10:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 10")
    
    if request.depth < 1 or request.depth > 5:
        raise HTTPException(status_code=400, detail="depth must be between 1 and 5")
    
    try:
        # Get context (last context_size keywords)
        context_keywords = request.keywords[-context_size:] if len(request.keywords) >= context_size else request.keywords
        
        # Predict next keywords with or without depth
        if request.depth > 1:
            hierarchical_results = predict_next_keyword_with_depth(
                model, tokenizer, context_keywords, 
                top_k=request.top_k, depth=request.depth
            )
            predictions = format_hierarchical_predictions(hierarchical_results)
        else:
            results = predict_next_keyword(model, tokenizer, context_keywords, top_k=request.top_k)
            predictions = [
                PredictionResult(keyword=kw, probability=prob)
                for kw, prob in results
            ]
        
        return PredictResponse(
            predictions=predictions,
            context_used=context_keywords,
            context_size=context_size,
            full_sequence_length=len(request.keywords)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.get("/model/info")
async def model_info():
    """Get model information."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "context_size": context_size,
        "input_shape": model.input_shape,
        "vocab_size": len(tokenizer.word_index) + 1 if tokenizer else None,
        "model_loaded": True
    }


def load_model(model_path: str, tokenizer_path: str):
    """Load model and tokenizer into global variables."""
    global model, tokenizer, context_size
    
    try:
        print(f"Loading model from {model_path}...")
        model, tokenizer = load_model_and_tokenizer(model_path, tokenizer_path)
        context_size = model.input_shape[1]
        print(f"✅ Model loaded successfully!")
        print(f"   Context size: {context_size}")
        print(f"   Vocabulary size: {len(tokenizer.word_index) + 1}")
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Load model on server startup."""
    model_path = os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH)
    tokenizer_path = os.getenv("TOKENIZER_PATH", DEFAULT_TOKENIZER_PATH)
    
    if not load_model(model_path, tokenizer_path):
        print("⚠️  Warning: Model not loaded. API will return 503 errors until model is loaded.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Keyword Predictor API server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--model", "-m", type=str, default=DEFAULT_MODEL_PATH,
                       help="Path to trained model file")
    parser.add_argument("--tokenizer", "-t", type=str, default=DEFAULT_TOKENIZER_PATH,
                       help="Path to tokenizer JSON file")
    parser.add_argument("--reload", action="store_true",
                       help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    # Set environment variables for startup
    os.environ["MODEL_PATH"] = args.model
    os.environ["TOKENIZER_PATH"] = args.tokenizer
    
    print("=" * 70)
    print(" " * 20 + "🚀 Starting Keyword Predictor API")
    print("=" * 70)
    print(f"Model: {args.model}")
    print(f"Tokenizer: {args.tokenizer}")
    print(f"Server: http://{args.host}:{args.port}")
    print(f"Docs: http://{args.host}:{args.port}/docs")
    print("=" * 70)
    
    uvicorn.run(
        "api_keyword_predictor:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


