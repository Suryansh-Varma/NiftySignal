# NiftySIgnal Security Guide

This document outlines security measures, best practices, and hardening steps for the NiftySIgnal application.

## 1. Frontend Security (Next.js/React)

### Input Validation

All user inputs are validated on both client and server:

**Portfolio Form Validation:**
- Symbol: Must be valid NSE format (e.g., RELIANCE.NS or RELIANCE)
- Quantity: Must be integer between 1 and 1,000,000
- Buy price: Must be between ₹0.01 and ₹1,000,000
- Buy date: Cannot be in future or >50 years in past

**Code Example:**
```typescript
// Validate quantity
if (!formData.quantity || formData.quantity < 1) {
  setError('Quantity must be at least 1 share.')
  return
}

// Validate price
if (formData.buy_price <= 0 || formData.buy_price > 1000000) {
  setError('Buy price must be between ₹0.01 and ₹1,000,000.')
  return
}

// Validate date
const buyDate = new Date(formData.buy_date)
if (buyDate > new Date()) {
  setError('Buy date cannot be in the future.')
  return
}
```

### Rate Limiting (Client-side)

Prevents brute force and spam attacks:

**Portfolio Form:**
- 3-second cooldown between form submissions
- 2-second cooldown between delete operations
- Prevents rapid clicking on buttons

**Implementation:**
```typescript
const [lastSubmitTime, setLastSubmitTime] = useState(0)

// Check rate limit
const now = Date.now()
if (now - lastSubmitTime < 3000) {
  setError('Please wait before submitting again. (3 second cooldown)')
  return
}

// Update timestamp after successful submission
setLastSubmitTime(Date.now())
```

### Confirmation Dialogs

Prevents accidental data loss:

**Delete Position:**
```typescript
const confirmed = window.confirm(
  `Are you sure you want to remove ${symbolName}? This cannot be undone.`
)
if (!confirmed) return
```

### XSS Protection

- React automatically escapes HTML in JSX
- User inputs are never directly inserted into HTML
- All user data is properly escaped in templates

### CSRF Protection

- Uses browser's built-in CSRF protection
- Supabase client handles session tokens securely
- No cross-origin form submissions

### Secure Storage

**Environment Variables:**
```
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com  # Public API URL
NEXT_PUBLIC_WS_URL=wss://yourdomain.com         # Secure WebSocket
NEXT_PUBLIC_SUPABASE_URL=...                    # Supabase public
NEXT_PUBLIC_SUPABASE_ANON_KEY=...               # Anon key (cannot write data)
```

**Sensitive Data:**
- User session tokens are stored in Supabase session storage
- Never stored in local storage or cookies directly
- Authentication handled by Supabase

### Content Security Policy

Add CSP headers in `next.config.js`:

```javascript
const securityHeaders = [
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-inline'; img-src 'self' https:; font-src 'self' https:"
  }
]

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      }
    ]
  }
}
```

## 2. Backend Security (Python/FastAPI)

### Environment Variables

Never commit secrets to version control:

```bash
# .env (NOT committed to git)
DATABASE_URL=postgresql://secure_user:secure_password@host/db
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxx...xxxxxxxx
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
SECRET_KEY=your-super-secret-key-min-32-chars
```

**.gitignore:**
```
.env
.env.local
.env.*.local
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
```

### Input Validation (Pydantic)

All API inputs use Pydantic models for automatic validation:

```python
from pydantic import BaseModel, Field, validator

class PortfolioCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=4, max_length=10)
    quantity: int = Field(..., gt=0, le=1000000)
    buy_price: float = Field(..., gt=0, le=1000000)
    buy_date: str

    @validator('symbol')
    def validate_symbol(cls, v):
        # Ensure symbol is uppercase and valid NSE format
        v = v.upper().strip()
        if not v.endswith('.NS'):
            v = f"{v}.NS"
        return v

    @validator('buy_price')
    def validate_price(cls, v):
        if v <= 0 or v > 1000000:
            raise ValueError('Price must be between ₹0.01 and ₹1,000,000')
        return round(v, 2)
```

### SQL Injection Prevention

