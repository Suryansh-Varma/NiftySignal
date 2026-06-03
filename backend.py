"""
NIFTYSIGNAL CORE STARTUP SCRIPT
Starts and validates the backend API only.
"""

import subprocess
import sys
import time
from pathlib import Path
import socket
import requests

print("\n" + "=" * 80)
print("NIFTYSIGNAL BACKEND STARTUP")
print("=" * 80)

BASE_DIR = Path(__file__).parent
API_SERVER_DIR = BASE_DIR / "api_server"

if not API_SERVER_DIR.exists():
    fallback_api_dir = BASE_DIR / "app" / "api_server"
    if fallback_api_dir.exists():
        API_SERVER_DIR = fallback_api_dir


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_backend_health(url: str, attempts: int = 3) -> bool:
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, timeout=(1, 1.5))
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        if attempt < attempts:
            time.sleep(0.4)

    return False


print("\n[1] Checking Backend API...")
try:
    if is_port_open("127.0.0.1", 8000) and check_backend_health("http://127.0.0.1:8000/api/health"):
        print("    Backend is already running on port 8000 and healthy")
    else:
        print("    Backend not running - starting it now")
except KeyboardInterrupt:
    print("\n    Health check interrupted by user")
    sys.exit(130)

print("\n" + "=" * 80)
print("BACKEND READY")
print("=" * 80)
print("\nOperational command:")
print("   cd app/api_server")
print("   python -m uvicorn main:app --reload --port 8000")

response = input("\nWould you like to start the backend now? (y/n): ")

if response.lower() == 'y':
    if not API_SERVER_DIR.exists():
        print(f"\nERROR: Backend directory not found: {API_SERVER_DIR}")
        print("Expected either './api_server' or './app/api_server'.")
        sys.exit(1)

    print("\n1. Starting Backend API (Port 8000)...")
    backend_cmd = "python -m uvicorn main:app --reload --port 8000"
    subprocess.Popen(
        ["cmd", "/k", backend_cmd],
        cwd=str(API_SERVER_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        shell=False,
    )

    print("\n" + "=" * 80)
    print("NIFTYSIGNAL BACKEND ENGAGED!")
    print("=" * 80)
    print("\n API Gateway:    http://localhost:8000")
    print("\n" + "=" * 80 + "\n")
else:
    print("\nInitialization aborted.")
