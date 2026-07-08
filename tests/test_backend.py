from fastapi.testclient import TestClient
from apps.backend.app.main import app

client = TestClient(app)

def test_chat_endpoint(mocker):
    # Mock the Ollama provider generate method
    from packages.providers.ollama import OllamaProvider
    mocker.patch.object(OllamaProvider, 'generate', return_value="Mocked response")

    response = client.post("/chat", json={"message": "Hey!"})
    assert response.status_code == 200
    assert response.json() == {"response": "Mocked response"}

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