Using SQLAlchemy ORM with parameterized queries:

```python
# ✅ SAFE - Uses parameterized queries
from sqlalchemy import select, and_

query = select(Portfolio).where(
    and_(
        Portfolio.user_id == user_id,
        Portfolio.symbol == symbol
    )
)
result = session.execute(query).first()

# ❌ UNSAFE - Never do this
query = f"SELECT * FROM portfolios WHERE user_id = {user_id}"
result = session.execute(text(query))
```

### Authentication & Authorization

**Token Validation:**
```python
from fastapi import Depends, HTTPException, status

async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail='Missing token')
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail='Invalid scheme')
        
        # Validate token with Supabase
        user = supabase.auth.get_user(token)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail='Invalid token')

@app.post("/api/portfolios")
async def create_portfolio(
    data: PortfolioCreateRequest,
    user: dict = Depends(get_current_user)
):
    # User is verified before endpoint executes
    return create_position(user.id, data)
```

### Rate Limiting

Prevent API abuse with rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/portfolios")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def create_portfolio(
    request: Request,
    data: PortfolioCreateRequest,
    user: dict = Depends(get_current_user)
):
    return create_position(user.id, data)
```

**Rate Limiting by User:**
```python
from slowapi.util import get_remote_address

def get_user_id(request: Request, user: dict = Depends(get_current_user)):
    return user.id

@app.post("/api/portfolios")
@limiter.limit("100/hour")  # 100 requests per hour per user
async def create_portfolio(
    request: Request,
    data: PortfolioCreateRequest,
    user_id: str = Depends(get_user_id)
):
    return create_position(user_id, data)
```

### CORS Configuration

Restrict cross-origin requests:

```python
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "http://localhost:3000",  # Dev only
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)
```

### Error Handling

Never expose sensitive information in errors:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full error internally
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return safe error to client
    return JSONResponse(
        status_code=500,
        content={"detail": "An error occurred. Please try again later."}
    )

# Specific exceptions with safe messages
@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred."}
    )
```

### HTTPS / TLS

```python
# Use HTTPS in production
@app.middleware("http")
async def https_redirect(request, call_next):
    if request.url.scheme == "http" and environ.get("ENV") == "production":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url, status_code=301)
    response = await call_next(request)
    return response
```

### Secrets Management

Use environment-based secrets:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str  # Required
    supabase_url: str
    supabase_key: str
    secret_key: str
    debug: bool = False
    cors_origins: list[str] = ["https://yourdomain.com"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

settings = Settings()

# Use in app
if settings.debug:
    logger.warning("Debug mode enabled - should never be True in production")
```

## 3. Database Security

### PostgreSQL Security Best Practices

```sql
-- Create least-privilege user for application
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';

-- Grant specific permissions
GRANT CONNECT ON DATABASE niftysignal TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Enable row-level security if using Supabase
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own portfolios" ON portfolios
  USING (auth.uid() = user_id);
```

### Connection Security

```python
# Use connection pooling with SSL
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    connect_args={
        "ssl": "require",  # Enforce SSL
        "sslmode": "require"
    }
)
```

### Backup Strategy

```bash
# Daily encrypted backup
0 2 * * * pg_dump $DATABASE_URL | gzip | openssl enc -aes-256-cbc -salt -out /backups/db_$(date +\%Y\%m\%d).sql.gz.enc

# Transfer to secure storage
0 3 * * * aws s3 cp /backups/db_*.sql.gz.enc s3://backup-bucket/ --sse AES256
```

## 4. API Security

### HTTP Headers

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### API Versioning

Use versioning for backward compatibility without breaking changes:

```python
@app.get("/api/v1/recommendations")
async def get_recommendations_v1():
    # Stable endpoint
    pass

@app.get("/api/v2/recommendations")
async def get_recommendations_v2():
    # New endpoint with breaking changes
    pass
```

### Request Validation

```python
from fastapi import Header, Query

@app.get("/api/data")
async def get_data(
    user_id: str = Header(...),  # Required header
    limit: int = Query(10, ge=1, le=1000),  # Constrained
):
    # Headers and query strings are validated
    pass
