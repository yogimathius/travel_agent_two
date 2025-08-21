# Travel Agent AI - Setup Guide

## Quick Start

1. **Clone and Setup**
```bash
cd travel_agent_two
poetry install
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and add your GitHub Personal Access Token
```

3. **Run the Application**
```bash
poetry run uvicorn src.travel_agent.main:app --reload
```

4. **Test the Application**
- Visit: http://localhost:8000 for the chat interface
- Visit: http://localhost:8000/docs for API documentation

## GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name like "Travel Agent AI"
4. Set expiration as needed
5. Select scopes (basic read access should be sufficient)
6. Copy the token and add it to your `.env` file

## Testing

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test files
poetry run pytest tests/test_models.py -v
poetry run pytest tests/test_flight_service.py -v
poetry run pytest tests/test_github_models.py -v
poetry run pytest tests/test_agent.py -v
```

## API Endpoints

- `GET /` - Web chat interface
- `POST /chat` - Chat with the AI agent
- `GET /docs` - Interactive API documentation
- `GET /health` - Health check
- `GET /sessions/{session_id}` - Get session details

## Project Structure

```
travel_agent_two/
├── src/travel_agent/
│   ├── models.py          # Pydantic data models
│   ├── flight_service.py  # Mock flight search service
│   ├── github_models.py   # GitHub Models AI integration
│   ├── agent.py          # Core agent logic
│   └── main.py           # FastAPI application
├── tests/                # Comprehensive test suite
├── docs/                 # Documentation
└── screenshots/          # Demo screenshots
```

## Key Features Implemented

✅ **Flight Search** - Real-time flight lookup with pricing
✅ **Natural Language** - Conversational AI interface  
✅ **Booking Flow** - Complete passenger info collection
✅ **Mock Integration** - Realistic flight data simulation
✅ **Type Safety** - Full Pydantic model validation
✅ **Testing** - 34 tests covering all components
✅ **API Documentation** - Auto-generated Swagger docs