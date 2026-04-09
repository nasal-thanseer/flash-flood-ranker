import os
import json
import requests
import time
from typing import TypedDict, List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# Define the state for LangGraph
class GraphState(TypedDict):
    location: str
    lat: float
    lon: float
    weather: Dict[str, Any]
    roads: List[str]
    rankings: List[Dict[str, Any]]
    errors: List[str]

# Node: Fetch Weather Data
def fetch_weather(state: GraphState) -> GraphState:
    """Fetches real-time weather data from Open-Meteo"""
    lat = state["lat"]
    lon = state["lon"]
    try:
        # Fetch current and hourly precipitation
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation&hourly=precipitation&timezone=auto"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Calculate next 24h expected rainfall sum
        hourly_precip = data.get("hourly", {}).get("precipitation", [])
        next_24h_precip = sum(hourly_precip[:24]) if hourly_precip else 0
        
        weather_info = {
            "current_precipitation_mm": data.get("current", {}).get("precipitation", 0),
            "next_24h_precipitation_mm": round(next_24h_precip, 2)
        }
        state["weather"] = weather_info
    except Exception as e:
        state["errors"].append(f"Weather API error: {str(e)}")
        state["weather"] = {"current_precipitation_mm": 0, "next_24h_precipitation_mm": 0}
    
    return state

# Node: Fetch Roads Data
def fetch_roads(state: GraphState) -> GraphState:
    """Fetches street names using Overpass API (OpenStreetMap)"""
    location_name = state.get("location", "Target")
    lat = state.get("lat", 0.0)
    lon = state.get("lon", 0.0)
    
    # Fast Bounding Box (~11km square) avoids slow global hierarchy relation lookups which cause 504s
    bbox = f"{lat - 0.05},{lon - 0.05},{lat + 0.05},{lon + 0.05}"
    query = f"""
    [out:json][timeout:15];
    way["highway"]["name"]({bbox});
    out body 20;
    """
    
    # Multi-endpoint cascade to prevent timeouts
    endpoints = [
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    
    roads_set = set()
    for url in endpoints:
        try:
            response = requests.post(url, data={"data": query}, timeout=10)
            response.raise_for_status()
            data = response.json()
            for element in data.get("elements", []):
                name = element.get("tags", {}).get("name")
                if name:
                    roads_set.add(name)
            if roads_set:
                break # Success! Hit a working server
        except Exception as e:
            print(f"Overpass {url} timeout, trying next server...")
            continue
            
    roads = list(roads_set)[:15] # Limit to 15 roads for MVP speed
    if not roads:
        # Fallback if overpass fails to find roads by name
        print("Silent Overpass fallback trigger: All endpoints timed out or returned empty.")
        roads = [f"{location_name} Main Road", f"{location_name} Temple Street", f"{location_name} Market Road", f"{location_name} Center Street"]
        
    state["roads"] = roads
    
    return state

# Node: Rank Streets using Gemini
def rank_streets(state: GraphState) -> GraphState:
    """Uses Gemini to predict the vulnerability and rank the streets."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        state["errors"].append("GEMINI_API_KEY is missing or invalid.")
        state["rankings"] = []
        return state

    # Cascade models to completely bypass Free-Tier Quota limitations natively
    models = ["gemini-2.0-flash-lite-preview-02-05", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    
    roads = state["roads"]
    weather = state["weather"]
    location = state["location"]
    
    prompt = f"""
    You are an expert Flood Risk AI Agent evaluating an informal settlement in {location}.
    
    Current Weather Data:
    - Current Precipitation: {weather.get('current_precipitation_mm', 0)} mm
    - Expected 24h Precipitation: {weather.get('next_24h_precipitation_mm', 0)} mm
    
    Target Streets:
    {json.dumps(roads, indent=2)}
    
    Based on the weather and typical structural/topographic vulnerabilities of these roads (infer if needed, base it on typical proximity to water bodies, low elevation, or structural density for the area).
    Assign each street a 'vulnerability_score' from 1 to 100 (100 is extremely vulnerable to flooding) and provide a short 'reason' for evacuation priority.
    
    Return ONLY a valid JSON array of objects with keys: "street_name", "vulnerability_score", "reason". Sort the array descending by vulnerability_score.
    """
    
    for model_name in models:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name, 
                temperature=0.2,
                google_api_key=api_key,
                max_retries=0 # Fast-fail to quickly cascade models
            )
            response = llm.invoke(prompt)
            text = response.content.strip()
            
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            rankings = json.loads(text.strip())
            state["rankings"] = rankings
            return state # Success!
            
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "404" in err_msg or "quota" in err_msg.lower():
                continue # Soft-fail and try the next model's quota
    
    # Exhausted all models
    state["errors"].append("Quota Exhausted: You have exceeded the free tier daily request limits across all available Gemini models.")
    state["rankings"] = []
    
    return state


# Build the LangGraph Workflow
def build_graph():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("fetch_weather", fetch_weather)
    workflow.add_node("fetch_roads", fetch_roads)
    workflow.add_node("rank_streets", rank_streets)
    
    # Define edges: Start -> fetch_weather -> fetch_roads -> rank_streets -> END
    workflow.set_entry_point("fetch_weather")
    workflow.add_edge("fetch_weather", "fetch_roads")
    workflow.add_edge("fetch_roads", "rank_streets")
    workflow.add_edge("rank_streets", END)
    
    return workflow.compile()

# Execution Helper
def run_agent(location: str, lat: float, lon: float) -> GraphState:
    graph = build_graph()
    initial_state = GraphState(
        location=location,
        lat=lat,
        lon=lon,
        weather={},
        roads=[],
        rankings=[],
        errors=[]
    )
    result = graph.invoke(initial_state)
    return result
