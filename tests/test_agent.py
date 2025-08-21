import pytest
import sys
import os
from datetime import date
from unittest.mock import AsyncMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from travel_agent.agent import TravelAgent
from travel_agent.models import ChatRequest, ConversationState


class TestTravelAgent:
    def setup_method(self):
        self.agent = TravelAgent(github_token="test_token")
    
    def test_create_session(self):
        session_id = self.agent._create_session()
        assert session_id in self.agent.sessions
        assert self.agent.sessions[session_id].state == ConversationState.INITIAL
    
    def test_get_session_creates_if_not_exists(self):
        session_id = "test-session-123"
        session = self.agent._get_session(session_id)
        assert session.session_id == session_id
        assert session_id in self.agent.sessions
    
    @pytest.mark.asyncio
    async def test_parse_date_formats(self):
        # Test various date formats
        date1 = await self.agent._parse_date("2025-12-15")
        assert date1 == date(2025, 12, 15)
        
        date2 = await self.agent._parse_date("12/15/2025")
        assert date2 == date(2025, 12, 15)
        
        # Invalid date should return None
        invalid_date = await self.agent._parse_date("invalid-date")
        assert invalid_date is None
    
    @pytest.mark.asyncio
    async def test_extract_search_params(self):
        intent_data = {
            "origin": "Los Angeles",
            "destination": "New York",
            "departure_date": "2025-12-15",
            "adults": 2,
            "cabin_class": "business"
        }
        
        search_request = await self.agent._extract_search_params(intent_data)
        
        assert search_request is not None
        assert search_request.origin == "Los Angeles"
        assert search_request.destination == "New York"
        assert search_request.departure_date == date(2025, 12, 15)
        assert search_request.adults == 2
    
    @pytest.mark.asyncio
    async def test_extract_search_params_missing_info(self):
        # Missing required fields
        intent_data = {
            "origin": "Los Angeles",
            # Missing destination and departure_date
        }
        
        search_request = await self.agent._extract_search_params(intent_data)
        assert search_request is None
    
    @pytest.mark.asyncio
    @patch('travel_agent.agent.GitHubModelsClient.extract_travel_intent')
    @patch('travel_agent.agent.GitHubModelsClient.generate_response')
    async def test_chat_initial_greeting(self, mock_generate, mock_extract):
        # Mock AI responses
        mock_extract.return_value = {
            "intent": "other",
            "user_message": "Hello"
        }
        mock_generate.return_value = "Hello! I'm your travel agent. How can I help you today?"
        
        request = ChatRequest(message="Hello")
        response = await self.agent.chat(request)
        
        assert response.response == "Hello! I'm your travel agent. How can I help you today?"
        assert response.state == ConversationState.INITIAL
    
    @pytest.mark.asyncio
    @patch('travel_agent.agent.GitHubModelsClient.extract_travel_intent')
    @patch('travel_agent.agent.MockFlightService.search_flights')
    async def test_chat_flight_search(self, mock_search, mock_extract):
        # Mock intent extraction
        mock_extract.return_value = {
            "intent": "search_flights",
            "origin": "LAX",
            "destination": "JFK",
            "departure_date": "2025-12-15",
            "adults": 1,
            "cabin_class": "economy"
        }
        
        # Mock flight service response
        from travel_agent.models import FlightSearchResponse, Airport, Flight, FlightSegment, BaggageInfo, BagageType, CabinClass
        from datetime import datetime
        
        airport_lax = Airport(code="LAX", name="LAX", city="Los Angeles")
        airport_jfk = Airport(code="JFK", name="JFK", city="New York")
        
        segment = FlightSegment(
            airline="Test Airlines",
            flight_number="TA123",
            departure_airport=airport_lax,
            arrival_airport=airport_jfk,
            departure_time=datetime(2025, 12, 15, 8, 0),
            arrival_time=datetime(2025, 12, 15, 16, 30),
            duration="5h 30m"
        )
        
        flight = Flight(
            segments=[segment],
            total_duration="5h 30m",
            stops=0,
            price=299.99,
            cabin_class=CabinClass.ECONOMY,
            baggage_info=[
                BaggageInfo(type=BagageType.CARRY_ON, included=True),
                BaggageInfo(type=BagageType.CHECKED, included=False, fee=35.0)
            ]
        )
        
        from travel_agent.models import FlightSearchRequest, FlightType
        
        search_request = FlightSearchRequest(
            origin="LAX",
            destination="JFK", 
            departure_date=date(2025, 12, 15),
            flight_type=FlightType.ONE_WAY
        )
        
        mock_search.return_value = FlightSearchResponse(
            request=search_request,
            flights=[flight],
            search_id="test123",
            total_results=1
        )
        
        request = ChatRequest(message="I want to fly from LAX to JFK on December 15th")
        response = await self.agent.chat(request)
        
        assert "found 1 flights" in response.response
        assert "LAX → JFK" in response.response
        assert "$299.99" in response.response
        assert response.state == ConversationState.SHOWING_RESULTS
    
    def test_format_flight_display(self):
        from travel_agent.models import Airport, Flight, FlightSegment, BaggageInfo, BagageType, CabinClass
        from datetime import datetime
        
        airport_lax = Airport(code="LAX", name="LAX", city="Los Angeles")
        airport_jfk = Airport(code="JFK", name="JFK", city="New York")
        
        segment = FlightSegment(
            airline="Test Airlines",
            flight_number="TA123",
            departure_airport=airport_lax,
            arrival_airport=airport_jfk,
            departure_time=datetime(2025, 12, 15, 8, 0),
            arrival_time=datetime(2025, 12, 15, 16, 30),
            duration="5h 30m"
        )
        
        flight = Flight(
            segments=[segment],
            total_duration="5h 30m",
            stops=0,
            price=299.99,
            cabin_class=CabinClass.ECONOMY,
            baggage_info=[
                BaggageInfo(type=BagageType.CARRY_ON, included=True),
                BaggageInfo(type=BagageType.CHECKED, included=False, fee=35.0)
            ]
        )
        
        formatted = self.agent._format_flight_for_display(flight, 0)
        
        assert "Option 1" in formatted
        assert "$299.99" in formatted
        assert "Direct" in formatted
        assert "LAX → JFK" in formatted
        assert "Test Airlines TA123" in formatted
    
    def test_format_baggage(self):
        from travel_agent.models import BaggageInfo, BagageType
        
        baggage_info = [
            BaggageInfo(type=BagageType.CARRY_ON, included=True),
            BaggageInfo(type=BagageType.CHECKED, included=False, fee=35.0)
        ]
        
        formatted = self.agent._format_baggage(baggage_info)
        assert "Carry-on included" in formatted
        assert "1st bag: $35.0" in formatted