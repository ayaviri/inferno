from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import requests

router = APIRouter()

GRAPH_HOPPER_API_URL = (
    "http://localhost:8989/route"  # Replace with your GraphHopper instance URL
)


@router.get("/calculate-route")
async def calculate_route(
    start_lat: float = Query(..., description="Starting latitude"),
    start_lon: float = Query(..., description="Starting longitude"),
    end_lat: float = Query(..., description="Ending latitude"),
    end_lon: float = Query(..., description="Ending longitude"),
    vehicle: str = Query("car", description="Vehicle type, e.g., car, bike, foot"),
    weighting: str = Query(
        "fastest", description="Weighting type, e.g., fastest, shortest"
    ),
    locale: str = Query("en", description="Language for response, e.g., en, de"),
):
    """
    Calculate the fastest route between two points using GraphHopper.
    """
    try:
        # Build the request payload for GraphHopper
        params = {
            "point": [f"{start_lat},{start_lon}", f"{end_lat},{end_lon}"],
            "vehicle": vehicle,
            "weighting": weighting,
            "locale": locale,
        }

        # Send the request to the GraphHopper instance
        response = requests.get(GRAPH_HOPPER_API_URL, params=params)
        response.raise_for_status()

        # Parse the response from GraphHopper
        gh_response = response.json()

        if "paths" not in gh_response or len(gh_response["paths"]) == 0:
            raise ValueError("No routes found")

        # Extract the best route (first path)
        best_route = gh_response["paths"][0]
        travel_time = best_route.get("time", 0) / 1000  # Convert ms to seconds
        distance = best_route.get("distance", 0) / 1000  # Convert meters to kilometers

        return JSONResponse(
            content={
                "start": {"lat": start_lat, "lon": start_lon},
                "end": {"lat": end_lat, "lon": end_lon},
                "travel_time_sec": travel_time,
                "distance_km": distance,
                "details": best_route,
            }
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Error connecting to GraphHopper: {e}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )
