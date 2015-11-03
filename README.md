# NextBus real-time Route Vehicle Locations to a Python Pandas Dataframe

Similar to the R version in another project about NextBus Vehicle Locations

Requires Python `Pandas`, `Matplotlib`, and `Basemap` from `mpl_toolkits`

# WIP

This project is a *work in progress*. The implementation is *incomplete* and
subject to change. The documentation can be inaccurate.

# Examples:

The current way of calling the script is:

     ./plot_dataframe_nextbus_vehicle_locations.py  agency-code   route-code

where `agency-code` is the transit agency code in the NextBus system (some examples below), and the `route-code` the route in the NextBus system. Note that the `route-code` is exact, e.g., for the example of the `Los Angeles Metro`, the route `20` refers only to route `20` and not to other colinear routes in a similar path, like routes `720`.

For the vehicle locations of the `Los Angeles Metro, Route 20, Downtown LA - Santa Monica via Wilshire Blvd`:

     ./plot_dataframe_nextbus_vehicle_locations.py  lametro  20

![Los Angeles Metro, Route 20, Downtown LA - Santa Monica via Wilshire Blvd](/nextbus_vehicle_locations_gmaps_lametro_20.png?raw=true "Los Angeles Metro Route 20, Downtown LA - Santa Monica via Wilshire Blvd")

For the vehicle locations of the `New York City Metropolitan Transportation Authority - Bronx Bx12 Broadway Inwood - Bay Plaza`:

     ./plot_dataframe_nextbus_vehicle_locations.py  bronx  BX12

![New York City Metropolitan Transportation Authority - Bronx Route Bx12 Broadway Inwood - Bay Plaza](/nextbus_vehicle_locations_gmaps_bronx_BX12.png?raw=true "New York City Metropolitan Transportation Authority - Bronx Bx12 Broadway Inwood - Bay Plaza")

For the vehicle locations of the `Toronto Transit Commission - Route 39 Finch Ave East`:

     ./plot_dataframe_nextbus_vehicle_locations.py  ttc  39

![Toronto Transit Commission - Route 39 Finch Ave East](/nextbus_vehicle_locations_gmaps_ttc_39.png?raw=true "Toronto Transit Commission - Route 39 Finch Ave East")

For the vehicle locations of the `San Francisco Municipal Transportation Agency - Route 38 Geary Blvd`:

     ./plot_dataframe_nextbus_vehicle_locations.py  sf-muni  38

![San Francisco Municipal Transportation Agency - Route 38 Geary Blvd](/nextbus_vehicle_locations_gmaps_sf_muni_38.png?raw=true "San Francisco Municipal Transportation Agency - Route 38 Geary Blvd")

