from datetime import datetime, date, timedelta
from typing import List, Optional
import random
from .models import (
    Flight, FlightSegment, Airport, FlightSearchRequest, FlightSearchResponse,
    BaggageInfo, BagageType, CabinClass
)


class MockFlightService:
    """
    Mock flight service that simulates real flight data for development and demo.
    In production, this would be replaced with Amadeus API integration.
    """
    
    def __init__(self):
        self.airports = {
            "LAX": Airport(code="LAX", name="Los Angeles International", city="Los Angeles"),
            "JFK": Airport(code="JFK", name="John F. Kennedy International", city="New York"),
            "ORD": Airport(code="ORD", name="Chicago O'Hare International", city="Chicago"),
            "DFW": Airport(code="DFW", name="Dallas/Fort Worth International", city="Dallas"),
            "ATL": Airport(code="ATL", name="Hartsfield-Jackson Atlanta International", city="Atlanta"),
            "SFO": Airport(code="SFO", name="San Francisco International", city="San Francisco"),
            "MIA": Airport(code="MIA", name="Miami International", city="Miami"),
            "SEA": Airport(code="SEA", name="Seattle-Tacoma International", city="Seattle"),
            "DEN": Airport(code="DEN", name="Denver International", city="Denver"),
            "LAS": Airport(code="LAS", name="McCarran International", city="Las Vegas"),
        }
        
        self.airlines = [
            "American Airlines", "Delta Air Lines", "United Airlines",
            "Southwest Airlines", "JetBlue Airways", "Alaska Airlines"
        ]
    
    def _resolve_airport(self, location: str) -> Optional[Airport]:
        """Resolve airport code or city name to Airport object."""
        location = location.upper().strip()
        
        # Try exact airport code match
        if location in self.airports:
            return self.airports[location]
        
        # Try city name match
        for airport in self.airports.values():
            if airport.city.upper() == location:
                return airport
        
        return None
    
    def _generate_baggage_info(self, cabin_class: CabinClass) -> List[BaggageInfo]:
        """Generate realistic baggage policies based on cabin class."""
        baggage = []
        
        # Carry-on
        if cabin_class == CabinClass.ECONOMY:
            baggage.append(BaggageInfo(
                type=BagageType.CARRY_ON,
                included=True,
                weight_limit="22x14x9 inches"
            ))
        else:
            baggage.append(BaggageInfo(
                type=BagageType.CARRY_ON,
                included=True,
                weight_limit="22x14x9 inches"
            ))
        
        # Checked bag
        if cabin_class in [CabinClass.BUSINESS, CabinClass.FIRST]:
            baggage.append(BaggageInfo(
                type=BagageType.CHECKED,
                included=True,
                weight_limit="50 lbs"
            ))
        else:
            baggage.append(BaggageInfo(
                type=BagageType.CHECKED,
                included=False,
                fee=35.0,
                weight_limit="50 lbs"
            ))
        
        return baggage
    
    def _calculate_flight_time(self, origin: Airport, destination: Airport) -> timedelta:
        """Calculate realistic flight time between airports."""
        # Simplified distance-based calculation
        base_times = {
            ("LAX", "JFK"): timedelta(hours=5, minutes=30),
            ("LAX", "CHI"): timedelta(hours=4, minutes=15),
            ("JFK", "MIA"): timedelta(hours=3, minutes=10),
            ("SFO", "SEA"): timedelta(hours=2, minutes=30),
            ("DEN", "ATL"): timedelta(hours=3, minutes=45),
        }
        
        key = (origin.code, destination.code)
        reverse_key = (destination.code, origin.code)
        
        if key in base_times:
            return base_times[key]
        elif reverse_key in base_times:
            return base_times[reverse_key]
        else:
            # Default calculation based on rough distance
            return timedelta(hours=random.randint(2, 6), minutes=random.choice([0, 15, 30, 45]))
    
    def _generate_flight_times(self, departure_date: date) -> tuple[datetime, datetime]:
        """Generate realistic departure and arrival times."""
        # Common departure hours
        departure_hour = random.choice([6, 7, 8, 9, 10, 12, 14, 16, 18, 19, 20])
        departure_minute = random.choice([0, 15, 30, 45])
        
        departure_time = datetime.combine(
            departure_date,
            datetime.min.time().replace(hour=departure_hour, minute=departure_minute)
        )
        
        return departure_time
    
    def _generate_direct_flight(self, origin: Airport, destination: Airport, 
                              departure_date: date, cabin_class: CabinClass) -> Flight:
        """Generate a direct flight."""
        airline = random.choice(self.airlines)
        flight_number = f"{airline[:2].upper()}{random.randint(100, 9999)}"
        
        departure_time = self._generate_flight_times(departure_date)
        flight_duration = self._calculate_flight_time(origin, destination)
        arrival_time = departure_time + flight_duration
        
        duration_str = f"{flight_duration.seconds // 3600}h {(flight_duration.seconds % 3600) // 60}m"
        
        segment = FlightSegment(
            airline=airline,
            flight_number=flight_number,
            departure_airport=origin,
            arrival_airport=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration_str,
            aircraft=random.choice(["Boeing 737", "Airbus A320", "Boeing 787"])
        )
        
        # Price calculation based on cabin class and distance
        base_price = random.randint(200, 800)
        multipliers = {
            CabinClass.ECONOMY: 1.0,
            CabinClass.PREMIUM_ECONOMY: 1.5,
            CabinClass.BUSINESS: 3.0,
            CabinClass.FIRST: 5.0
        }
        price = base_price * multipliers[cabin_class]
        
        return Flight(
            segments=[segment],
            total_duration=duration_str,
            stops=0,
            price=round(price, 2),
            cabin_class=cabin_class,
            baggage_info=self._generate_baggage_info(cabin_class),
            is_refundable=cabin_class in [CabinClass.BUSINESS, CabinClass.FIRST]
        )
    
    def _generate_connecting_flight(self, origin: Airport, destination: Airport,
                                  departure_date: date, cabin_class: CabinClass) -> Flight:
        """Generate a flight with one connection."""
        # Choose a random hub airport
        possible_hubs = [code for code in self.airports.keys() 
                        if code not in [origin.code, destination.code]]
        hub_code = random.choice(possible_hubs)
        hub = self.airports[hub_code]
        
        # First segment
        airline1 = random.choice(self.airlines)
        flight_number1 = f"{airline1[:2].upper()}{random.randint(100, 9999)}"
        departure_time1 = self._generate_flight_times(departure_date)
        duration1 = self._calculate_flight_time(origin, hub)
        arrival_time1 = departure_time1 + duration1
        
        # Layover time (45 minutes to 3 hours)
        layover = timedelta(minutes=random.randint(45, 180))
        
        # Second segment
        airline2 = airline1 if random.random() > 0.3 else random.choice(self.airlines)
        flight_number2 = f"{airline2[:2].upper()}{random.randint(100, 9999)}"
        departure_time2 = arrival_time1 + layover
        duration2 = self._calculate_flight_time(hub, destination)
        arrival_time2 = departure_time2 + duration2
        
        segments = [
            FlightSegment(
                airline=airline1,
                flight_number=flight_number1,
                departure_airport=origin,
                arrival_airport=hub,
                departure_time=departure_time1,
                arrival_time=arrival_time1,
                duration=f"{duration1.seconds // 3600}h {(duration1.seconds % 3600) // 60}m",
                aircraft=random.choice(["Boeing 737", "Airbus A320"])
            ),
            FlightSegment(
                airline=airline2,
                flight_number=flight_number2,
                departure_airport=hub,
                arrival_airport=destination,
                departure_time=departure_time2,
                arrival_time=arrival_time2,
                duration=f"{duration2.seconds // 3600}h {(duration2.seconds % 3600) // 60}m",
                aircraft=random.choice(["Boeing 737", "Airbus A320"])
            )
        ]
        
        total_duration = arrival_time2 - departure_time1
        total_duration_str = f"{total_duration.seconds // 3600}h {(total_duration.seconds % 3600) // 60}m"
        
        # Connecting flights are usually cheaper
        base_price = random.randint(150, 600)
        multipliers = {
            CabinClass.ECONOMY: 1.0,
            CabinClass.PREMIUM_ECONOMY: 1.5,
            CabinClass.BUSINESS: 3.0,
            CabinClass.FIRST: 5.0
        }
        price = base_price * multipliers[cabin_class]
        
        return Flight(
            segments=segments,
            total_duration=total_duration_str,
            stops=1,
            price=round(price, 2),
            cabin_class=cabin_class,
            baggage_info=self._generate_baggage_info(cabin_class),
            is_refundable=cabin_class in [CabinClass.BUSINESS, CabinClass.FIRST]
        )
    
    async def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """Search for flights based on the request."""
        origin = self._resolve_airport(request.origin)
        destination = self._resolve_airport(request.destination)
        
        if not origin:
            raise ValueError(f"Unknown origin: {request.origin}")
        if not destination:
            raise ValueError(f"Unknown destination: {request.destination}")
        
        flights = []
        
        # Generate 3-8 flights
        num_flights = random.randint(3, 8)
        
        for i in range(num_flights):
            if request.direct_only:
                flight = self._generate_direct_flight(origin, destination, 
                                                    request.departure_date, request.cabin_class)
            else:
                # Mix of direct and connecting flights
                if random.random() > 0.4:  # 60% chance of direct flight
                    flight = self._generate_direct_flight(origin, destination,
                                                        request.departure_date, request.cabin_class)
                else:
                    flight = self._generate_connecting_flight(origin, destination,
                                                            request.departure_date, request.cabin_class)
            
            # Filter by max price if specified
            if request.max_price is None or flight.price <= request.max_price:
                flights.append(flight)
        
        # Sort by price
        flights.sort(key=lambda f: f.price)
        
        # Generate a unique search ID
        search_id = f"search_{random.randint(100000, 999999)}"
        
        return FlightSearchResponse(
            request=request,
            flights=flights,
            search_id=search_id,
            total_results=len(flights)
        )