```

## 5. Deployment Security

### Environment Checklist

```yaml
Production Deployment:
  - [ ] DEBUG = False
  - [ ] SECRET_KEY set to secure random string (min 32 chars)
  - [ ] Database password is strong (min 20 chars, mixed)
  - [ ] All API endpoints use HTTPS/TLS
  - [ ] CORS origins restricted to your domain
  - [ ] Rate limiting enabled on all endpoints
  - [ ] Error logging configured (Sentry/CloudWatch)
  - [ ] Database backups automated daily
  - [ ] Firewall rules configured (whitelist only necessary ports)
  - [ ] Security headers enabled
  - [ ] API keys rotated regularly
  - [ ] Dependencies updated (pip audit, npm audit)
```

### Dependencies Audit

```bash
# Python
pip install pip-audit
pip-audit --desc  # Show descriptions of vulnerabilities

# Node.js
npm audit fix  # Auto-fix known vulnerabilities
npm audit --audit-level=high  # Fail if high severity found

# Regular check (weekly)
0 0 * * 0 cd /app && pip-audit --desc 2>&1 | mail admin@yourdomain.com
```

### Nginx Security Configuration

```nginx
# Security headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# Disable server identification
server_tokens off;

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://backend;
}

# SSL/TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

## 6. Monitoring & Incident Response

### Security Logging

```python
import logging

security_logger = logging.getLogger('security')

# Log authentication events
security_logger.warning(f"Failed login attempt from {request.client.host}")
security_logger.info(f"User {user_id} deleted portfolio position {position_id}")

# Log suspicious patterns
if request_count_in_minute > 100:
    security_logger.critical(f"Rate limit exceeded for {request.client.host}")
```

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-url",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

### Regular Security Audits

```bash
# Run monthly security checks
- Dependency vulnerabilities (pip-audit, npm audit)
- API endpoint tests (OWASP Top 10)
- Database integrity checks
- Backup restoration test
- Log review for suspicious patterns
```

## 7. Incident Response Plan

### Security Breach Response

1. **Immediate (0-1 hour):**
   - Isolate affected systems
   - Enable verbose logging
   - Notify security team

2. **Short-term (1-24 hours):**
   - Determine scope of breach
   - Patch vulnerabilities
   - Rotate credentials
   - Review logs for unauthorized access

3. **Medium-term (1-7 days):**
   - Notify users if data exposed
   - Conduct security audit
   - Document findings
   - Update security measures

4. **Long-term (1+ months):**
   - Implement preventive measures
   - Update documentation
   - Staff training
   - Regular audits

### Credentials Rotation

```bash
# Rotate database password monthly
ALTER USER app_user WITH PASSWORD 'new_secure_password_2024';

# Rotate API keys
aws iam create-access-key --user-name app-user  # New key
aws iam delete-access-key --user-name app-user --access-key-id OLD_KEY

# Update in .env and restart services
systemctl restart niftysignal-backend
```

## 8. Compliance

### Data Protection

- **GDPR:** User data can be exported/deleted on request
- **Data Retention:** Portfolio data retained for 7 years per financial regulations
- **Encryption:** All data encrypted at rest (PostgreSQL) and in transit (HTTPS/WSS)

### Audit Trail

```python
# Log all significant user actions
class PortfolioAudit(Base):
    __tablename__ = "portfolio_audits"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    action = Column(String)  # 'create', 'update', 'delete'
    symbol = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)  # For tracking

@app.post("/api/portfolios")
async def create_portfolio(data, user, request):
    # Create audit log
    audit = PortfolioAudit(
        user_id=user.id,
        action="create",
        symbol=data.symbol,
        ip_address=request.client.host
    )
    session.add(audit)
    session.commit()
```

## Support & References

- **OWASP Top 10:** https://owasp.org/Top10/
- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/
- **Supabase Security:** https://supabase.com/docs/guides/auth
- **PostgreSQL Security:** https://www.postgresql.org/docs/current/sql-syntax.html
- **Node.js Security:** https://nodejs.org/en/docs/guides/security/

---

**Last Updated:** March 2026  
**Version:** 1.0
