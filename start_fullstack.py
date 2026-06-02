"""
NIFTYSIGNAL CORE STARTUP SCRIPT
Starts the Frontend and Backend API
"""

import subprocess
import sys
import time
from pathlib import Path
import socket
import requests

print("\n" + "="*80)
print("NIFTYSIGNAL TERMINAL STARTUP")
print("="*80)

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"
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

# [1] Environment Verification
print("\n[1] Checking Node.js...")
try:
    result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"    Node.js version: {result.stdout.strip()}")
    else:
        print("    ERROR: Node.js not found!")
        sys.exit(1)
except FileNotFoundError:
    print("    ERROR: Node.js not found!")
    sys.exit(1)

# [2] Frontend Dependency Sync
print("\n[2] Checking Frontend Dependencies...")
if not (FRONTEND_DIR / "node_modules").exists():
    print("    Installing frontend dependencies...")
    print("    This may take a few minutes...")
    subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True)
    print("    Frontend dependencies installed!")
else:
    print("    Frontend dependencies already installed")


# [3] Backend Health Check
print("\n[3] Checking Backend API...")
try:
    if is_port_open("127.0.0.1", 8000) and check_backend_health("http://127.0.0.1:8000/api/health"):
        print("    Backend is already running on port 8000 and healthy")
    else:
        print("    Backend not running - you need to start it separately")
        print("    Run: cd app/api_server && python -m uvicorn main:app --port 8000")
except requests.exceptions.RequestException:
    print("    Backend not running - you need to start it separately")
    print("    Run: cd app/api_server && python -m uvicorn main:app --port 8000")
except KeyboardInterrupt:
    print("\n    Health check interrupted by user")
    sys.exit(130)

# [4] Environment Setup
print("\n[4] Checking Frontend Environment...")
env_file = FRONTEND_DIR / ".env.local"

if not env_file.exists():
    print("    Creating .env.local file...")
    with open(env_file, 'w') as f:
        f.write("# Frontend Environment Variables\n")
        f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
    print("    Created .env.local with default values")
else:
    print("    .env.local already exists")

print("\n" + "="*80)
print("READY TO INITIALIZE!")
print("="*80)

print("\nOPERATIONAL INSTRUCTIONS:")
print("\n1. BACKEND:")
print("   cd app/api_server")
print("   python -m uvicorn main:app --reload --port 8000")

print("\n2. FRONTEND:")
print("   cd frontend")
print("   npm run dev")

print("\n" + "="*80)
print("Visit: http://localhost:3000")
print("="*80)

response = input("\nWould you like to start the production stack now? (y/n): ")

if response.lower() == 'y':
    print("\n[Initializing Stack...]")

    if not API_SERVER_DIR.exists():
        print(f"\nERROR: Backend directory not found: {API_SERVER_DIR}")
        print("Expected either './api_server' or './app/api_server'.")
        sys.exit(1)

    if not FRONTEND_DIR.exists():
        print(f"\nERROR: Frontend directory not found: {FRONTEND_DIR}")
        sys.exit(1)
    
    # Start backend
    print("\n1. Starting Backend API (Port 8000)...")
    backend_cmd = "python -m uvicorn main:app --reload --port 8000"
    subprocess.Popen(
        ["cmd", "/k", backend_cmd],
        cwd=str(API_SERVER_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        shell=False,
    )
    time.sleep(2)
    
    # Start Frontend
    print("2. Starting Frontend (Port 3000)...")
    frontend_cmd = "npm run dev"
    subprocess.Popen(
        ["cmd", "/k", frontend_cmd],
        cwd=str(FRONTEND_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        shell=False,
    )
    
    print("\n" + "="*80)
    print("NIFTYSIGNAL TERMINAL ENGAGED!")
    print("="*80)
    print("\n API Gateway:    http://localhost:8000")
    print("Terminal UI:    http://localhost:3000")
    print("\n" + "="*80 + "\n")
else:
    print("\nInitialization aborted.")
