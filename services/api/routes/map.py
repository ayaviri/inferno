from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
# import fetch_map_data function from 

router = APIRouter()

@router.get("/map-data")
async def get_map_data(
    region: str = Query(None, description="Region name, in this case Denver"),
    bound_box: str = Query(None, description="Bounding box in 'min_lon,min_lat,max_lon,max_lat'")
):
    if not region and not bound_box:
        raise HTTPException(
            status_code=400,
            detail="Requires 'region' or 'bound_box' parameter" )
    
    try:
        map_data = fetch_map_data(region, bound_box)
        return JSONResponse(content=map_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))