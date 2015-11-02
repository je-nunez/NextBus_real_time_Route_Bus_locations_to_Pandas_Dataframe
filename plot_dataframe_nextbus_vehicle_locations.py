#!/usr/bin/env python2

"""
Retrieves a NextBus Vehicle Locations Feed for a route into a Panda Data frame
"""

import sys
import time
import urllib2
import xml.etree.ElementTree as ET
import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
# from matplotlib.patches import Polygon, Circle


# how long in time to analyze changes in the vehicle locations in NextBus:
# in the most recent 15 minutes
#
TIME_WINDOW_LOCATION_CHANGE = 30 * 60

# pylint: disable=line-too-long

def dataframe_nextbus_bus_location(agency, route):
    """Retrieves the data from NextBus Vehicle Locations XML API, at

       http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=<agency_tag>&r=<route tag>&t=<epoch time in msec>

    parses the XML, and returns a Panda Data frame with the information."""

    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals

    nextbus_vehicle_locations_fmt = "http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a={}&r={}&t={}000"

    # current time
    now_epoch = int(time.time())
    start_time = now_epoch - TIME_WINDOW_LOCATION_CHANGE

    # Get the changes in vehicle locations since the last 15 minutes
    url_nextbus_feed = nextbus_vehicle_locations_fmt.format(agency, route,
                                                            start_time)

    sys.stderr.write("DEBUG: NextBus Vehicles: {}\n".format(url_nextbus_feed))
    nextbus_vehicle_location = urllib2.urlopen(url_nextbus_feed).read()
    # sys.stderr.write("DEBUG: read: {}\n".format(nextbus_vehicle_location))

    root = ET.fromstring(nextbus_vehicle_location)

    # A cleaner conversion from NextBus Vehicle Locations to Panda Dataframe
    # is necessary -note that NextBus uses the Java Camel Style notations for
    # its symbols.
    dataframe_columns = ["id", "lon", "lat", "secsSinceReport", "routeTag",
                         "dirTag", "heading", "speedKmHr"]
    dataframe_records = []

    for elem in root:
        # vehicle {'lon': '-122.3925', 'secsSinceReport': '23', 'id': '6290', 'routeTag': '38R', 'predictable': 'true', 'speedKmHr': '0', 'lat': '37.78986', 'dirTag': '38R__O_F00', 'heading': '218'}
        if elem.tag != 'vehicle':
            sys.stderr.write("WARN: ignoring {}\n".format(str(elem)))
            continue

        current_record = []

        vehicle_id = elem.get('id', default="UNKNOWN")
        current_record.append(vehicle_id)

        vehicle_longitude = np.nan   # NaN
        if 'lon' in  elem.attrib:
            try:
                # Do your best to convert to float...
                vehicle_longitude = float(elem.attrib['lon'])
            except ValueError as dummy_ignored_exc:
                pass
        current_record.append(vehicle_longitude)

        vehicle_latitude = np.nan
        if 'lat' in  elem.attrib:
            try:
                vehicle_latitude = float(elem.attrib['lat'])
            except ValueError as dummy_ignored_exc:
                pass
        current_record.append(vehicle_latitude)

        vehicle_last_updated = np.nan
        if 'secsSinceReport' in  elem.attrib:
            try:
                vehicle_last_updated = float(elem.attrib['secsSinceReport'])
            except ValueError as dummy_ignored_exc:
                pass
        current_record.append(vehicle_last_updated)

        route_tag = elem.get('routeTag', default="UNKNOWN")
        current_record.append(route_tag)

        dir_tag = elem.get('dirTag', "UNKNOWN")
        current_record.append(dir_tag)

        heading = elem.get('heading', "UNKNOWN")
        current_record.append(heading)

        vehicle_speed = np.nan
        if 'speedKmHr' in  elem.attrib:
            try:
                vehicle_speed = float(elem.attrib['speedKmHr'])
            except ValueError as dummy_ignored_exc:
                pass
        current_record.append(vehicle_speed)

        # append the current record to the list of records
        dataframe_records.append(current_record)

    # Create the Panda DataFrame from the NextBus Vehicle Locations
    vehicle_locations_df = DataFrame.from_records(data=dataframe_records,
                                                  columns=dataframe_columns)
    return vehicle_locations_df


def render_nextbus_dataframe(route, nextbus_df):
    """Plots the NextBus Vehicle Location's Panda Data frame to a
    Matplotlib and Basemap Geospatial image."""

    bmap = Basemap(llcrnrlon=min(nextbus_df.lon),
                   llcrnrlat=min(nextbus_df.lat),
                   urcrnrlon=max(nextbus_df.lon),
                   urcrnrlat=max(nextbus_df.lat),
                   ellps='WGS84',
                   resolution='h', area_thresh=1000)

    bmap.drawmapboundary(fill_color='white')

    bmap.scatter(nextbus_df.lon, nextbus_df.lat,
                 marker='o', edgecolor='b', facecolor='b', alpha=0.5)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('NextBus Vehicle Locations for route {}'.format(route))
    plt.grid()
    # plt.legend(loc='lower center')
    plt.savefig('nextbus_vehicle_locations.png', fmt='png', dpi=300)


def main():
    """Main function."""

    # the list of transit agencies for NextBus can be taken here:
    #
    #     http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList
    #
    # url_agencies <- "http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList"
    #
    # NextBus "sf-muni" = San Francisco Municipal Transportation Agency

    # TODO: get agency_code and bus_route from the command-line via
    #       argparse.ArgumentParser
    agency_code = "sf-muni"

    # the bus route code. For a given transit agency, it can be taken from here:
    #
    #   http://webservices.nextbus.com/service/publicXMLFeed?command=routeList&a=<agency-code>
    #
    # In this case, the NextBus code is the same as the bus#, ie., San Francisco Muni 38R bus

    bus_route = "38R"

    nextbus_dataframe = dataframe_nextbus_bus_location(agency_code, bus_route)

    print nextbus_dataframe

    render_nextbus_dataframe(bus_route, nextbus_dataframe)


if __name__ == '__main__':
    main()
