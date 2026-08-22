from fastapi.testclient import TestClient
from sqlmodel import Session
from post.models import Post
from post.services import PostService

# Note: Tests will return 401 if not authenticated.
# To fully test CRUD, override the auth dependency in conftest.py 
# or generate a mock token.

def test_read_posts(client: TestClient):
    response = client.get("/posts/")
    # Ensure it returns 401 Unauthorized initially since we added JWT auth
    assert response.status_code == 401
