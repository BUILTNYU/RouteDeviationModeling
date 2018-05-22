from collections import namedtuple

import geopandas as gpd
import numpy as np
from shapely.geometry import Point

import config as cf

Stop = namedtuple("Stop", ["id", "xy", "typ", "dep_t"]) 
Stop.TYPES = ["chk", "dem", "agg", "walk", "fake"]

def random_chk(chkpts, xmin=-1):
    chk = [c for c in chkpts if c.xy.x > xmin]
    return chk[np.random.choice(len(chk))]

def random_xy(sid, xmin=0):
    return Stop(sid, Point((cf.R_LENGTH - xmin) * np.random.rand() + xmin,
                           2 * cf.MAX_DEV * np.random.rand()),
                "dem", None)

def plot_stops(stops, ax=None, color='red', label=None):
    stops_gdf = gpd.GeoDataFrame(stops)
    stops_gdf["geometry"] = stops_gdf["xy"]
    ax = stops_gdf.plot(ax=ax, color=color, label=label)
    ax.set_ylim(0, 2 * cf.MAX_DEV)
    return ax
