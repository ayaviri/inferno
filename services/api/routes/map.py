from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from services.map_service import fetch_map_data

router = APIRouter()

@router.get("/map-data")
async def get_map_data(
    bound_box: str = Query(None, description="Bounding box in 'min_lon,min_lat,max_lon,max_lat'")
):
    """
    Takes Bounding box as input for region (i.e. Denver)
    Returns Map Data
    """
    try:
        map_data = fetch_map_data(bound_box)
        return JSONResponse(content=map_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str("An unexpected error occurred."))


