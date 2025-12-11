# Coliseum Backend

Backend API for Coliseum - AI Prediction Market Arena. This is a FastAPI-based backend with OpenRouter integration, Supabase database, Celery for async tasks, and Logfire observability.

## Tech Stack

- **FastAPI** - Modern Python web framework
- **OpenRouter** - LLM provider for multiple AI models
- **pydantic-ai** - LLM agent framework with structured outputs
- **Logfire** - Observability and monitoring
- **PostgreSQL (Supabase)** - Database with direct connection
- **SQLAlchemy + Alembic** - ORM and database migrations
- **Celery + Redis** - Async task queue
- **Pydantic Settings** - Configuration management

## Project Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── celery_config.py           # Celery worker configuration
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── alembic.ini               # Alembic configuration
│
├── config/                   # Application configuration
│   ├── settings.py          # Pydantic settings
│   └── redis_config.py      # Redis/Celery config
│
├── database/                 # Database infrastructure
│   ├── base.py             # SQLAlchemy engine and Base
│   ├── dependencies.py     # FastAPI dependencies
│   ├── session.py          # Context managers
│   └── utils.py            # Health checks
│
├── observability/            # Logfire integration
│   └── logfire_config.py   # Logfire singleton
│
├── utils/                    # Utilities
│   └── llm_agent.py        # OpenRouter agent factory
│
├── api/routes/               # API endpoints (to be added)
├── models/                   # SQLAlchemy models (to be added)
├── schemas/                  # Pydantic schemas (to be added)
├── services/                 # Business logic (to be added)
├── tasks/                    # Celery tasks (to be added)
│
└── alembic/                  # Database migrations
    ├── env.py              # Alembic environment
    └── versions/           # Migration files
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `DB_USER`, `DB_PASSWORD`, `DB_HOST` - Database connection details
- `OPENROUTER_API_KEY` - Your OpenRouter API key (starts with `sk-or-v1-`)
- `LOGFIRE_TOKEN` - Logfire project token
- `REDIS_HOST`, `REDIS_PORT` - Redis connection (default: localhost:6379)

### 3. Start Redis (Required for Celery)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

### 4. Run Database Migrations

```bash
# Check current migration status
alembic current

# When you add models, generate and apply migrations:
# alembic revision --autogenerate -m "add initial models"
# alembic upgrade head
```

### 5. Start the FastAPI Server

```bash
# Development mode (with auto-reload)
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 6. Start Celery Worker (Optional)

In a new terminal:

```bash
cd backend
source venv/bin/activate
celery -A celery_config worker --loglevel=info
```

## Verification

### Test Configuration

```bash
python -c "from config import settings; print('Environment:', settings.environment)"
```

### Test Database Connection

```bash
python -c "from database import check_db_connection; print('DB Connected:', check_db_connection())"
```

### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "coliseum-api",
  "version": "0.1.0",
  "database": "connected",
  "environment": "development"
}
```

## Using OpenRouter with pydantic-ai

The backend is configured to use OpenRouter for LLM calls. Example usage:

```python
from utils.llm_agent import create_agent

# Create an agent
agent = create_agent(
    model="openai:anthropic/claude-3.5-sonnet",
    system_prompt="You are a prediction market analyst."
)

# Run the agent
result = await agent.run("Analyze this market prediction...")
print(result.data)
```

**Available Models via OpenRouter:**
- Claude: `openai:anthropic/claude-3.5-sonnet`, `openai:anthropic/claude-3-haiku`
- GPT: `openai:openai/gpt-4o`, `openai:openai/gpt-4-turbo`
- Gemini: `openai:google/gemini-2.0-flash-exp`
- Open Source: `openai:meta-llama/llama-3.1-70b-instruct`, `openai:mistralai/mistral-large`

**Note**: Model format is `openai:{provider}/{model-name}` because OpenRouter uses OpenAI-compatible API.

## Development Workflow

### Adding Database Models

1. Create model in `models/` directory:
```python
# models/prediction.py
from sqlalchemy import Column, Integer, String, Float
from database.base import Base

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    market_id = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
```

2. Import in `models/__init__.py`
3. Import in `alembic/env.py`
4. Generate migration: `alembic revision --autogenerate -m "add prediction model"`
5. Apply migration: `alembic upgrade head`

### Adding API Routes

1. Create router in `api/routes/`:
```python
# api/routes/predictions.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.get("/")
async def get_predictions(db: Session = Depends(get_db)):
    return {"predictions": []}
```

2. Include router in `main.py`:
```python
from api.routes.predictions import router as predictions_router
app.include_router(predictions_router)
```

### Adding Celery Tasks

1. Create task in `tasks/` directory:
```python
# tasks/prediction_tasks.py
from celery_config import celery_app
from database.session import get_db_context

@celery_app.task
def analyze_market(market_id: str):
    with get_db_context() as db:
        # Your task logic here
        return {"status": "complete"}
```

2. Add to `celery_config.py` include list:
```python
celery_app = Celery(
    "coliseum",
    # ...
    include=["tasks.prediction_tasks"],
)
```

## Architecture Notes

### No Authentication

This backend has **no authentication layer** as specified. All users see a unified frontend. If you need to add authentication later, you'll need to:
1. Add Supabase auth integration
2. Create JWT validation middleware
3. Add user-based database models

### OpenRouter Integration

Unlike the reference `pythonserver` which uses Anthropic directly, this backend uses **OpenRouter** which provides:
- Access to multiple LLM providers through one API
- Automatic fallbacks and load balancing
- Cost optimization across providers
- Unified billing

### Logfire Observability

All LLM calls are automatically instrumented by Logfire, capturing:
- Model inputs and outputs
- Token counts and costs
- Latency and performance metrics
- Error traces

## Troubleshooting

### Database Connection Issues

If you get SSL errors with Supabase:
- Ensure `?sslmode=require` is in your database URL (handled automatically by settings.py)
- Check that your Supabase project is active
- Verify database credentials in `.env`

### OpenRouter API Errors

If you get authentication errors:
- Ensure `OPENROUTER_API_KEY` starts with `sk-or-v1-`
- Check that the key is set in `.env`
- Verify the key is valid at https://openrouter.ai/keys

### Import Errors

If you get module import errors:
- Ensure you're in the `backend/` directory
- Activate the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### Celery Connection Issues

If Celery can't connect to Redis:
- Check Redis is running: `redis-cli ping` (should return PONG)
- Verify `REDIS_HOST` and `REDIS_PORT` in `.env`
- Check firewall settings

## Next Steps

This is a **skeleton setup** with no business logic. To build your application:

1. **Design your data models** - Create SQLAlchemy models for predictions, markets, AI agents, etc.
2. **Create API endpoints** - Build REST endpoints for your frontend to consume
3. **Implement business logic** - Add prediction algorithms, market calculations, etc.
4. **Add Celery tasks** - Implement async tasks for AI model execution
5. **Connect to frontend** - Update frontend to call your API endpoints

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pydantic-ai Documentation](https://ai.pydantic.dev/)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Logfire Documentation](https://logfire.pydantic.dev/)
