#!/usr/bin/env python2

"""
Retrieves a NextBus Vehicle Locations Feed for a route into a Panda Data frame
"""

import sys
import time
import urllib2
import numpy as np
import pandas as pd
from pandas import DataFrame
import shapely.wkt
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
# from matplotlib.patches import Polygon, Circle


def dataframe_nextbus_bus_location(agency, route,
                                   time_window_location_change=30 * 60):
    # pylint: disable=line-too-long
    """Retrieves the data from NextBus Vehicle Locations XML API, at

       http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=<agency_tag>&r=<route tag>&t=<epoch time in msec>

    parses the XML, and returns a Panda Data frame with the information."""

    import xml.etree.ElementTree as ET

    nextbus_vehicle_locations_fmt = ("http://webservices.nextbus.com/"
                                     "service/publicXMLFeed?"
                                     "command=vehicleLocations"
                                     "&a={}&r={}&t={}000")

    # from what start-time to request NextBus for the change in the
    # locations of the vehicles servicing this transit route
    # now_epoch = int(time.time())
    start_time = int(time.time()) - time_window_location_change

    # Get the changes in vehicle locations since the last 15 minutes
    url_nextbus_feed = nextbus_vehicle_locations_fmt.format(agency, route,
                                                            start_time)

    sys.stderr.write("DEBUG: NextBus Vehicles: {}\n".format(url_nextbus_feed))
    nextbus_vehicle_location = urllib2.urlopen(url_nextbus_feed).read()
    # sys.stderr.write("DEBUG: read: {}\n".format(nextbus_vehicle_location))

    xml_doc_root = ET.fromstring(nextbus_vehicle_location)

    # A cleaner conversion from NextBus Vehicle Locations to Panda Dataframe
    # is necessary -note that NextBus uses the Java Camel Style notations for
    # its symbols.
    dataframe_columns = ["id", "lon", "lat", "secsSinceReport", "routeTag",
                         "dirTag", "heading", "speedKmHr"]
    dataframe_records = []

    for xml_elem in xml_doc_root:
        elem_list = listify_nextbus_xml_elem(xml_elem)

        if elem_list:
            # the XML element could be parsed: then append this record to the
            # list of records
            dataframe_records.append(elem_list)

    # Create the Panda DataFrame from the NextBus Vehicle Locations
    vehicle_locations_df = DataFrame.from_records(data=dataframe_records,
                                                  columns=dataframe_columns)
    return vehicle_locations_df


def listify_nextbus_xml_elem(xml_elem):
    """Converts a XML Element containing a NextBus Vehicle Location to a
    Python list whose elements are the attributes of that NextBus Vehicle
    Location XML Element."""

    # vehicle {'lon': '-122.3925', 'secsSinceReport': '23', 'id': '6290',
    #          'routeTag': '38R', 'predictable': 'true', 'speedKmHr': '0',
    #          'lat': '37.78986', 'dirTag': '38R__O_F00', 'heading': '218'}
    if xml_elem.tag != 'vehicle':
        sys.stderr.write("WARN: ignoring {}\n".format(str(xml_elem)))
        return None

    return_list = []

    vehicle_id = xml_elem.get('id', default="UNKNOWN")
    return_list.append(vehicle_id)

    vehicle_longitude = get_float_from_xml_elem(xml_elem, 'lon')
    return_list.append(vehicle_longitude)

    vehicle_latitude = get_float_from_xml_elem(xml_elem, 'lat')
    return_list.append(vehicle_latitude)

    vehicle_last_updated = get_float_from_xml_elem(xml_elem, 'secsSinceReport')
    return_list.append(vehicle_last_updated)

    route_tag = xml_elem.get('routeTag', default="UNKNOWN")
    return_list.append(route_tag)

    dir_tag = xml_elem.get('dirTag', "UNKNOWN")
    return_list.append(dir_tag)

    heading = xml_elem.get('heading', "UNKNOWN")
    return_list.append(heading)

    vehicle_speed = get_float_from_xml_elem(xml_elem, 'speedKmHr')
    return_list.append(vehicle_speed)

    return return_list


def get_float_from_xml_elem(xml_elem, xml_attrib, default_val=np.nan):
    """Returns the value of the attribute 'xml_attrib', which is expected
    to be a float, from the XML element 'xml_elem'."""

    value = default_val
    if xml_attrib in xml_elem.attrib:
        try:
            value = float(xml_elem.attrib[xml_attrib])
        except ValueError as dummy_ignored_exc:
            pass
    return value


