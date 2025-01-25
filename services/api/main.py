from fastapi import FastAPI
from fastapi import Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shapely.geometry import shape, Point
import json
import random
from ResponseTime import router, calculate_route
import requests

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

class ComputeAvgResBody(BaseModel):
    response_locs: list[list[float]]

@app.get("/")
def test():
    return {"message": "Hello World"}

@app.post("/avg-response-time")
def compute_avg_res(body: ComputeAvgResBody):
    em_locs: list[list[float]] = region_chunks()
    total = 0

    for loc in em_locs:
        time = compute_fastest_time_to_loc(loc, body.response_locs)
        total += time

    compute_avg = total / len(em_locs)

    return {"average": compute_avg}

def region_chunks():
    # convention for project - lon, lat
    with open("denver.geojson", "r") as geojson_file:
        geojson_data = json.load(geojson_file)

    random_coords = []

    for feature in geojson_data["features"]:
        geom = shape(feature["geometry"])
        minx, miny, maxx, maxy = geom.bounds
        n = 2
        feature_coords = []

        while len(feature_coords) < n:
            lat = random.uniform(miny, maxy)
            lon = random.uniform(minx, maxx)
            point = Point(lon, lat)
            if geom.contains(point):
                feature_coords.append([lon, lat])

        random_coords.extend(feature_coords)
    return random_coords

def compute_fastest_time_to_loc(loc: list[float], response_ctrs: list[list[float]]):
    return min([compute_response_time(loc, ctr) for ctr in response_ctrs])

def compute_response_time(loc: list[float], response_ctrs: list[float]):
    
    GRAPH_HOPPER_API_URL = (
    "http://localhost:8989/route"  # Replace with your GraphHopper instance URL
)
    
    start_lon, start_lat = response_ctrs[0], response_ctrs[1]
    end_lon, end_lat = loc[0], loc[1]

    # Build the request payload for GraphHopper
    params = {
        "point": [f"{start_lat},{start_lon}", f"{end_lat},{end_lon}"],
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

    return travel_time

@app.get("/map-data")
async def get_map_data(
    bbox: str = Query(
        "...", description="Bounding box in 'min_lon,min_lat,max_lon,max_lat'"
    ),
):
    """
    Takes Bounding box as input for region (i.e. Denver)
    Returns Map Data
    """

    try:
        map_data = fetch_map_data(bbox)
        return JSONResponse(content=map_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data not found: {e}")
    except Exception:
        raise HTTPException(
            status_code=500, detail=str("An unexpected error occurred.")
        )
