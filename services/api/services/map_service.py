def validate_bbox(bound_box: str) -> tuple:
    coords = bound_box.split(",")
    if len(coords) != 4:
        raise ValueError("Bounding must have 4 values: min_lon, min_lat, max_lon, max_lat")

