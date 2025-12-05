"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences


@pytest.fixture
def sample_keywords():
    """Sample keyword sequences for testing."""
    return [
        ["login1.login_user", "login1.authenticate", "login1.verify_session"],
        ["setup1.configure_switch", "setup1.enable_feature", "setup1.verify_config"],
        ["test1.run_test", "test1.check_result", "test1.log_output"],
    ]


@pytest.fixture
def sample_tokenizer(sample_keywords):
    """Create a tokenizer fitted on sample keywords."""
    tokenizer = Tokenizer()
    # Flatten keywords and fit
    all_keywords = []
    for seq in sample_keywords:
        all_keywords.extend(seq)
    tokenizer.fit_on_texts(all_keywords)
    return tokenizer


@pytest.fixture
def mock_model(sample_tokenizer):
    """Create a minimal mock model for testing."""
    vocab_size = len(sample_tokenizer.word_index) + 1
    context_size = 2
    
    model = Sequential([
        Embedding(vocab_size, 8, input_length=context_size),
        LSTM(16, return_sequences=False),
        Dropout(0.2),
        Dense(vocab_size, activation="softmax")
    ])
    
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer="adam",
        metrics=["accuracy"]
    )
    
    return model


@pytest.fixture
def temp_model_file(mock_model, tmp_path):
    """Save a temporary model file for testing."""
    model_path = tmp_path / "test_model.keras"
    mock_model.save(str(model_path))
    return str(model_path)


@pytest.fixture
def temp_tokenizer_file(sample_tokenizer, tmp_path):
    """Save a temporary tokenizer file for testing."""
    tokenizer_path = tmp_path / "test_tokenizer.json"
    tokenizer_json = sample_tokenizer.to_json()
    with open(tokenizer_path, 'w', encoding='utf-8') as f:
        json.dump(json.loads(tokenizer_json), f, indent=2)
    return str(tokenizer_path)


@pytest.fixture
def sample_xml_content():
    """Sample Robot Framework XML content for testing extraction."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<robot>
    <suite id="s1" name="Test Suite">
        <kw name="testsuite_setup" library="setup_lib" type="SETUP">
            <kw name="Setup Keyword 1" library="setup_lib">
                <msg>Setup message</msg>
            </kw>
        </kw>
        <test id="s1-t1" name="Test Case 1">
            <kw name="test_setup" library="test_lib" type="SETUP">
                <kw name="Test Setup Keyword" library="test_lib">
                    <msg>Test setup message</msg>
                </kw>
            </kw>
            <kw name="Main Keyword 1" library="main_lib">
                <msg>Main keyword message</msg>
            </kw>
            <kw name="Main Keyword 2" library="main_lib">
                <msg>Another main keyword</msg>
            </kw>
            <kw name="test_teardown" library="test_lib" type="TEARDOWN">
                <kw name="Test Teardown Keyword" library="test_lib">
                    <msg>Test teardown message</msg>
                </kw>
            </kw>
        </test>
        <test id="s1-t2" name="Test Case 2">
            <kw name="Another Keyword" library="other_lib">
                <msg>Another keyword message</msg>
            </kw>
        </test>
        <kw name="testsuite_teardown" library="teardown_lib" type="TEARDOWN">
            <kw name="Teardown Keyword 1" library="teardown_lib">
                <msg>Teardown message</msg>
            </kw>
        </kw>
    </suite>
</robot>
"""


@pytest.fixture
def temp_xml_file(sample_xml_content, tmp_path):
    """Create a temporary XML file for testing."""
    xml_path = tmp_path / "test_output.xml"
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(sample_xml_content)
    return str(xml_path)


@pytest.fixture
def sample_dataset_json(sample_keywords, tmp_path):
    """Create a sample dataset JSON file."""
    dataset = [
        {"test_name": f"Test {i+1}", "keywords": keywords}
        for i, keywords in enumerate(sample_keywords)
    ]
    json_path = tmp_path / "test_dataset.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2)
    return str(json_path)