def render_nextbus_dataframe(route, nextbus_df):
    """Plots the NextBus Vehicle Location's Panda Data frame to a
    Matplotlib and Basemap Geospatial image."""

    min_long = min(nextbus_df.lon)
    min_lat = min(nextbus_df.lat)
    max_long = max(nextbus_df.lon)
    max_lat = max(nextbus_df.lat)

    bmap = Basemap(llcrnrlon=min_long, llcrnrlat=min_lat,
                   urcrnrlon=max_long, urcrnrlat=max_lat,
                   ellps='WGS84',
                   resolution='h', area_thresh=1000)

    bmap.drawmapboundary(fill_color='white')

    bmap.scatter(nextbus_df.lon, nextbus_df.lat,
                 marker='d', edgecolor='g', facecolor='g', alpha=0.5)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.axis([min_long, max_long, min_lat, max_lat])
    plt.title('NextBus Vehicle Locations for route {}'.format(route))
    plt.grid(True)
    # plt.legend(loc='lower center')
    plt.savefig('nextbus_vehicle_locations.png', fmt='png', dpi=600)
    # plt.show()


def get_gmap_markers_for_dataframe(nextbus_df, containing_geom=None):
    """Builds and returns the string with the Google Maps markers to plot the
    transit vehicles in the Panda data frame given as argument (and which
    vehicles optionally happen to be inside the 'containing_geom')."""

    from shapely.geometry import Point

    gmaps_markers = ""

    # %7C is equal to the pipe '|' character
    # "&markers=color:green%7C40.718217,-73.998284"
    # "&markers=color:green%7C40.718217,-73.998284"

    color_palette = ["green", "red", "blue", "yellow", "orange"]

    # note that the parser of the NextBus real-time vehicle location does not
    # return 'NA' as the counterpart of this script in R, but returns the
    # explicit string 'UNKNOWN' as the direction_tag (this parser assumes
    # that NextBus never returns a direction_tag with value 'UNKNOWN' -FIXME)

    unique_dir_tags = pd.unique(nextbus_df.dirTag.ravel())

    # build the sequence of Markers points in the Google Maps
    for a_dir_tag_idx in range(len(unique_dir_tags)):
        # find the NextBus vehicles in this data frame with that dir tag
        a_dir_tag = unique_dir_tags[a_dir_tag_idx]
        color = color_palette[a_dir_tag_idx % len(color_palette)]
        marker_for_this_dir_tag = "markers=color:{}%7Csize=tiny%7Clabel:{}".\
                                  format(color, a_dir_tag.upper())

        for dummy_index, row in nextbus_df[nextbus_df.dirTag == a_dir_tag].\
                                    iterrows():
            # see if this vehicle in this direction is also within the
            # contained geometry requested (use 'longitude, latitude' order
            # as the Python Fiona module uses -we assume the WSG84 coordinate
            # system)
            if containing_geom:
                vehicle_p = Point(row['lon'], row['lat'])
                # print "Checking vehicle {} inside {}".\
                #            format(vehicle_p.wkt, containing_geom.wkt)
                if not containing_geom.contains(vehicle_p):
                    # there is a 'containing_geom' given and this vehicle's
                    # location is not contained inside it: ignore this vehicle
                    continue

            vehicle = "{:7.7f},{:7.7f}".format(row['lat'], row['lon'])
            marker_for_this_dir_tag += "%7C" + vehicle

        # sys.stderr.write("DEBUG: Google Maker for dir_tag '{}': {}\n".\
        #                    format(a_dir_tag, marker_for_this_dir_tag))

        if gmaps_markers:
            gmaps_markers += '&' + marker_for_this_dir_tag
        else:
            gmaps_markers = marker_for_this_dir_tag

    return gmaps_markers


