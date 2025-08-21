import pytest
import sys
import os
from datetime import date, datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from travel_agent.models import (
    Airport, Flight, FlightSegment, FlightSearchRequest,
    PassengerInfo, ConversationSession, CabinClass, FlightType,
    ConversationState, BaggageInfo, BagageType
)


class TestAirport:
    def test_airport_creation(self):
        airport = Airport(
            code="LAX",
            name="Los Angeles International Airport",
            city="Los Angeles"
        )
        assert airport.code == "LAX"
        assert airport.country == "US"  # Default value


class TestPassengerInfo:
    def test_passenger_creation(self):
        passenger = PassengerInfo(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            email="john@example.com",
            phone="+1234567890"
        )
        assert passenger.first_name == "John"
        assert passenger.date_of_birth == date(1990, 1, 1)
    
    def test_passenger_validation(self):
        with pytest.raises(ValueError):
            PassengerInfo(
                first_name="John",
                last_name="Doe",
                date_of_birth="invalid-date",
                email="invalid-email",
                phone="+1234567890"
            )


class TestFlightSearchRequest:
    def test_basic_search_request(self):
        request = FlightSearchRequest(
            origin="LAX",
            destination="NYC",
            departure_date=date(2025, 12, 15)
        )
        assert request.origin == "LAX"
        assert request.flight_type == FlightType.ONE_WAY
        assert request.adults == 1
        assert request.cabin_class == CabinClass.ECONOMY
    
    def test_round_trip_request(self):
        request = FlightSearchRequest(
            origin="LAX",
            destination="NYC",
            departure_date=date(2025, 12, 15),
            return_date=date(2025, 12, 22),
            flight_type=FlightType.ROUND_TRIP
        )
        assert request.return_date == date(2025, 12, 22)
        assert request.flight_type == FlightType.ROUND_TRIP
    
    def test_adults_validation(self):
        with pytest.raises(ValueError):
            FlightSearchRequest(
                origin="LAX",
                destination="NYC",
                departure_date=date(2025, 12, 15),
                adults=0  # Invalid: must be >= 1
            )


class TestFlight:
    def setup_method(self):
        self.lax = Airport(code="LAX", name="LAX", city="Los Angeles")
        self.jfk = Airport(code="JFK", name="JFK", city="New York")
        
        self.segment = FlightSegment(
            airline="American Airlines",
            flight_number="AA100",
            departure_airport=self.lax,
            arrival_airport=self.jfk,
            departure_time=datetime(2025, 12, 15, 8, 0),
            arrival_time=datetime(2025, 12, 15, 16, 30),
            duration="5h 30m"
        )
        
        self.baggage = [
            BaggageInfo(type=BagageType.CARRY_ON, included=True),
            BaggageInfo(type=BagageType.CHECKED, included=False, fee=35.0)
        ]
    
    def test_direct_flight(self):
        flight = Flight(
            segments=[self.segment],
            total_duration="5h 30m",
            stops=0,
            price=299.99,
            cabin_class=CabinClass.ECONOMY,
            baggage_info=self.baggage
        )
        
        assert flight.is_direct is True
        assert flight.stops == 0
        assert flight.origin.code == "LAX"
        assert flight.destination.code == "JFK"
    
    def test_connecting_flight(self):
        ord_airport = Airport(code="ORD", name="ORD", city="Chicago")
        
        segment2 = FlightSegment(
            airline="American Airlines",
            flight_number="AA200",
            departure_airport=ord_airport,
            arrival_airport=self.jfk,
            departure_time=datetime(2025, 12, 15, 18, 0),
            arrival_time=datetime(2025, 12, 15, 21, 30),
            duration="2h 30m"
        )
        
        flight = Flight(
            segments=[self.segment, segment2],
            total_duration="8h 30m",
            stops=1,
            price=249.99,
            cabin_class=CabinClass.ECONOMY,
            baggage_info=self.baggage
        )
        
        assert flight.is_direct is False
        assert flight.stops == 1
        assert flight.origin.code == "LAX"
        assert flight.destination.code == "JFK"


class TestConversationSession:
    def test_session_creation(self):
        session = ConversationSession(session_id="test-123")
        assert session.session_id == "test-123"
        assert session.state == ConversationState.INITIAL
        assert len(session.messages) == 0
        assert len(session.passengers) == 0
    
    def test_session_with_search(self):
        search_request = FlightSearchRequest(
            origin="LAX",
            destination="NYC",
            departure_date=date(2025, 12, 15)
        )
        
        session = ConversationSession(
            session_id="test-123",
            current_search=search_request,
            state=ConversationState.SHOWING_RESULTS
        )
        
        assert session.current_search.origin == "LAX"
        assert session.state == ConversationState.SHOWING_RESULTS