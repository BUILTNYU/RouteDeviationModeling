import logging

from shapely.geometry import Point

import bus
import config as cf
import passenger as ps
import test
import stop
import add_stop as insert
import write
import cost
import average_statistics as astat

class Sim(object):
    def __init__(self, iteration):
        self.t = -(cf.ADVANCE_DEMAND * 60)
        self.active_buses = []
        self.inactive_buses = []
        self.next_bus_id = 0
        self.next_passenger_id = 0
        self.customers_per_second = cf.N_CUSTOMERS_PER_HR / 3600
        self.init_chk()
        self.unserviced_demand = {}
        self.serviced_demand = []

        self.output = write.record_stats(iteration)
        logging.debug("Initialized.")

    def init_chk(self):
        self.chkpts = []
        #Add beginning and endpoints to checkpoints
        n_chk = cf.N_INT_POINTS + 2 
        for i in range(n_chk):
            #X-Coordinates of checkpoints are evenly spaced
            res = cf.R_LENGTH * (i / (n_chk - 1))
            xy = Point(res, cf.MAX_DEV)
            #Departure time are evenly spaced
            dep_t = ((i / (n_chk - 1)) * cf.R_TIME * 60)

            self.chkpts.append(stop.Stop(i, xy, "chk", dep_t))
        self.next_stop_id = cf.N_INT_POINTS + 2


    def check_add_bus(self):
        if self.t < 0 or self.next_bus_id >= cf.N_RIDES:
            return
        #Buses will launch at headway intervals, measured in seconds
        if self.t % (cf.HEADWAY * 60) == 0:
            #Bus (id, stops remaining, time, current stop)
            self.active_buses.append(bus.Bus(self.next_bus_id, self.chkpts[1:], self.t, self.chkpts[0]))
            self.next_bus_id = self.next_bus_id + 1

    def print_passenger_stats(self):
        print("Serviced: {}".format(len(self.serviced_demand)))
        print("Not Serviced: {}".format(len(self.unserviced_demand)))
        print("Avg wait time: {}".format(sum((p.arrival_t - p.request_t) for p in self.serviced_demand) / len(self.serviced_demand)))
        print("Avg travel time: {}".format(sum((p.arrival_t - p.pickup_t) for p in self.serviced_demand) / len(self.serviced_demand)))
        pass

    def step(self):
        if len(self.active_buses) == 0 and self.next_bus_id >= cf.N_RIDES:
            self.print_passenger_stats()
            self.output.end()
            raise ValueError
        logging.debug("t is %s", self.t)
        #Added busses and stops
        self.check_add_bus()
        ps.add_passengers(self)
        #Check stop feasibility
        serviced_ids = []
        new_o, new_d = False, False
        #unserviced demands contain passenger(id, type, pick up, drop off, time of request)
        for dem_id, dem in self.unserviced_demand.items():
            # buses are in order so we choose first time-wise
            for b in self.active_buses:
                #check feasibility of passenger for each bus
               
                results = insert.insert_stop(dem, b, self.t, self.chkpts, self)
                new_o, new_d = results[1], results[2]
                if results[0]:
                    serviced_ids.append(dem_id)
                    break
        
        for sid in serviced_ids:
            serviced = self.unserviced_demand.pop(sid)
            self.serviced_demand.append(serviced)
        
        change = False
        if self.t >=0:
            change = bus.move_buses(self)

        self.t = self.t + cf.T_STEP
        return (new_o, new_d, change)
