import logging

import numpy as np
from shapely.geometry import Point

import config as cf
import stop

class Passenger(object):
    TYPES = ["PD", "RPD", "PRD", "RPRD"]
    def __init__(self, pid, typ,
                 o, d, request_t):
        self.id = pid
        self.type = typ
        self.o = o
        self.d = d
        self.request_t = request_t
        self.pickup_t = -1
        self.arrival_t = -1

    def __repr__(self):
        return "(" + str(self.id) + "," + str(self.o.id)  + "," + str(self.d.id) + "," + str(self.request_t) + "," + str(self.pickup_t) + "," + str(self.arrival_t) + ")"

    def __str__(self):
        return self.__repr__()

    def plot(self, ax):
        s1 = ax.scatter([self.o.xy.x], [self.o.xy.y], color='green', s=2)
        s2 = ax.scatter([self.d.xy.x], [self.d.xy.y], color='blue', s=2)
        return s1, s2


def add_passengers(sim):
    pass
     
#def add_passengers(sim):
#    n = np.random.poisson(sim.customers_per_second)
#    passenger_types = np.random.choice(Passenger.TYPES, size=n, p=cf.PTYPE_WEIGHTS)
#    logging.debug("adding %s passengers of types %s", n, passenger_types)
#    old_len = len(sim.unserviced_demand)
#    for i, ptyp in enumerate(passenger_types):
#
#        if ptyp in {"PD", "PRD"}:
#            o = stop.random_chk(sim.chkpts[:-1])
#        else:
#            o = stop.random_xy(sim.next_stop_id)
#            sim.next_stop_id += 1
#
#        if ptyp in {"RPD", "PD"}:
#            # can only go to destinations after
#            d = stop.random_chk(sim.chkpts[1:], xmin=o.xy.x)
#        else:
#            d = stop.random_xy(sim.next_stop_id, xmin=o.xy.x)
#            sim.next_stop_id += 1
#
#        sim.unserviced_demand.append(Passenger(sim.next_passenger_id + i, ptyp, o, d, sim.t))
#    new_len = len(sim.unserviced_demand)
#    if new_len > old_len:
#        print(sim.unserviced_demand)
#    sim.next_passenger_id += n

