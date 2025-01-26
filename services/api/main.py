from fastapi import FastAPI
from fastapi import Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shapely.geometry import shape, Point
import redis
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


@app.on_event("startup")
def startup():
    global r
    r = redis.Redis(host="localhost", port=6379, db=0)


class SimulateSingleRequestBody(BaseModel):
    fire_loc: list[float]
    response_locs: list[list[float]]


@app.post("/simulate-single")
def simulate_single_fire(body: SimulateSingleRequestBody):
    response_time = compute_fastest_time_to_loc(body.fire_loc, body.response_locs)
    return {"response_time": response_time}


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
    byte_data = r.get(str(n))
    center_locs = convert_to_coordinate_pairs(byte_data)
    return {"center_locs": center_locs}


def convert_to_coordinate_pairs(byte_data: bytes):
    coordinates = json.loads(byte_data.decode("utf-8"))
    return [list(map(float, pair)) for pair in coordinates]


@app.get("/optimal-config-offline")
def optimal_config_offline(n: int):
    center_locs: list[list[float]] = compute_optimal_config(n)
    return {"center_locs": center_locs}


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
