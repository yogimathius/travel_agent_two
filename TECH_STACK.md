# Tech Stack Selection & Justification

## Selected Technology Stack

### 1. Language & Framework
**Python + FastAPI**
- **Justification**: 
  - Simple, rapid development
  - Excellent AI/ML library ecosystem
  - FastAPI provides async support for API calls
  - Easy testing with pytest
  - Great documentation and type hints

### 2. Language Model
**GitHub Models - GPT-4o-mini**
- **Justification**:
  - Free tier available through GitHub
  - Excellent conversation capabilities
  - Good instruction following for structured tasks
  - Suitable for travel booking conversations
  - No local model management needed

### 3. Logic Model/Framework
**Custom Decision Tree + Pydantic Models**
- **Justification**:
  - Deterministic decision-making for flight recommendations
  - Easy to test and debug
  - Pydantic for data validation and structure
  - Transparent logic flow for booking process

### 4. Flight Data API
**Amadeus for Developers (Free Tier)**
- **Justification**:
  - Real flight data with free tier
  - Comprehensive flight search capabilities
  - Includes pricing, schedules, and airline details
  - Good documentation and Python SDK

### 5. Session Management
**In-memory with Python dictionaries**
- **Justification**:
  - Simple for demo purposes
  - No external database dependencies
  - Easy to implement and test
  - Sufficient for single-session interactions

### 6. Testing Framework
**pytest + httpx**
- **Justification**:
  - TDD-friendly with excellent test discovery
  - Async testing support for API calls
  - Fixtures for test data management
  - Mocking capabilities for external APIs

### 7. Development Environment
**Poetry for dependency management**
- **Justification**:
  - Deterministic builds
  - Easy virtual environment management
  - Clean dependency specification
  - Good for reproducible setups

## Architecture Overview

```
User Input → FastAPI Endpoint → GitHub Models (NLU/NLG) → Decision Logic → Flight API → Response
                                    ↓
                              Session State Management
```

## Alternative Considerations

### Why not other LLMs?
- **OpenAI GPT**: Requires paid API key
- **Local models**: Complex setup, resource intensive
- **Anthropic Claude**: Paid service
- **GitHub Models**: Free tier, easy integration

### Why not other frameworks?
- **Django**: Overkill for simple API
- **Flask**: Less modern async support
- **Node.js**: Less AI/ML ecosystem
- **FastAPI**: Perfect balance of simplicity and features

### Why not other flight APIs?
- **Skyscanner**: More complex integration
- **Google Flights**: No direct API access
- **Amadeus**: Good free tier, comprehensive data

This stack provides the optimal balance of simplicity, functionality, and cost-effectiveness for the project requirements.