import logging

import numpy as np
from shapely.geometry import Point

import config as cf

class Bus(object):
    def __init__(self, vid, stops, t, ostop):
        self.id = vid
        self.passengers_on_board = {}
        self.passengers_assigned = {}
        self.serviced_passengers = []
        self.miles_traveled = 0
        self.stops_remaining = stops.copy()
        self.stops_visited = [ostop]
        self.cur_xy = Point(0, cf.MAX_DEV)
        self.start_t = t
        self.hold_time = 0 # hold time, seconds

        # note if distance not unfiorm, this would change
        # also the '.distance' call is euclidean, but
        # all stops have the same y-value
        dist = self.cur_xy.distance(stops[0].xy)
        dep_t = stops[0].dep_t
        self.init_slack_times = {s.id: (dep_t - cf.WAITING_TIME - (dist / (cf.BUS_SPEED / 3600))) for s in stops}
        self.avail_slack_times = {s.id: (dep_t - cf.WAITING_TIME - (dist / (cf.BUS_SPEED / 3600))) for s in stops}

    def plot(self, ax):
        return ax.scatter([self.cur_xy.x], [self.cur_xy.y])

    def usable_slack_time(self, t, nxt_chk_id, chkpts):
        """
        Computes how much slack time the bus can use 
        assuming its next checkpoint is `nxt_chk_id`.
        This is based on the formula in the MAST paper.
        """
        init_slack = self.init_slack_times[nxt_chk_id]
        avail_slack = self.avail_slack_times[nxt_chk_id]
        next_chk = chkpts[nxt_chk_id]
        prev_chk = chkpts[nxt_chk_id - 1]
        t_now = t - self.start_t
        if t_now < prev_chk.dep_t:
            return min(avail_slack, init_slack * cf.MIN_INIT_SLACK)
        elif t_now > next_chk.dep_t:
            return 0
        
        # just straight from the MAST paper
        # essentially a fraction based on how
        # close to the next checkpoint we are
        usable_slack =  init_slack * (1 + (cf.MIN_INIT_SLACK - 1) * (1 - ((t_now - prev_chk.dep_t)  / (chkpts[1].dep_t))))
        return min(avail_slack, usable_slack)

def move_buses(sim):
    change = False
    for bus in sim.active_buses:
        if bus.hold_time >= 0:
            logging.debug("bus %s is holding", bus.id)
            bus.hold_time -= 1
            # get the stragglers
            if bus.hold_time <= 0:
                cur_stop = bus.stops_visited[-1]
                to_move = []
                for p in bus.passengers_assigned.values():
                    if p.o == cur_stop:
                        to_move.append(p.id)
                        if (not change):
                            change = True
                for m in to_move:
                    pas = bus.passengers_assigned.pop(m)
                    pas.pickup_t = sim.t
                    bus.passengers_on_board[m] = pas
            continue

        logging.debug("bus %s updating", bus.id)
        logging.debug("cur_xy is %s", bus.cur_xy)

        y_dist = bus.stops_remaining[0].xy.y - bus.cur_xy.y
        x_dist = bus.stops_remaining[0].xy.x - bus.cur_xy.x
        # move either x or y
        old_xy = bus.cur_xy
        if np.abs(y_dist) > np.abs(x_dist):
            dy = np.sign(y_dist) * (cf.BUS_SPEED / 3600) * cf.T_STEP
            if np.abs(dy) >= np.abs(y_dist):
                temp = handle_arrival(bus, sim.t)
                if (not change):
                    change = temp
                continue
            bus.cur_xy = Point(bus.cur_xy.x, bus.cur_xy.y + dy)
        else:
            dx = np.sign(x_dist) * (cf.BUS_SPEED / 3600) * cf.T_STEP
            if np.abs(dx) >= np.abs(x_dist):
                temp = handle_arrival(bus, sim.t)
                if (not change):
                    change = temp
                continue
            bus.cur_xy = Point(bus.cur_xy.x + dx, bus.cur_xy.y)

        logging.debug("new xy is %s", bus.cur_xy)

        diff = bus.cur_xy.distance(old_xy)
        logging.debug("diff is %s", diff)
        bus.miles_traveled += diff
        logging.debug("bus has traveled %s", bus.miles_traveled)
    if sim.active_buses and sim.active_buses[0].stops_remaining == []:
        print("FINISHED || " + str(len(sim.active_buses[0].passengers_assigned)))
        if (len(sim.active_buses[0].passengers_assigned) > 0):
            import pdb; pdb.set_trace()
        sim.inactive_buses.append(sim.active_buses.pop(0))
    return change

def handle_arrival(bus, t):
    #print("ARRIVED")
    change = False
    arr_stop = bus.stops_remaining.pop(0);
    #there may be duplicates of stops from merge -> may be a problem?
    bus.stops_visited.append(arr_stop)
    next_xy = bus.stops_visited[-1].xy
    bus.cur_xy = next_xy
    if arr_stop.dep_t:
        bus.hold_time = arr_stop.dep_t - (t - bus.start_t)
        bus.avail_slack_times[arr_stop.id] = 0
    else:
        bus.hold_time = cf.WAITING_TIME

    to_pop = []
    print("BUS " + str(bus.id) + " || Drop off: ", end= '')
    for passenger in bus.passengers_on_board.values():
        if passenger.d == arr_stop:
            to_pop.append(passenger.id)
            print(str(passenger.id), end = ', ')
            change = True
    print()
    for p in to_pop:
        pas = bus.passengers_on_board.pop(p)
        pas.arrival_t = t
        bus.serviced_passengers.append(pas)
        
    print("Pickup: ", end ='')
    to_pop = []
    for passenger in bus.passengers_assigned.values():
        if passenger.o == arr_stop:
            print(str(passenger.id) + "(" + str(passenger.d.xy) + ")", end = ", ")
            to_pop.append(passenger.id)
            change = True
    for p in to_pop:
        pas = bus.passengers_assigned.pop(p)
        pas.pickup_t = t
        bus.passengers_on_board[p] = pas
    print()
    for stop in bus.stops_remaining:
        print(stop.xy, end = ', ')
    print()
    print()
    return change
#    print("==== ON BOARD ====")
#    print(bus.passengers_on_board)
#    print("==== ASSIGNED ====")
#    print(bus.passengers_assigned)
#    print("==== SERVICED ====")
#    print(bus.serviced_passengers)
