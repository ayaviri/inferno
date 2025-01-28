# inferno

inferno is a fire response simulator for the denver area. it currently supports:
- average response time simulation given a configuration of fire stations
- fastest response time simulation given a configuration of fire stations and a fire
- optimal configuration of n fire stations

## components
there is a web client built using HTML, CSS, and JS (with [leaflet.js](https://leafletjs.com) for map visualization), an API the web client communicates with built using Python and the FastAPI web framework, and a [GraphHopper](https://github.com/graphhopper/graphhopper) server as a routing engine. these are all self-hosted

## running locally
each directory under `services/` has a `dev.sh` script that props up the respective service

## deeper dive into the simulations

#### average response time simulation given a configuration of fire stations 
in order to calculate this, a large number of random fires were generated within the region (rectangular in shape to facilitate this). for each fire, the response time from each fire station in the configuration was calculated using GraphHopper. then, the average across all fires was taken

#### fastest response time simulation given a configuration of fire stations and a fire
GraphHopper was used to calculate the response time from each fire station to the given fire. the shortest time was returned

#### optimal configuration of n fire stations
a simple k-means clustering algorithm was used. a large number of fires are randomly generated in the same way as they are for the first simulation. n fire stations are they initialized at random fires. for each iteration of this algorithm, each fire is assigned to the fire station with the fastest response time. once every fire is assigned, the location of each fire station is updated to the centroid of its cluster. this is done until the locations stabilize

## caveats
not every square inch of the region serviced is near a road in the OSM data provided to GraphHopper. as such, some routes cannot be calculated. as of right now, these routes are ignored in various ways that likely deviate the final result from the actual result
