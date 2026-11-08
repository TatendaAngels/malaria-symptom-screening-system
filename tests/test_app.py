import pytest
import sys
from pathlib import Path
from types import SimpleNamespace

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

def test_contact_page_has_required_form_fields(client):
    response = client.get('/contact')

    assert response.status_code == 200
    assert b'name="name"' in response.data
    assert b'name="email"' in response.data
    assert b'name="message"' in response.data

def test_contact_form_rejects_invalid_input(client):
    response = client.post('/contact', data={
        "name": "Test User",
        "email": "not-an-email",
        "message": "Hello"
    })

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"

def test_contact_form_requires_resend_api_key(client, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    response = client.post('/contact', data={
        "name": "Test User",
        "email": "test@example.com",
        "message": "Hello"
    })

    assert response.status_code == 503
    assert response.get_json()["status"] == "error"

def test_contact_form_sends_email(client, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-api-key")
    sent_requests = []

    def send_request(*args, **kwargs):
        sent_requests.append((args, kwargs))
        return SimpleNamespace(status_code=200, text="")

    monkeypatch.setattr("webapp.app.requests.post", send_request)
    response = client.post('/contact', data={
        "name": "Test User",
        "email": "test@example.com",
        "message": "Please contact me."
    })

    assert response.status_code == 200
    assert response.get_json()["status"] == "success"
    assert len(sent_requests) == 1
    args, kwargs = sent_requests[0]
    assert args == ("https://api.resend.com/emails",)
    assert kwargs["headers"]["Authorization"] == "Bearer test-api-key"
    assert kwargs["json"]["to"] == ["gumbochumatatenda1@gmail.com"]
    assert "Please contact me." in kwargs["json"]["text"]

def test_contact_form_reports_resend_failure(client, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-api-key")

    monkeypatch.setattr(
        "webapp.app.requests.post",
        lambda *args, **kwargs: SimpleNamespace(status_code=500, text="Resend error"),
    )
    response = client.post('/contact', data={
        "name": "Test User",
        "email": "test@example.com",
        "message": "Please contact me."
    })

    assert response.status_code == 500
    assert response.get_json()["status"] == "error"
    assert "Resend error" not in response.get_json()["message"]

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