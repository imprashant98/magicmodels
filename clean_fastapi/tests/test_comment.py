from fastapi.testclient import TestClient

# Note: Tests will return 401 if not authenticated.
# To fully test CRUD, override the auth dependency in conftest.py
# or generate a mock token.


def test_read_comments(client: TestClient):
    response = client.get("/comments/")
    # Ensure it returns 401 Unauthorized initially since we added JWT auth
    assert response.status_code == 401
