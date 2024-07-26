import pytest
from fastapi.testclient import TestClient
from src.main import app 
from unittest.mock import patch, MagicMock

# Create a TestClient instance
client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch("src.main.get_db_connection") as mock:
        # Create a mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock.return_value = mock_conn
        yield mock_cursor

def test_get_response(mock_db):
    # Arrange
    prompt = "How to install updates?"
    # Mock the fetchall method on the cursor to return the desired output
    mock_db.fetchall.return_value = [("To install updates, please follow the instructions provided in the documentation.",)]

    # Act
    response = client.post("/get-response/", json={"prompt": prompt})

    # Assert
    assert response.status_code == 200
    

def test_submit_feedback():
    # Arrange
    feedback_data = {
        "response_content": "Apologies!",
        "rating": 5
    }

    # Act
    response = client.post("/submit-feedback/", json=feedback_data)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Feedback saved."}