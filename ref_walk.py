import numpy as np
from shapely.geometry import Point

import config as cf
import insertion as ins
import stop

def check_distance(demand, cur_stop, next_stop):
    daqx = demand.xy.x - cur_stop.xy.x 
    daqy = demand.xy.y - cur_stop.xy.y 
    dqbx = next_stop.xy.x - demand.xy.x
    dqby = next_stop.xy.y - demand.xy.y
    
    dabx = next_stop.xy.x - cur_stop.xy.x
    daby = next_stop.xy.y - cur_stop.xy.y
    #ddist = travel distance added
    ddist = np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
    ddist_x = np.sum(np.abs([daqx, dqbx])) - np.abs(dabx)
    ddist_y = np.sum(np.abs([daqy, dqby])) - np.abs(daby)
    return (ddist, ddist_x, ddist_y)
    
def calculate_closest_walk(demand, cur_stop, next_stop):
    daqx = demand.xy.x - cur_stop.xy.x 
    daqy = demand.xy.y - cur_stop.xy.y 
    dqbx = next_stop.xy.x - demand.xy.x
    dqby = next_stop.xy.y - demand.xy.y
    minX = min(np.abs([daqx, dqbx]));
    minY = min(np.abs([daqy, dqby]));
    return (minX, minY)

def check_walking(demand, bus, t, chkpts, sim):
    if demand.type == "PD":
        return None

    if demand.type == "RPD":
        return rpd_walk(demand, bus, t, chkpts, sim)
    if demand.type == "PRD":
        return prd_walk(demand, bus, t, chkpts, sim)
    if demand.type == "RPRD":
        return rprd_walk(demand, bus, t, chkpts, sim)


