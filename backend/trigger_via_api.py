import asyncio
from fastapi.testclient import TestClient
from app.api.main import app

def main():
    client = TestClient(app)
    # create workspace and job
    # The API probably has endpoints for this.
    pass

if __name__ == "__main__":
    main()
