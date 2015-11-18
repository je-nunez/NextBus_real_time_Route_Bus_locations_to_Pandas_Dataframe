# NextBus real-time Route Vehicle Locations to a Python Pandas Dataframe

Similar to the R version in another project about NextBus Vehicle Locations

Requires Python `Pandas`, `Matplotlib`, and `Basemap` from `mpl_toolkits`

# WIP

This project is a *work in progress*. The implementation is *incomplete* and
subject to change. The documentation can be inaccurate.

# Examples of maps of real-time locations of transit vehicles

The current way of calling the script is:

     ./plot_dataframe_nextbus_vehicle_locations.py  [-i contain_geom] [-m maptype] agency-code  route-code


where `agency-code` is the transit agency code in the NextBus system (some examples below), the `route-code` the route in the NextBus system, the optional `-i contain_geom` is the containing geometry only inside which to draw the vehicles whose real-time location is of interest of this route (the `contain_geom` is an OGC `WKT` string in the WSG84 coordinate system with longitudes first and latitudes later -longit, latitude-), and `-m maptype` is the desired underlying Google Map background (`maptype` is one of the values `roadmap`, `mobile`, `satellite`, `terrain`, `hybrid`, `mapmaker-roadmap`, or `mapmaker-hybrid`).

*Note* that the `route-code` is exact, e.g., for the example of the `Los Angeles Metro`, the route `20` refers only to route `20` and not to other colinear routes in a similar path, like routes `720`.

For the map with the real-time locations of the vehicles servicing `San Francisco Municipal Transportation Agency - Route 38 Geary Blvd` only inside in the area (polygon) around Geary Blvd and Divisadero St, with a `hybrid` background:

     ./plot_dataframe_nextbus_vehicle_locations.py \
           -i 'POLYGON((-122.458 37.76, -122.42 37.76, -122.42 37.82, -122.458 37.82, -122.458 37.76))' \
           -m hybrid \
        sf-muni  38

A sample is below:

![San Francisco Municipal Transportation Agency - Route 38 Geary Blvd](/nextbus_vehicle_locations_gmaps_sf_muni_38.png?raw=true "San Francisco Municipal Transportation Agency - Route 38 Geary Blvd")

For the map with the real-time locations of the vehicles servicing `Toronto Transit Commission - Route 39 Finch Ave East` only inside in the area (polygon) around Finch station:

     ./plot_dataframe_nextbus_vehicle_locations.py \
         -i 'POLYGON((-79.446 43.780, -79.386 43.780, -79.386 43.789, -79.446 43.789, -79.446 43.780))' \
         -m hybrid \
       ttc  39

A sample is below:

![Toronto Transit Commission - Route 39 Finch Ave East](/nextbus_vehicle_locations_gmaps_ttc_39.png?raw=true "Toronto Transit Commission - Route 39 Finch Ave East")

For the map with the real-time locations of the vehicles servicing `Los Angeles Metro, Route 20, Downtown LA - Santa Monica via Wilshire Blvd`:

     ./plot_dataframe_nextbus_vehicle_locations.py  lametro  20

A sample is below:

![Los Angeles Metro, Route 20, Downtown LA - Santa Monica via Wilshire Blvd](/nextbus_vehicle_locations_gmaps_lametro_20.png?raw=true "Los Angeles Metro Route 20, Downtown LA - Santa Monica via Wilshire Blvd")

For the map with the real-time locations of the vehicles servicing `New York City Metropolitan Transportation Authority - Bronx Bx12 Broadway Inwood - Bay Plaza`:

     ./plot_dataframe_nextbus_vehicle_locations.py  bronx  BX12

A sample is below:

![New York City Metropolitan Transportation Authority - Bronx Route Bx12 Broadway Inwood - Bay Plaza](/nextbus_vehicle_locations_gmaps_bronx_BX12.png?raw=true "New York City Metropolitan Transportation Authority - Bronx Bx12 Broadway Inwood - Bay Plaza")

