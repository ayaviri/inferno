import redis
import requests

r = redis.Redis(host="localhost", port=6379, db=0)


def compute_and_persist_optimal_config(n: int):
    params = {"n": n}
    response = requests.get(
        "http://localhost:8000/optimal-config-offline", params=params
    )
    response.raise_for_status()
    data = response.json()
    r.set(str(n), str(data["center_locs"]))
