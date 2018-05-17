import logging

import numpy as np
from shapely.geometry import Point

import bus
import config as cf
import insertion as ins
import passenger as ps
import stop


class Sim(object):
    def __init__(self):
        self.t = -cf.ADVANCE_DEMAND
        self.active_buses = []
        self.inactive_buses = []
        self.next_bus_id = 0
        self.next_passenger_id = 0
        self.customers_per_second = cf.N_CUSTOMERS_PER_HR / 3600
        self.init_chk()
        ds = stop.Stop(self.next_stop_id, Point(1, .75), "dem", None)
        self.next_stop_id += 1
        ds2 = stop.Stop(self.next_stop_id, Point(2, .75), "dem", None)
        self.next_stop_id += 1
        d = ps.Passenger(0, "PRD", self.chkpts[0], ds, 0)
        d2 = ps.Passenger(1, "RPD", ds2, self.chkpts[1], 0)
        d3 = ps.Passenger(2, "PD", self.chkpts[0], self.chkpts[1], 0)
        d4 = ps.Passenger(3, "PD", self.chkpts[1], self.chkpts[2], 0)
        from collections import OrderedDict
        self.unserviced_demand = OrderedDict([(d3.id, d3),
                                              (d4.id, d4),
                                              (d.id, d),
                                              (d2.id, d2)])

        logging.debug("Initialized.")

    def init_chk(self):
        self.chkpts = []
        n_chk = cf.N_INT_POINTS + 2
        for i in range(n_chk):
            res = cf.R_LENGTH * (i / (n_chk - 1))
            xy = Point(res, cf.MAX_DEV)
            dep_t = ((i / (n_chk - 1)) * cf.R_TIME * 60)

            self.chkpts.append(stop.Stop(i, xy, "chk", dep_t))
        self.next_stop_id = cf.N_INT_POINTS + 2


    def check_add_bus(self):
        if self.t < 0 or self.next_bus_id >= cf.N_RIDES:
            return
        if self.t % (cf.HEADWAY * 60) == 0:
            self.active_buses.append(bus.Bus(self.next_bus_id, self.chkpts[1:], self.t, self.chkpts[0]))
            self.next_bus_id = self.next_bus_id + 1


    def step(self):
        logging.debug("t is %s", self.t)
        self.check_add_bus()
        ps.add_passengers(self)
        serviced_ids = []
        for dem_id, dem in self.unserviced_demand.items():
            for b in self.active_buses:
                print("checking dem {} with bus {} at time {}".format(dem.id, b.id, self.t))
                result = ins.feasible(dem, b, self.t, self.chkpts)
                if result is not None:
                    serviced_ids.append(dem_id)
        for sid in serviced_ids:
            self.unserviced_demand.pop(sid)

        bus.move_buses(self)
        for b in self.active_buses:
            b.usable_slack_time(self.t, self.chkpts[1].id, self.chkpts)
            b.usable_slack_time(self.t, self.chkpts[2].id, self.chkpts)
        self.t = self.t + cf.T_STEP
