import logging

import numpy as np
from shapely.geometry import Point

import bus
import config as cf
import insertion as ins
import passenger as ps
import test
ps.add_passengers = test.other_other_passengers
import stop
import walk


class Sim(object):
    def __init__(self):
        self.t = -(cf.ADVANCE_DEMAND * 60)
        self.active_buses = []
        self.inactive_buses = []
        self.next_bus_id = 0
        self.next_passenger_id = 0
        self.customers_per_second = cf.N_CUSTOMERS_PER_HR / 3600
        self.init_chk()
        self.unserviced_demand = {}
        self.serviced_demand = []

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

    import tabulate
    def print_passenger_stats(self):
        print("Serviced: {}".format(len(self.serviced_demand)))
        print("Not Serviced: {}".format(len(self.unserviced_demand)))
        print("Avg wait time: {}".format(sum((p.arrival_t - p.request_t) for p in self.serviced_demand) / len(self.serviced_demand)))
        print("Avg travel time: {}".format(sum((p.arrival_t - p.pickup_t) for p in self.serviced_demand) / len(self.serviced_demand)))
        #print(tabulate.tabulate
        pass
        

    def step(self):
        if len(self.active_buses) == 0 and self.next_bus_id >= cf.N_RIDES:
            self.print_passenger_stats()
            raise Exception("DONE!!!")
        logging.debug("t is %s", self.t)
        self.check_add_bus()
        ps.add_passengers(self)
        serviced_ids = []
        new_stop = False
        for dem_id, dem in self.unserviced_demand.items():
            # buses are in order so we choose first time-wise
            for b in self.active_buses:
                result = ins.feasible(dem, b, self.t, self.chkpts)
                if result is not None:
                    print(str(dem) + " is serviced")
                    serviced_ids.append(dem_id)
                    break # move to next demand
                elif cf.ALLOW_WALKING:
                    print("checking for this demand")
                    new_stop = walk.check_walking(dem, b, self.t, self.chkpts, self)

        for sid in serviced_ids:
            serviced = self.unserviced_demand.pop(sid)
            self.serviced_demand.append(serviced)

        if self.t >=0:
            bus.move_buses(self)

        self.t = self.t + cf.T_STEP
        return new_stop