def gmap_nextbus_dataframe(nextbus_df, containing_geom=None,
                           gmap_type='hybrid'):
    """Plots the NextBus Vehicle Location's Panda Data frame which (optionally)
    happen to be inside a 'containing_geom', into an image using Google Maps.
    The type of the Google Map (hybrid, roadmap, etc) is given in the
    'gmap_type' argument."""

    centr_long = (min(nextbus_df.lon) + max(nextbus_df.lon)) / 2
    centr_lat = (min(nextbus_df.lat) + max(nextbus_df.lat)) / 2

    gmaps_markers = get_gmap_markers_for_dataframe(nextbus_df, containing_geom)

    gmap_url = ("https://maps.googleapis.com/maps/api/staticmap?"
                "center={:7.7f},{:7.7f}&format=png&zoom=12"
                "&size=800x800&maptype={}&scale=2&{}"
               ).format(centr_lat, centr_long, gmap_type, gmaps_markers)

    # sys.stderr.write("DEBUG: Retrieving Google Maps: {}\n".format(gmap_url))

    try:
        gmap_content = urllib2.urlopen(gmap_url)
        # the filename where to save the Google Maps should be provided -FIXME
        gmap_file = open('nextbus_vehicle_locations_gmaps.png', 'wb')
        gmap_file.write(gmap_content.read())
        gmap_file.close()
    except Exception:     # pylint: disable=broad-except
        exc_type, exc_value, dummy_callstack = sys.exc_info()
        sys.stderr.write("ERROR: Exception retrieving Google Maps: {}\n".
                         format(gmap_url))
        sys.stderr.write('ERROR info: {}: {}\n'.format(exc_type, exc_value))


def main():
    """Main function."""

    import argparse
    from argparse import RawDescriptionHelpFormatter

    detailed_usage = get_this_script_docstring()

    summary_usage = ('Plots the vehicle locations servicing a transit route '
                     '(and which optionally are also inside a given '
                     'geospatial region).')

    # The ArgParser

    parser = argparse.ArgumentParser(description=summary_usage,
                                     epilog=detailed_usage,
                                     formatter_class
                                     =RawDescriptionHelpFormatter)

    parser.add_argument('agency', metavar='AGENCY', type=str,
                        help="NextBus transit agency on which to work on.")

    parser.add_argument('route', metavar='ROUTE', type=str,
                        help="NextBus transit route for which to plot the "
                             "locations of the vehicles servicing this "
                             "route")

    parser.add_argument('-i', '--in_geom', required=False,
                        type=str, metavar='IN_CONTAINING_GEOM',
                        help="A containing area (given as an OGC WKT string "
                             "in the WSG84 coordinate system with longitudes "
                             "first and latitudes later -longit, latitude-) "
                             "inside which to draw the transit vehicles "
                             "which are passing now through this geospatial "
                             "area, and to ignore all other transit vehicles "
                             "not inside this area.")

    allowable_gmap_types = ["roadmap", "mobile", "satellite", "terrain",
                            "hybrid", "mapmaker-roadmap", "mapmaker-hybrid"]

    parser.add_argument('-m', '--map_type',
                        default='hybrid', choices=allowable_gmap_types,
                        required=False, metavar='GOOGLE-MAPTYPE',
                        help='Which maptype of Google Map to request '
                             '(default: %(default)s)')

    args = parser.parse_args()

    if not args.agency or not args.route:
        sys.stderr.write("ERROR: Arguments not provided for Transit Agency "
                         "and Route\n")
        sys.exit(1)

    agency_code = args.agency
    bus_route = args.route

    containing_geom = None
    if args.in_geom:
        print "Parsing " + args.in_geom
        containing_geom = shapely.wkt.loads(args.in_geom)

    gmap_type = 'hybrid'
    if args.map_type:
        gmap_type = args.map_type

    # Query NextBus real-time vehicle location servicing a transit route and
    # load it into a Panda data frame
    nextbus_dataframe = dataframe_nextbus_bus_location(agency_code, bus_route)

    # print nextbus_dataframe

    render_nextbus_dataframe(bus_route, nextbus_dataframe)
    gmap_nextbus_dataframe(nextbus_dataframe, containing_geom, gmap_type)


def get_this_script_docstring():
    """Utility function to get the Python docstring of this script"""

    import os
    import inspect

    current_python_script_pathname = inspect.getfile(inspect.currentframe())
    dummy_pyscript_dirname, pyscript_filename = \
        os.path.split(os.path.abspath(current_python_script_pathname))
    pyscript_filename = os.path.splitext(pyscript_filename)[0]  # no extension
    pyscript_metadata = __import__(pyscript_filename)
    pyscript_docstring = pyscript_metadata.__doc__
    return pyscript_docstring


if __name__ == '__main__':
    main()
