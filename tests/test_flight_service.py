import pytest
import sys
import os
from datetime import date
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from travel_agent.flight_service import MockFlightService
from travel_agent.models import FlightSearchRequest, CabinClass, FlightType


class TestMockFlightService:
    def setup_method(self):
        self.service = MockFlightService()
    
    def test_airport_resolution(self):
        # Test airport code resolution
        airport = self.service._resolve_airport("LAX")
        assert airport is not None
        assert airport.code == "LAX"
        
        # Test city name resolution
        airport = self.service._resolve_airport("Los Angeles")
        assert airport is not None
        assert airport.code == "LAX"
        
        # Test unknown location
        airport = self.service._resolve_airport("UNKNOWN")
        assert airport is None
    
    @pytest.mark.asyncio
    async def test_basic_flight_search(self):
        request = FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date(2025, 12, 15),
            cabin_class=CabinClass.ECONOMY
        )
        
        response = await self.service.search_flights(request)
        
        assert response.request.origin == "LAX"
        assert response.request.destination == "JFK"
        assert len(response.flights) > 0
        assert response.total_results == len(response.flights)
        assert response.search_id.startswith("search_")
    
    @pytest.mark.asyncio
    async def test_direct_flights_only(self):
        request = FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date(2025, 12, 15),
            direct_only=True
        )
        
        response = await self.service.search_flights(request)
        
        # All flights should be direct (0 stops)
        for flight in response.flights:
            assert flight.stops == 0
            assert flight.is_direct is True
    
    @pytest.mark.asyncio
    async def test_price_filtering(self):
        request = FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date(2025, 12, 15),
            max_price=500.0
        )
        
        response = await self.service.search_flights(request)
        
        # All flights should be under the max price
        for flight in response.flights:
            assert flight.price <= 500.0
    
    @pytest.mark.asyncio
    async def test_cabin_class_pricing(self):
        economy_request = FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date(2025, 12, 15),
            cabin_class=CabinClass.ECONOMY
        )
        
        business_request = FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date(2025, 12, 15),
            cabin_class=CabinClass.BUSINESS
        )
        
        economy_response = await self.service.search_flights(economy_request)
        business_response = await self.service.search_flights(business_request)
        
        # Business class should be more expensive than economy
        if economy_response.flights and business_response.flights:
            economy_price = economy_response.flights[0].price
            business_price = business_response.flights[0].price
            assert business_price > economy_price
    
    @pytest.mark.asyncio
    async def test_unknown_airport(self):
        request = FlightSearchRequest(
            origin="UNKNOWN",
            destination="JFK",
            departure_date=date(2025, 12, 15)
        )
        
        with pytest.raises(ValueError, match="Unknown origin"):
            await self.service.search_flights(request)
    
    def test_baggage_info_generation(self):
        # Test economy class baggage
        economy_baggage = self.service._generate_baggage_info(CabinClass.ECONOMY)
        assert len(economy_baggage) == 2
        
        carry_on = next(b for b in economy_baggage if b.type.value == "carry_on")
        checked = next(b for b in economy_baggage if b.type.value == "checked")
        
        assert carry_on.included is True
        assert checked.included is False
        assert checked.fee == 35.0
        
        # Test business class baggage
        business_baggage = self.service._generate_baggage_info(CabinClass.BUSINESS)
        carry_on = next(b for b in business_baggage if b.type.value == "carry_on")
        checked = next(b for b in business_baggage if b.type.value == "checked")
        
        assert carry_on.included is True
        assert checked.included is True