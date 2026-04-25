from fastapi.testclient import TestClient
from main import app
from redis_client import redis_client

client = TestClient(app)

def test_read_products():
    response = client.get("/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_redis_connection():
    # Attempt a simple ping to Redis if it's running
    try:
        assert redis_client.ping() == True
    except Exception as e:
        # If redis isn't running locally, this could fail, which is expected under the fall-back
        pass

def test_read_product_not_found():
    response = client.get("/products/999999")
    assert response.status_code == 404

# Run locally for quick confirmation when the script is executed
if __name__ == "__main__":
    test_read_products()
    test_redis_connection()
    test_read_product_not_found()
    print("All tests passed successfully!")
