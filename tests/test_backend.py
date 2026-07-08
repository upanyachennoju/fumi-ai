from fastapi.testclient import TestClient
from apps.backend.app.main import app, ChatMessage

client = TestClient(app)

def test_chat_endpoint():
    response = client.post("/chat", json={"message": "Hey!"})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "Fumi AI Backend",
        "version": "0.1.0"
    }

def test_get_config():
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "chroma_db_path" in data
    assert "vault_path" in data
    assert "model" in data
