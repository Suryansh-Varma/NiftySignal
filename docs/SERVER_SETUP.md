# Server Setup Guide

## Prerequisites

1. **Install Python dependencies**:
   ```bash
   pip install -e .
   ```
   Or install manually:
   ```bash
   pip install fastapi uvicorn pandas numpy scikit-learn pyarrow
   ```

2. **Ensure you have trained the model** (optional, but recommended):
   ```bash
   python app/api/train_model.py
   ```
   This generates `results/latest_recommendations.csv` which the API serves.

## Running the API Server

### Option 1: From project root (Recommended)
```bash
# From the project root directory
uvicorn app.api_server.main:app --reload --port 8000
```

### Option 2: From api_server directory
```bash
cd app/api_server
uvicorn main:app --reload --port 8000
```

### Option 3: Using Python module
```bash
python -m uvicorn app.api_server.main:app --reload --port 8000
```

## Server Endpoints

Once running, the server will be available at:
- **API Base URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/api/health`
- **Recommendations**: `http://localhost:8000/api/recommendations`
- **Filtered Recommendations**: `http://localhost:8000/api/recommendations?symbol=RELIANCE.NS`
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

## Testing the Server

### Using curl:
```bash
# Health check
curl http://localhost:8000/api/health

# Get all recommendations
curl http://localhost:8000/api/recommendations

# Get specific symbol
curl http://localhost:8000/api/recommendations?symbol=RELIANCE.NS
```

### Using Python:
```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# Get recommendations
response = requests.get("http://localhost:8000/api/recommendations")
print(response.json())
```

## Environment Variables

You can customize CORS origins using environment variables:

```bash
# Windows PowerShell
$env:ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
uvicorn app.api_server.main:app --reload --port 8000

# Windows CMD
set ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
uvicorn app.api_server.main:app --reload --port 8000

# Linux/Mac
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
uvicorn app.api_server.main:app --reload --port 8000
```

## Troubleshooting

### Port already in use
If port 8000 is busy, use a different port:
```bash
uvicorn app.api_server.main:app --reload --port 8001
```

### Missing recommendations file
If you see "Recommendations not found" error:
1. Run the model training script first:
   ```bash
   python app/api/train_model.py
   ```
2. This will create `results/latest_recommendations.csv`

### Module not found errors
Make sure you're running from the project root and have installed dependencies:
```bash
pip install -e .
```

## Running in Production

For production, use a production ASGI server like Gunicorn with Uvicorn workers:

```bash
pip install gunicorn
gunicorn app.api_server.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Or use Uvicorn with production settings:
```bash
uvicorn app.api_server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

