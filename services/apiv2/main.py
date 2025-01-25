from fastapi import FastAPI
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
#from services.map_service import fetch_map_data

app = FastAPI()

class ComputeAvgResBody(BaseModel):
    response_locs: list[list[float]]

@app.get('/')
def test():
    return {'message': 'Hello World'}

@app.post('/avg-response-time')
async def compute_avg_res(
    body: ComputeAvgResBody
):
    em_locs: list[list[float]] = region_chunks()
    
    for loc in em_locs:
        total += compute_fastest_time_to_loc(loc, body.response_locs)
    
    compute_avg = total / len(em_locs) 
    
    return {'average': compute_avg}

def region_chunks():
    pass

def compute_fastest_time_to_loc(loc: list[float], response_ctrs: list[list[float]]):
    pass


@app.get("/map-data")
async def get_map_data(
    bbox: str = Query("...", description="Bounding box in 'min_lon,min_lat,max_lon,max_lat'")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str("An unexpected error occurred."))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


