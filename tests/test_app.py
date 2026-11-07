import pytest
import sys
from pathlib import Path

# Ensure the root folder is in the path so we can import webapp
sys.path.append(str(Path(__file__).resolve().parent.parent))
from webapp.app import app

@pytest.fixture
def client():
    # Set up the Flask test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page_loads(client):
    """Test that the homepage loads successfully."""
    response = client.get('/')
    assert response.status_code == 200

def test_screening_page_loads(client):
    """Test that the screening page loads successfully."""
    response = client.get('/screening')
    assert response.status_code == 200

def test_api_valid_input(client):
    """Test the API with a valid patient."""
    payload = {
        "age": 7,
        "sex": "female",
        "temp_c": 39.2,
        "fever_now": 1,
        "chills": 1,
        "headache": 1
    }
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "risk_level" in data
    assert "score" in data
    assert "advice" in data
    assert data["risk_level"] in ["urgent", "higher", "moderate", "lower"]

def test_api_missing_age(client):
    """Test the API rejects a request with no age."""
    payload = {"sex": "male", "fever_now": 1}
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_api_invalid_age(client):
    """Test the API rejects biologically impossible ages."""
    payload = {"age": -5, "sex": "female"}
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_api_invalid_temperature(client):
    """Test the API rejects impossible temperatures."""
    payload = {"age": 30, "sex": "male", "temp_c": 99.5}
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_danger_sign_override(client):
    """Test that checking a danger sign forces an 'urgent' risk level."""
    # Even with a high age and no other symptoms, a danger sign should trigger urgent
    payload = {
        "age": 30,
        "sex": "male",
        "bleeding": 1  # Danger sign
    }
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["risk_level"] == "urgent"
    assert len(data["danger_signs"]) > 0