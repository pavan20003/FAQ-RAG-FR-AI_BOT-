from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok_without_external_services() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_page_and_widget_script_are_served() -> None:
    client = TestClient(create_app())
    demo = client.get("/demo")
    script = client.get("/widget/chat.js")

    assert demo.status_code == 200
    assert 'data-api-url="/"' in demo.text
    assert script.status_code == 200
    assert "innerHTML" not in script.text