def rpd_walk(demand, bus, t, chkpts, sim):
    #treat the bus's current location as a stop.
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    #list of all current stops in the queue
    add_faux = [faux_stop] + bus.stops_remaining
    try:
        #finds the last index where the demand is
        max_possible_ix = add_faux.index(demand.d)
    # weve already passed their checkpoint, not possible
    except ValueError:
        return None
    
    costs_by_stop = {}
    #zips (all stops before last index, stops remaining) -> every consequtive pair
    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux[:max_possible_ix], bus.stops_remaining)):
        
        nxt_chk = None;
        for s in bus.stops_remaining[ix:]:
            #if it is a checkpoint (finds the enxt checkpoint)
            if s.dep_t:
                nxt_chk = s
                break
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts) - cf.WAITING_TIME
        if st < 0:
            continue
        ddist, ddist_x, ddist_y = check_distance(demand.o, cur_stop, next_stop)
        
        # initial walk direction
        walk_dir = 'x' if ddist_x > ddist_y else ddist_y
        max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60) # mph * (1 hr / 60 min)
        max_drive_dist = st * (cf.BUS_SPEED / 3600) 
        # make sure we can actually cover the distance
        
        #[ASK] why was max_walk_dist multipled by 2
        max_distance_possible = max_walk_dist + max_drive_dist 
        if ddist > max_distance_possible:
            #if it is beyond max distance, then we cannot walk there
            #print("Max distance is: " + str(max_distance_possible) + " ddist is {}".format(ddist))
            pass
        else:
            """
            if walk_dir == 'x':
                #walk distance is either halfway to the stop or its maximum walking distance
                walk_dist = np.min([ddist_x / 2, max_walk_dist])
                #if we have left over max walk distance, we can allow them to travel the y direction as well
                if walk_dist < max_walk_dist and ddist_y > 0:
                    new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist,
                                  demand.o.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, ddist_y]))
                else:
                    new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist, demand.o.xy.y)
            else:
                walk_dist = np.min([ddist_y / 2, max_walk_dist])
                if walk_dist < max_walk_dist and ddist_x > 0:
                    new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist,
                                  demand.o.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, ddist_y / 2]))
                else:
                    new_o = Point(demand.o.xy.x,
                                  np.sign(ddist_y)* walk_dist +  demand.o.xy.y)
            """
            #distance from the stops
            #ddist_x/ddist_y is accurate when the demand in inbetween the two stops.
            #xdist/ydist is accurate when the demand falls outside the bounds.
            xdist, ydist = calculate_closest_walk(demand.o, cur_stop, next_stop)
            if walk_dir == 'x':
                #the stop is not currently feasible so we will have to walk the difference
                walk_dist = min(ddist_x, xdist) - max_drive_dist
                #if we have left over max walk distance, we can allow them to travel the y direction as well
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist,
                              demand.o.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, min(ddist_y, ydist)]))
            else:
                walk_dist = min(ddist_y, ydist) - max_drive_dist
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* np.min([max_walk_dist - walk_dist, min(ddist_x, xdist)]),
                              demand.o.xy.y + np.sign(ddist_y) * walk_dist)
                    
            walk_arr_t = t + (np.abs(new_o.x - demand.o.xy.x) + np.abs(new_o.y - demand.o.xy.y)) / (cf.W_SPEED / 3600.)
            #TODO: make sure that the walker arrives before the bus
            # what we need to write is something that computes exactly
            # when the bus would arrive based on where we are inserting this
            # stop.
            # THIS IS CURRENTLY BROKEN & only works for this test example!!
            bus_arr_t = t + bus.hold_time + (np.abs(cur_stop.xy.x - new_o.x) + np.abs(new_o.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t <= walk_arr_t:
                #The passenger is there after the bus leaves
                #print("Bus time: " + str( bus_arr_t) + ", Walk time: " + str(walk_arr_t))
                pass
            else: 
                new_o_stop = stop.Stop(sim.next_stop_id, new_o, "walk", None)
                sim.next_stop_id += 1
                old_o = demand.o
                demand.o = new_o_stop
                #check that new stop is feasible
                result = ins.feasible(demand, bus, t, chkpts, cost_only=True)
                if result:
                    min_ix, min_cost, min_nxt_chk = result
                    costs_by_stop[new_o_stop.id] =  (new_o_stop, min_ix, min_cost, min_nxt_chk, bus_arr_t, walk_arr_t)
                demand.o = old_o

    min_ix = None
    min_stop = None
    min_nxt_chk = None
    min_cost = 9999
    for k, v in costs_by_stop.items():
        if v[2] < min_cost:
            min_stop = v[0]
            min_ix = v[1]
            min_cost = v[2]
            min_nxt_chk = v[3]
            
            print("WALK || Bus Time: " + str(v[4]) + ", Walk Time: " + str(v[5]))

    # we return the old stop for visualization purposes.
    # when we plot, the passengers 'o' has been set to
    # the new origin, so we want to plot where they initially
    # were before they walked
    return (min_cost, min_stop, min_ix, min_nxt_chk)
    
def prd_walk(demand, bus, t, chkpts, sim):
    t_now = t - bus.start_t
    # weve already passed this stop
    if t_now > demand.o.dep_t:
        return None
    try:
        earliest_ix = bus.stops_remaining.index(demand.o)
    except ValueError:
        earliest_ix = -1

    if earliest_ix == -1:
        stops_slice = [bus.stops_visited[-1]] + bus.stops_remaining
    else:
        stops_slice = bus.stops_remaining[earliest_ix:]

    costs_by_stop = {}
    for ix, (cur_stop, next_stop) in enumerate(zip(stops_slice, stops_slice[1:])):
        nxt_chk = None
        for s in bus.stops_remaining[ix:]:
            #if it is a checkpoint (finds the enxt checkpoint)
            if s.dep_t:
                nxt_chk = s
                break
            
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts) - cf.WAITING_TIME
        if st < 0:
            continue
        ddist, ddist_x, ddist_y = check_distance(demand.d, cur_stop, next_stop)
        
        walk_dir = 'x' if ddist_x > ddist_y else ddist_y
        max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60) # mph * (1 hr / 60 min)
        max_drive_dist = st * (cf.BUS_SPEED / 3600) 
        
        xdist, ydist = calculate_closest_walk(demand.d, cur_stop, next_stop)
        if walk_dir == 'x':
            walk_dist = min(ddist_x, xdist) - max_drive_dist
            new_d = Point(demand.d.xy.x +  np.sign(ddist_x)* walk_dist,
                          demand.d.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, min(ddist_y, ydist)]))
        else:
            walk_dist = min(ddist_y, ydist) - max_drive_dist
            new_d = Point(demand.d.xy.x +  np.sign(ddist_x)* np.min([max_walk_dist - walk_dist, min(ddist_x, xdist)]),
                          demand.d.xy.y + np.sign(ddist_y) * walk_dist)
        walk_arr_t = t + (np.abs(new_d.x - demand.d.xy.x) + np.abs(new_d.y - demand.d.xy.y)) / (cf.W_SPEED / 3600.)
        bus_arr_t = t + bus.hold_time + (np.abs(cur_stop.xy.x - new_d.x) + np.abs(new_d.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
        if bus_arr_t <= walk_arr_t:
            #print("Bus time: " + str( bus_arr_t) + ", Walk time: " + str(walk_arr_t))
            continue
        else: 
            new_d_stop = stop.Stop(sim.next_stop_id, new_d, "walk", None)
            sim.next_stop_id += 1
            old_d = demand.d
            demand.d = new_d_stop
            #check that new stop is feasible
            result = ins.feasible(demand, bus, t, chkpts, cost_only=True)
            if result:
                min_ix, min_cost, min_nxt_chk = result
                costs_by_stop[new_d_stop.id] =  (new_d_stop, min_ix, min_cost, min_nxt_chk, bus_arr_t, walk_arr_t)
            demand.d = old_d

    min_ix = None
    min_stop = None
    old_stop = None
    min_nxt_chk = None
    min_cost = 9999
    for k, v in costs_by_stop.items():
        if v[2] < min_cost:
            min_stop = v[0]
            min_ix = v[1]
            min_cost = v[2]
            min_nxt_chk = v[3]
            print("Bus Time: " + str(v[4]) + ", Walk Time: " + str(v[5]))

    if min_stop:
        old_stop = demand.d
        demand.d = min_stop
        bus.stops_remaining.insert(min_ix, min_stop)
        bus.avail_slack_times[min_nxt_chk[0].id] -= min_nxt_chk[1]
        bus.passengers_assigned[demand.id] = demand
    return old_stop

def rprd_walk(demand, bus, t, chkpts, sim):
    pass
    