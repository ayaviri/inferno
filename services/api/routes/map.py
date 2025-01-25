from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
# import fetch_map_data function from 

router = APIRouter()

@router.get("/map-data")
async def get_map_data(
    bound_box: str = Query(None, description="Bounding box in 'min_lon,min_lat,max_lon,max_lat'")
):
    try:
        map_data = fetch_map_data(bound_box)
        return JSONResponse(content=map_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str("An unexpected error occurred."))