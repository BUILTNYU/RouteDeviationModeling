import logging

import numpy as np
from shapely.geometry import Point

import bus
import config as cf
import insertion as ins
import passenger as ps
import test

import stop
import walk
import walk_merge as walkm
import add_stop as insert

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
        """
    def modify_stop(self, demand, bus, new_stop, origin):
        if (origin):
            old_stop = demand.o
            demand.o = new_stop[1]
        else:
            old_stop = demand.d
            demand.d = new_stop[1]
        bus.stops_remaining.insert(new_stop[2], new_stop[1])
        bus.avail_slack_times[new_stop[3][0].id] -= new_stop[3][1]
        bus.passengers_assigned[demand.id] = demand
        return old_stop
        """
    def step(self):
        if len(self.active_buses) == 0 and self.next_bus_id >= cf.N_RIDES:
            self.print_passenger_stats()
            raise Exception("DONE!!!")
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
                """
                result = ins.feasible(dem, b, self.t, self.chkpts)
                if result is not None:
                    print(str(dem) + " is serviced")
                    serviced_ids.append(dem_id)
                    break # move to next demand
                else:
                    new_stop = None
                    merge_stop = None
                    walk_stop = None
                    if cf.ALLOW_MERGE_WALKING:
                        merge_stop = walkm.check_merge_walking(dem, b, self.t, self.chkpts, self)
                    if cf.ALLOW_NEW_WALKING:
                        walk_stop = walk.check_walking(dem, b, self.t, self.chkpts, self)
                    #check that the stops exist & compare the costs
                    if (merge_stop and walk_stop and merge_stop[1] and walk_stop[1]):
                        if (merge_stop[0] < walk_stop[0]):
                            if (dem.type == "RPD"):
                                new_stop = self.modify_stop(dem, b, merge_stop, True)
                            elif(dem.type == "PRD"):
                                pass
                            else:
                                pass
                        else:
                            if (dem.type == "RPD"):
                                new_stop = self.modify_stop(dem, b, walk_stop, True)
                            elif(dem.type == "PRD"):
                                pass
                            else:
                                pass
                    else:
                        #if only one solution exists, take that solution
                        if (merge_stop and merge_stop[1]):
                            new_stop = self.modify_stop(dem, b, merge_stop, True)
                        elif (walk_stop and walk_stop[1]):
                            new_stop = self.modify_stop(dem, b, walk_stop, True)
                            """
                results = insert.insert_stop(dem, b, self.t, self.chkpts, self)
                new_o, new_d = results[1], results[2]
                if results[0]:
                    serviced_ids.append(dem_id)
                    break

        for sid in serviced_ids:
            serviced = self.unserviced_demand.pop(sid)
            self.serviced_demand.append(serviced)

        if self.t >=0:
            bus.move_buses(self)

        self.t = self.t + cf.T_STEP
        return (new_o, new_d)
