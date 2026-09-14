export interface Location {
  longitude: number;
  latitude: number;
}
export interface Attraction {
  poi_id: string;
  name: string;
  address: string;
  location: Location;
  visit_duration: number;
  description: string;
  category: string;
  ticket_price: number;
  photos: string[];
}
export interface Hotel {
  poi_id: string;
  name: string;
  address: string;
  location: Location;
  type: string;
  estimated_cost: number;
}
export interface Meal {
  type: "breakfast" | "lunch" | "dinner";
  name: string;
  description: string;
  estimated_cost: number;
}
export interface DayPlan {
  date: string;
  day_index: number;
  description: string;
  transportation: string;
  accommodation: string;
  attractions: Attraction[];
  hotel: Hotel | null;
  meals: Meal[];
  transportation_cost: number;
}
export interface WeatherInfo {
  date: string;
  day_weather: string;
  night_weather: string;
  day_temp: number | null;
  night_temp: number | null;
  wind_direction: string;
  wind_power: string;
}
export interface Budget {
  total_attractions: number;
  total_hotels: number;
  total_meals: number;
  total_transportation: number;
  total: number;
  note: string;
}
export interface TripPlan {
  id: string;
  city: string;
  start_date: string;
  end_date: string;
  days: DayPlan[];
  weather_info: WeatherInfo[];
  overall_suggestions: string;
  budget: Budget;
  warnings: string[];
  source: string;
}
export interface TripFormData {
  city: string;
  start_date: string;
  end_date: string;
  travel_days: number;
  transportation: string;
  accommodation: string;
  preferences: string[];
  free_text_input: string;
}
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}
export interface PlanSummary {
  id: string;
  city: string;
  start_date: string;
  end_date: string;
  created_at: string;
}
export interface Session {
  id: string;
  title: string;
  updated_at: string;
}
export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}
export interface ChatReply {
  session_id: string;
  reply: string;
}
export interface RouteInfo {
  distance: number;
  duration: number;
  route_type: string;
  polyline: [number, number][];
}
export type PlanEvent =
  | { type: "progress"; message: string }
  | { type: "error"; message: string }
  | { type: "result"; data: TripPlan };
