"""Public data contract. Facts come from tools; estimated costs are explicitly marked."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TripRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    city: str = Field(min_length=1, max_length=60)
    start_date: date
    end_date: date
    travel_days: int = Field(ge=1, le=30)
    transportation: Literal['公共交通', '自驾', '步行', '混合'] = '公共交通'
    accommodation: str = Field(default='经济型酒店', min_length=1, max_length=40)
    preferences: list[str] = Field(default_factory=list, max_length=6)
    free_text_input: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def check_dates(self):
        if (self.end_date - self.start_date).days + 1 != self.travel_days:
            raise ValueError('日期范围必须与旅行天数一致，结束日期不得早于开始日期')
        if any(len(item) > 40 for item in self.preferences):
            raise ValueError('每个偏好标签最多 40 个字符')
        return self


class Location(BaseModel):  # 被amap_http返回的POI对象使用检查，检查位置信息是否合法
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)


class POIInfo(BaseModel):
    id: str
    name: str
    address: str = ''
    location: Location
    type: str = ''
    photos: list[str] = Field(default_factory=list)


class WeatherInfo(BaseModel):
    date: date
    day_weather: str
    night_weather: str
    day_temp: int | None = None
    night_temp: int | None = None
    wind_direction: str = ''
    wind_power: str = ''


class Attraction(BaseModel):
    poi_id: str
    name: str
    address: str
    location: Location
    visit_duration: int = Field(ge=15, le=480)
    description: str
    category: str = '景点'
    ticket_price: int = Field(ge=0)
    price_is_estimate: bool = True
    photos: list[str] = Field(default_factory=list)


class Meal(BaseModel):
    type: Literal['breakfast', 'lunch', 'dinner']
    name: str
    description: str = ''
    estimated_cost: int = Field(ge=0)


class Hotel(BaseModel):
    poi_id: str
    name: str
    address: str
    location: Location
    type: str
    estimated_cost: int = Field(ge=0)


class DayPlan(BaseModel):
    date: date
    day_index: int
    description: str
    transportation: str
    accommodation: str
    attractions: list[Attraction]
    hotel: Hotel | None = None
    meals: list[Meal]
    transportation_cost: int = Field(default=0, ge=0)


class Budget(BaseModel):
    total_attractions: int
    total_hotels: int
    total_meals: int
    total_transportation: int
    total: int
    note: str = '所有费用为规划估算，并非实时报价；住宿按旅行天数减一晚计算。'


class TripPlan(BaseModel):
    id: UUID | None = None
    city: str
    start_date: date
    end_date: date
    days: list[DayPlan]
    weather_info: list[WeatherInfo]
    overall_suggestions: str
    budget: Budget
    warnings: list[str] = Field(default_factory=list)
    source: str = '高德地图工具查询；安排及费用由 AI 估算'


class TripPlanResponse(BaseModel):
    success: bool = True
    message: str = '旅行计划生成成功'
    data: TripPlan


# The LLM selects IDs and estimates; it cannot supply authoritative coordinates.
class AttractionChoice(BaseModel):
    poi_id: str = Field(description='必须是候选景点中存在的 id')
    visit_duration: int = Field(ge=15, le=480)
    description: str
    ticket_price: int = Field(ge=0, le=10000, description='估算门票费用，元')


class DraftDay(BaseModel):
    date: date
    description: str
    attractions: list[AttractionChoice] = Field(min_length=1, max_length=4)
    hotel_id: str | None = Field(description='候选酒店 id；最后一天或没有候选时填 null')
    hotel_cost: int = Field(ge=0, le=50000)
    meals: list[Meal] = Field(min_length=3, max_length=3)
    transportation_cost: int = Field(ge=0, le=10000)


class PlanDraft(BaseModel):
    days: list[DraftDay] = Field(min_length=1, max_length=30)
    overall_suggestions: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: UUID | None = None


class RouteRequest(BaseModel):
    origin: Location
    destination: Location
    city: str = Field(min_length=1, max_length=60)
    route_type: Literal['walking', 'driving', 'transit'] = 'walking'


class RevisionRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=2000)
