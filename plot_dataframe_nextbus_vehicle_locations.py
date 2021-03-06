#!/usr/bin/env python2

"""
Retrieves a NextBus Vehicle Locations Feed for a route into a Panda Data frame
and plots it geospatially using Matplotlib Basemap and Google Maps
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
                                   time_window_location_change=30 * 60,
                                   containing_geom=None):
    # pylint: disable=line-too-long
    """Retrieves the data from NextBus Vehicle Locations XML API, at

       http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=<agency_tag>&r=<route tag>&t=<epoch time in msec>

    parses the XML, and for those transit vehicles servicing this route which
    are inside a 'containing_geom' in WSG84 coordinates, gathers them into a
    Panda Data frame, returning it."""

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
        # parse this NextBus vehicle, if its location is inside
        # 'containing_geom'
        elem_list = listify_nextbus_xml_elem(xml_elem, containing_geom)

        if elem_list:
            # the XML element could be parsed: then append this record to the
            # list of records
            dataframe_records.append(elem_list)

    # Create the Panda DataFrame from the NextBus Vehicle Locations
    vehicle_locations_df = DataFrame.from_records(data=dataframe_records,
                                                  columns=dataframe_columns)
    return vehicle_locations_df


def listify_nextbus_xml_elem(xml_elem, containing_geom=None):
    """Converts a XML Element containing a NextBus Vehicle Location to a
    Python list whose elements are the attributes of that NextBus Vehicle
    Location XML Element. Returns the list, and only if this parsed NextBus
    Vehicle is also inside a 'containing_geom' in WSG84 coordinates."""

    from shapely.geometry import Point

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

    # check if this vehicle's position is inside the 'containing_geom'
    # geospatial condition (use 'longitude, latitude' order as the Python
    # Fiona module uses -we assume the WSG84 coordinate system)

    if containing_geom:
        vehicle_p = Point(vehicle_longitude, vehicle_latitude)
        # print "Checking vehicle {} inside {}".\
        #            format(vehicle_p.wkt, containing_geom.wkt)
        if not containing_geom.contains(vehicle_p):
            # there is a 'containing_geom' given and this vehicle's
            # location is not contained inside it: ignore this vehicle
            return None

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
    # Other components (like GMaps plotting) will also use Matplotlib, so
    # it's better to clear the figure that Matplotlib generated
    plt.clf()


def get_rgb_hexad_color_palete():
    """Returns a list of RGB values with the color palette used to plot the
    transit vehicles returned by NextBus. Each entry returned in the color
    palette has the RGB hexadecimal format, and without the prefix '0x' as
    for colors in Google Maps, nor the prefix '#' for the matplotlib color.
    Ie., the entry for blue is returned as '0000FF' and for red 'FF0000'."""

    # We don't use these color names directly because their intensity might
    # be (are) reflected diferently between between the remote server and
    # matplotlib, and this difference in rendering a same color affects the
    # color-legend in matplotlib. For this reason too, we don't need to use
    # only the named colors in Google Maps but more in matplotlib, for in
    # both cases hexadecimal RGB values are really used.

    high_contrast_colors = ["green", "red", "blue", "yellow", "aqua",
                            "brown", "gray", "honeydew", "purple",
                            "turquoise", "magenta", "orange"]

    from matplotlib.colors import ColorConverter, rgb2hex

    color_converter = ColorConverter()
    hex_color_palette = [rgb2hex(color_converter.to_rgb(cname))[1:] for \
                         cname in high_contrast_colors]
    # matplotlib.colors.cnames[cname] could have been used instead of rgb2hex

    return hex_color_palette


def get_gmap_markers_for_dataframe(nextbus_df):
    """Builds and returns the string with the Google Maps markers to plot the
    transit vehicles in the Panda data frame given as argument."""

    gmaps_markers = ""

    # %7C is equal to the pipe '|' character
    #    "&markers=color:green%7C40.718217,-73.998284"
    #    "&markers=color:green%7C40.718217,-73.998284"
    #
    color_palette = get_rgb_hexad_color_palete()

    # note that the parser of the NextBus real-time vehicle location does not
    # return 'NA' as the counterpart of this script in R, but returns the
    # explicit string 'UNKNOWN' as the direction_tag (this parser assumes
    # that NextBus never returns a direction_tag with value 'UNKNOWN' -FIXME)

    unique_dir_tags = pd.unique(nextbus_df.dirTag.ravel())

    color_legend = {}

    # build the sequence of Markers points in the Google Maps
    for a_dir_tag_idx in range(len(unique_dir_tags)):
        # find the NextBus vehicles in this data frame with that dir tag
        a_dir_tag = unique_dir_tags[a_dir_tag_idx]
        color = color_palette[a_dir_tag_idx % len(color_palette)]

        # Build the legend for this color to this direction of the route
        if a_dir_tag_idx < len(color_palette):
            color_legend[color] = a_dir_tag
        else:
            # a_dir_tag_idx >= len(color_palette): there are more directions
            # than colors: print a warning only for the first occurrence when
            # it is noticed this case
            if a_dir_tag_idx == len(color_palette):
                sys.stderr.write("WARNING: More directions in route: " +
                                 "{} than colors to plot them: {}".
                                 format(len(unique_dir_tags),
                                        len(color_palette)) +
                                 "\n"
                                )

        # Build the Google Map marker for this direction of the transit route
        marker_for_this_dir_tag = "markers=color:0x{}%7Csize=tiny%7Clabel:{}".\
                                  format(color, a_dir_tag_idx)

        for dummy_index, row in nextbus_df[nextbus_df.dirTag == a_dir_tag].\
                                    iterrows():

            # vehicle = "{:7.7f},{:7.7f}".format(row['lat'], row['lon'])
            marker_for_this_dir_tag += "%7C{:7.7f},{:7.7f}".\
                                           format(row['lat'], row['lon'])

        # sys.stderr.write("DEBUG: Google Maker for dir_tag '{}': {}\n".\
        #                    format(a_dir_tag, marker_for_this_dir_tag))

        if gmaps_markers:
            gmaps_markers += '&' + marker_for_this_dir_tag
        else:
            gmaps_markers = marker_for_this_dir_tag

    return (gmaps_markers, color_legend)


def get_gmap_url_for_dataframe(nextbus_df, gmap_type='hybrid'):
    """Builds and returns the string with the Google Maps URL to plot the
    transit vehicles in the Panda data frame given as argument."""

    centr_long = (min(nextbus_df.lon) + max(nextbus_df.lon)) / 2
    centr_lat = (min(nextbus_df.lat) + max(nextbus_df.lat)) / 2

    gmaps_markers, color_legend = get_gmap_markers_for_dataframe(nextbus_df)

    gmap_url = ("https://maps.googleapis.com/maps/api/staticmap?"
                "center={:7.7f},{:7.7f}&format=png&zoom=12"
                "&size=800x800&maptype={}&scale=2&{}"
               ).format(centr_lat, centr_long, gmap_type, gmaps_markers)

    # sys.stderr.write("DEBUG: Retrieving Google Maps: {}\n".format(gmap_url))

    return (gmap_url, color_legend)


def build_legend_colors_to_directs(color_legend):
    """Returns a set of matplotlib legend lines and texts according to the
    mapping in the dictionary 'color_legend'."""

    import matplotlib.patches as mpatches

    legend_items = []
    for used_color in color_legend:
        direction_route = color_legend[used_color]

        legend_patch = mpatches.Patch(color='#' + used_color,
                                      capstyle='round', label=direction_route)
        legend_items.append(legend_patch)

    return legend_items


def download_and_plot_gmap(gmap_url, color_legend):
    """Download a Google Map given its URL, plots it using Matplotlib adding a
    legend according to the dictionary 'color_legend', and saves it into a
    PNG image file."""

    gmap_content = urllib2.urlopen(gmap_url)

    axis = plt.gca()

    # disable the plotting of the ticks in the Matplotlib axis

    axis.get_xaxis().set_visible(False)
    axis.get_yaxis().set_visible(False)

    # axis.set_xlim(0, 1)
    # axis.set_ylim(0, 1)

    img = plt.imread(gmap_content)

    plt.imshow(img)

    # Get the lines for the matplotlib legend, according to the mapping in
    # the dictionary 'color_legend'

    legend_lines = build_legend_colors_to_directs(color_legend)

    plt.legend(handles=legend_lines, bbox_to_anchor=(1.00, 1.00), loc=1,
               borderaxespad=0., prop={"size": 8})

    # the filename where to save the Google Maps should be provided -FIXME
    plt.savefig('nextbus_vehicle_locations_gmaps.png', fmt='png', dpi=300)
    plt.clf()


def gmap_nextbus_dataframe(nextbus_df, gmap_type='hybrid'):
    """Plots the NextBus Vehicle Location's Panda Data frame into an image
    using Google Maps. The type of the Google Map (hybrid, roadmap, etc) is
    given in the 'gmap_type' argument."""

    gmap_url, color_legend = get_gmap_url_for_dataframe(nextbus_df, gmap_type)

    try:

        download_and_plot_gmap(gmap_url, color_legend)

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

    # Query the changes in NextBus real-time vehicle location servicing a
    # transit route in the last 15 minutes and whose vehicles are now inside a
    # 'containing_geom', and load them into a Panda data frame
    nextbus_dataframe = dataframe_nextbus_bus_location(agency_code, bus_route,
                                                       15 * 60,
                                                       containing_geom)

    # print nextbus_dataframe

    render_nextbus_dataframe(bus_route, nextbus_dataframe)
    gmap_nextbus_dataframe(nextbus_dataframe, gmap_type)


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
