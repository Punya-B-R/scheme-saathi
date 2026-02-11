"""
Start the Scheme Saathi backend server.
Run from backend directory: python run_server.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 60)
    print("\nServer will start at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Alternative docs: http://localhost:8000/redoc")
    print("\nPress CTRL+C to stop\n")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
