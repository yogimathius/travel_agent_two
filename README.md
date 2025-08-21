# Travel Agent AI

An AI-powered travel agent that helps users search and book domestic flights using natural language conversation.

## Features

- Real-time flight search and pricing
- Natural language conversation interface
- Flight details including layovers, baggage policies
- Passenger information collection
- Booking simulation (no actual purchases)

## Tech Stack

- **Backend**: Python + FastAPI
- **AI**: GitHub Models (GPT-4o-mini)
- **Flight Data**: Amadeus API
- **Testing**: pytest

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in API keys
3. Install dependencies: `poetry install`
4. Run the server: `poetry run uvicorn src.travel_agent.main:app --reload`

## API Keys Required

- GitHub Personal Access Token (for GitHub Models)
- Amadeus API credentials (free tier available)

## Usage

Visit `http://localhost:8000/docs` for the API documentation and interactive testing interface.