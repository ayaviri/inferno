from fastapi import FastAPI
from fastapi import Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shapely.geometry import shape, Point
import json
import random
import requests
import numpy as np
import random
import math

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
    em_locs: list[list[float]] = region_chunks(50)
    total = 0

    for loc in em_locs:
        time = compute_fastest_time_to_loc(loc, body.response_locs)
        total += time if time > 0 else 0

    compute_avg = total / len(em_locs)

    return {"average": compute_avg}


def region_chunks(num_chunks: int):
    with open("denver.geojson", "r") as geojson_file:
        geojson_data = json.load(geojson_file)
        geom = shape(geojson_data["features"][0]["geometry"])

    random_coords = []

    for _ in range(num_chunks):
        minx, miny, maxx, maxy = geom.bounds
        lat = random.uniform(miny, maxy)
        lon = random.uniform(minx, maxx)
        random_coords.append([lon, lat])

    return random_coords


def compute_fastest_time_to_loc(loc: list[float], response_ctrs: list[list[float]]):
    response_times = list(
        filter(
            lambda x: x > 0, [compute_response_time(loc, ctr) for ctr in response_ctrs]
        )
    )

    if response_times:
        return min(response_times)
    else:
        return -1


def compute_response_time(loc: list[float], response_ctrs: list[float]):
    GRAPH_HOPPER_API_URL = (
        "http://localhost:8989/route"  # Replace with your GraphHopper instance URL
    )

    start_lon, start_lat = response_ctrs[0], response_ctrs[1]
    end_lon, end_lat = loc[0], loc[1]

    # Build the request payload for GraphHopper
    params = {
        "point": [f"{start_lat},{start_lon}", f"{end_lat},{end_lon}"],
        "profile": "car",
    }

    # Send the request to the GraphHopper instance
    response = requests.get(GRAPH_HOPPER_API_URL, params=params)

    if response.status_code != 200:
        print(response.text)
        return -1

    # Parse the response from GraphHopper
    gh_response = response.json()

    if "paths" not in gh_response or len(gh_response["paths"]) == 0:
        raise ValueError("No routes found")

    # Extract the best route (first path)
    best_route = gh_response["paths"][0]
    travel_time = best_route.get("time", 0) / 1000  # Convert ms to seconds

    return travel_time

@app.get("/optimal-config")
def optimal_config(n: int):
    center_loc: list[list[float]] = compute_optimal_config(n)
    return {"center_loc" : center_loc}

def compute_optimal_config(n: int):
    fire_locations = region_chunks(50)
    init_centroids = initialize_centroids(fire_locations, n)
    centroids = init_centroids
    
    for i in range(20):
        print(i)
        clusters = {i: [] for i in range(n)}
        for fire in fire_locations:
            route_times = []
            for centroid in centroids:
                response_time = compute_response_time(fire, centroid)
                if response_time > 0:
                    route_times += [response_time]
                else:
                    route_times += [999999999]
            closest_station = np.argmin(route_times)
            clusters[closest_station].append(fire)
            
        new_centroids = []
        for cluster_points in clusters.values():
            new_centroids.append(find_centroid(cluster_points))
        
        if stabilized(centroids, new_centroids):
            break
        centroids = new_centroids
        
    return centroids

def initialize_centroids(fire_loc: list[list[float]], n: int):
    return random.sample(fire_loc, n)

def find_centroid(cluster):
    lon_coords = [pt[0] for pt in cluster]
    lat_coords = [pt[1] for pt in cluster]
    mean_lon = np.mean(lon_coords)
    mean_lat = np.mean(lat_coords)
    
    return [mean_lon, mean_lat]

def stabilized(old: list[list[float]], new: list[list[float]]) -> bool:
    total_abs_dist = 0
    for old, new in zip(old, new):
        total_abs_dist = math.dist(old, new)
    return total_abs_dist < 0.001 


    

# def validate_and_snap_loc(location: list[float]):
#     GRAPH_HOPPER_API_URL = ("http://localhost:8989/route") # Q: this is passed as a tuple right? Also we should maybe globablize this
    
#     response = requests.get(GRAPH_HOPPER_API_URL, params = {
#         "point" : f"{location[0]},{location[1]}",
#         "point" : f"{location[0]},{location[1]}", #overwriting first point with same point to request one
#         "vehicle" : "car",
#         "locale" : "en",
#         "snap_prevention" : ["ferry", "tunnel", "bridge"] # Q /j: wtf is a "ford" lol
#     })
#     response.raise_for_status()
#     gh_response = response.json()
    
#     if "paths" in gh_response and len(gh_response["paths"]) > 0:
#         snapped_point = gh_response["paths"][0]["snapped_waypoints"]
#         return [snapped_point["lon"], snapped_point["lat"]]
#     else:
#         raise ValueError("No valid roads near the given location") # Q: is raising an error totally necessary?
    
#     # Q: will RequestException be necessary

# def optimize_response_ctrs (emergencies: list[list[float]], num_ctrs: int):
#     kmeans = KMeans(n_clusters = num_ctrs, random_state = 42).fit(emergencies)
#     centroids = kmeans.cluster_centers_
    
#     snapped_locs = []
#     for centroid in centroids:
#         snapped_location = validate_and_snap_loc(centroid)
#         snapped_locs.append(snapped_locs)
    
#     return snapped_locs

# def eval_ctr_config(emergencies: list[list[float]], response_centers: list[list[float]]):
#     total_response_time = 0
#     for emergency in emergencies:
#         min_time = min([compute_response_time(emergency, center) for center in response_centers])
#         total_response_time += min_time
    
#     avg_resp_time = total_response_time / len(emergencies)
#     return avg_resp_time

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
