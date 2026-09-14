"""Deterministic validation and assembly. No model calls and no network access."""

from datetime import timedelta

from ..models.schemas import (
    Attraction, Budget, DayPlan, Hotel, PlanDraft, POIInfo, TripPlan, TripRequest, WeatherInfo,
)


def validate_draft(request: TripRequest, draft: PlanDraft,
                   attractions: list[POIInfo], hotels: list[POIInfo]) -> list[str]:
    errors = []
    expected_dates = [request.start_date + timedelta(days=i) for i in range(request.travel_days)]
    if [day.date for day in draft.days] != expected_dates:
        errors.append('行程日期必须按顺序完整覆盖请求的起止日期')
    attraction_ids = {item.id for item in attractions}
    hotel_ids = {item.id for item in hotels}
    for index, day in enumerate(draft.days):
        ids = [item.poi_id for item in day.attractions]
        if any(poi_id not in attraction_ids for poi_id in ids):
            errors.append(f'第 {index + 1} 天使用了候选列表以外的景点 ID')
        if len(ids) != len(set(ids)):
            errors.append(f'第 {index + 1} 天重复安排相同景点')
        if sum(item.visit_duration for item in day.attractions) > 600:
            errors.append(f'第 {index + 1} 天游览时间超过 10 小时')
        if sorted(meal.type for meal in day.meals) != ['breakfast', 'dinner', 'lunch']:
            errors.append(f'第 {index + 1} 天必须各包含一份早、中、晚餐')
        if day.hotel_id is not None and day.hotel_id not in hotel_ids:
            errors.append(f'第 {index + 1} 天使用了候选列表以外的酒店 ID')
        needs_hotel = index < request.travel_days - 1 and bool(hotels)
        if needs_hotel and day.hotel_id is None:
            errors.append(f'第 {index + 1} 天需要从候选列表选择住宿酒店')
    return errors


def assemble_plan(request: TripRequest, draft: PlanDraft, attractions: list[POIInfo],
                  hotels: list[POIInfo], weather: list[WeatherInfo], warnings: list[str]) -> TripPlan:
    points = {point.id: point for point in attractions}
    lodging = {point.id: point for point in hotels}
    days = []
    for index, day in enumerate(draft.days):
        selected = []
        for choice in day.attractions:
            point = points[choice.poi_id]
            selected.append(Attraction(
                poi_id=point.id, name=point.name, address=point.address, location=point.location,
                category=point.type, photos=point.photos, description=choice.description,
                visit_duration=choice.visit_duration, ticket_price=choice.ticket_price,
            ))
        hotel = None
        if day.hotel_id and index < request.travel_days - 1:
            point = lodging[day.hotel_id]
            hotel = Hotel(poi_id=point.id, name=point.name, address=point.address,
                          location=point.location, type=request.accommodation, estimated_cost=day.hotel_cost)
        days.append(DayPlan(
            date=day.date, day_index=index, description=day.description,
            transportation=request.transportation, accommodation=request.accommodation,
            attractions=selected, hotel=hotel, meals=day.meals,
            transportation_cost=day.transportation_cost,
        ))
    costs = {
        'total_attractions': sum(item.ticket_price for day in days for item in day.attractions),
        'total_hotels': sum(day.hotel.estimated_cost for day in days if day.hotel),
        'total_meals': sum(meal.estimated_cost for day in days for meal in day.meals),
        'total_transportation': sum(day.transportation_cost for day in days),
    }
    matching_weather = [item for item in weather if request.start_date <= item.date <= request.end_date]
    notices = list(warnings)
    if len({item.date for item in matching_weather}) < request.travel_days:
        notices.append('高德当前预报未覆盖全部旅行日期；未覆盖日期不生成天气，请临近出发时查询。')
    if not hotels and request.travel_days > 1:
        notices.append('未取得可用酒店信息，预算不含住宿，需自行确认。')
    notices.append('路线顺序由模型建议；出发前请通过地图核对实际交通、开放时间与预约要求。')
    return TripPlan(
        city=request.city, start_date=request.start_date, end_date=request.end_date, days=days,
        weather_info=matching_weather, overall_suggestions=draft.overall_suggestions,
        budget=Budget(**costs, total=sum(costs.values())), warnings=list(dict.fromkeys(notices)),
    )
