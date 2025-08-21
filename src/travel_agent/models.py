from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CabinClass(str, Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class FlightType(str, Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class BagageType(str, Enum):
    CARRY_ON = "carry_on"
    CHECKED = "checked"


class ConversationState(str, Enum):
    INITIAL = "initial"
    COLLECTING_PREFERENCES = "collecting_preferences"
    SHOWING_RESULTS = "showing_results"
    COLLECTING_PASSENGER_INFO = "collecting_passenger_info"
    CONFIRMING_BOOKING = "confirming_booking"
    COMPLETED = "completed"


class Airport(BaseModel):
    code: str = Field(..., description="3-letter IATA airport code")
    name: str = Field(..., description="Full airport name")
    city: str = Field(..., description="City name")
    country: str = Field(default="US", description="Country code")


class BaggageInfo(BaseModel):
    type: BagageType
    included: bool = Field(..., description="Whether included in ticket price")
    fee: Optional[float] = Field(None, description="Additional fee if not included")
    weight_limit: Optional[str] = Field(None, description="Weight or size limit")


class FlightSegment(BaseModel):
    airline: str
    flight_number: str
    departure_airport: Airport
    arrival_airport: Airport
    departure_time: datetime
    arrival_time: datetime
    duration: str = Field(..., description="Flight duration in format like '2h 30m'")
    aircraft: Optional[str] = None


class Flight(BaseModel):
    segments: List[FlightSegment]
    total_duration: str
    stops: int = Field(..., description="Number of stops (0 for direct)")
    price: float
    cabin_class: CabinClass
    baggage_info: List[BaggageInfo]
    is_refundable: bool = False
    
    @property
    def is_direct(self) -> bool:
        return self.stops == 0
    
    @property
    def origin(self) -> Airport:
        return self.segments[0].departure_airport
    
    @property
    def destination(self) -> Airport:
        return self.segments[-1].arrival_airport


class FlightSearchRequest(BaseModel):
    origin: str = Field(..., description="Origin airport code or city name")
    destination: str = Field(..., description="Destination airport code or city name")
    departure_date: date
    return_date: Optional[date] = None
    adults: int = Field(default=1, ge=1, le=9)
    cabin_class: CabinClass = CabinClass.ECONOMY
    flight_type: FlightType = FlightType.ONE_WAY
    direct_only: bool = False
    max_price: Optional[float] = None


class FlightSearchResponse(BaseModel):
    request: FlightSearchRequest
    flights: List[Flight]
    search_id: str = Field(..., description="Unique ID for this search")
    total_results: int


class PassengerInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    email: str
    phone: str
    gender: Optional[str] = None
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class BookingRequest(BaseModel):
    search_id: str
    selected_flight_index: int
    passengers: List[PassengerInfo]
    contact_email: str
    contact_phone: str


class BookingResponse(BaseModel):
    booking_reference: str
    total_price: float
    status: str = "confirmed"
    flight: Flight
    passengers: List[PassengerInfo]
    booking_date: datetime = Field(default_factory=datetime.now)


class UserMessage(BaseModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentMessage(BaseModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    requires_input: bool = False
    suggested_responses: Optional[List[str]] = None


class ConversationSession(BaseModel):
    session_id: str
    state: ConversationState = ConversationState.INITIAL
    current_search: Optional[FlightSearchRequest] = None
    last_search_results: Optional[FlightSearchResponse] = None
    selected_flight: Optional[Flight] = None
    passengers: List[PassengerInfo] = []
    context: Dict[str, Any] = Field(default_factory=dict)
    messages: List[UserMessage | AgentMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    state: ConversationState
    requires_input: bool = False
    suggested_responses: Optional[List[str]] = None
    flight_results: Optional[List[Flight]] = None