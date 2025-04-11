from mcp.server.fastmcp import FastMCP
import random
import requests
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv()
mcp = FastMCP("Bing Search and Travel", instructions="Output in Markdown format")

@mcp.tool()
def bing_search(query: str, count: int = 5) -> str:
    """Search the web using Bing Search API"""
    api_key = os.environ.get("BING_SEARCH_API_KEY")
    if not api_key:
        raise ValueError("BING_SEARCH_API_KEY environment variable is not set")
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": count, "responseFilter": "Webpages"}
    
    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        
        results = []
        if "webPages" in search_results and "value" in search_results["webPages"]:
            for result in search_results["webPages"]["value"]:
                results.append(f"Title: {result['name']}\nURL: {result['url']}\nSnippet: {result['snippet']}\n")
        
        return "\n".join(results) if results else "No results found"
    except Exception as e:
        return f"Search error: {str(e)}"

@mcp.tool()
def get_travel_time(origin: str, destination: str, mode: str = "car") -> str:
    """Calculate travel time between two places using Azure Maps"""
    subscription_key = os.environ.get("AZURE_MAPS_API_KEY")
    if not subscription_key:
        raise ValueError("AZURE_MAPS_API_KEY environment variable is not set")
    
    try:
        search_url = "https://atlas.microsoft.com/search/address/json"
        search_params = {
            "api-version": "1.0",
            "subscription-key": subscription_key,
            "query": origin
        }
        response = requests.get(search_url, params=search_params)
        response.raise_for_status()
        origin_data = response.json()
        if not origin_data.get("results"):
            return f"Could not find location: {origin}"
        origin_point = origin_data['results'][0]['position']
        
        search_params["query"] = destination
        response = requests.get(search_url, params=search_params)
        response.raise_for_status()
        dest_data = response.json()
        if not dest_data.get("results"):
            return f"Could not find location: {destination}"
        dest_point = dest_data['results'][0]['position']
        
        route_url = "https://atlas.microsoft.com/route/directions/json"
        route_params = {
            "api-version": "1.0",
            "subscription-key": subscription_key,
            "query": f"{origin_point['lat']},{origin_point['lon']}:{dest_point['lat']},{dest_point['lon']}",
            "travelMode": mode
        }
        
        response = requests.get(route_url, params=route_params)
        response.raise_for_status()
        route_data = response.json()
        
        if "routes" in route_data and route_data["routes"]:
            route = route_data["routes"][0]
            duration_seconds = route["summary"]["travelTimeInSeconds"]
            distance_km = route["summary"]["lengthInMeters"] / 1000
            
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            time_str = ""
            if hours > 0:
                time_str += f"{int(hours)} hour{'s' if hours > 1 else ''} "
            time_str += f"{int(minutes)} minute{'s' if minutes > 1 else ''}"
            
            return f"Travel from {origin} to {destination} by {mode}: {time_str} ({distance_km:.1f} km)"
        else:
            return "No route found."
    except Exception as e:
        return f"Error calculating travel time: {str(e)}"

@mcp.tool()
def find_hotels(address: str, radius_km: float = 2.0, limit: int = 5) -> str:
    """Find hotels near a specified address"""
    subscription_key = os.environ.get("AZURE_MAPS_API_KEY")
    if not subscription_key:
        raise ValueError("AZURE_MAPS_API_KEY environment variable is not set")
    
    try:
        search_url = "https://atlas.microsoft.com/search/address/json"
        search_params = {
            "api-version": "1.0",
            "subscription-key": subscription_key,
            "query": address
        }
        response = requests.get(search_url, params=search_params)
        response.raise_for_status()
        location_data = response.json()
        
        if not location_data.get("results"):
            return f"Could not find location: {address}"
            
        location = location_data['results'][0]['position']
        lat, lon = location['lat'], location['lon']
        
        poi_url = "https://atlas.microsoft.com/search/poi/json"
        poi_params = {
            "api-version": "1.0",
            "subscription-key": subscription_key,
            "query": "hotel",
            "lat": lat,
            "lon": lon,
            "radius": int(radius_km * 1000),
            "limit": limit
        }
        
        response = requests.get(poi_url, params=poi_params)
        response.raise_for_status()
        hotel_data = response.json()
        
        results = []
        if "results" in hotel_data and hotel_data["results"]:
            for hotel in hotel_data["results"]:
                name = hotel.get("poi", {}).get("name", "Unknown Hotel")
                address_text = hotel.get("address", {}).get("freeformAddress", "Address unknown")
                distance = hotel.get("dist", 0) / 1000  # Convert meters to km
                
                results.append(f"🏨 {name}\nAddress: {address_text}\nDistance: {distance:.2f} km")
        
        if results:
            return f"Found {len(results)} hotels near {address}:\n\n" + "\n\n".join(results)
        else:
            return f"No hotels found within {radius_km} km of {address}"
    
    except Exception as e:
        return f"Error searching for hotels: {str(e)}"
