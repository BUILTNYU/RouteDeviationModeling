import numpy as np
from shapely.geometry import Point

import config as cf
import stop
import stats

def check_origin(demand, bus, t, chkpts, sim, d):
    #check for normal pickup
    results = stats.check_normal(demand.o, bus, t, chkpts, sim, destination = d, dem = demand)
    if (results):
        #if normal is valid, it can be merge or normal stop
        if (results[4]):
            #record is requests.csv. changes if it is a chkpt or not for merged
            if (results[1].typ == "chk"):
                sim.output.pickup_assignment(demand.id, results[1].id, results[5], results[3][1], results[0], checkpoint = True)
            else:
                sim.output.pickup_assignment(demand.id, results[1].id, results[5], results[3][1], results[0])
            return ("MERGE", results)
        else:
            #The stop is regular and does not need displaying
            sim.output.pickup_assignment(demand.id, results[1].id, 0., results[3][1], results[0])
            return ("NORMAL", results)
    #else check if walking is a vlid option
    else:
        if cf.ALLOW_WALKING:
            walk_origin = check_origin_walk(demand, bus, t, chkpts, sim, d)
            if (walk_origin[1]):
                #the stop requires walking and needs displaying
                sim.output.pickup_assignment(demand.id, walk_origin[1].id, walk_origin[4], walk_origin[3][1], walk_origin[0])
                return ("WALK", (walk_origin[0], walk_origin[1], walk_origin[2], walk_origin[3]))
        return None

#check if walking is valid
def check_origin_walk(demand, bus, t, chkpts, sim, dest):
    #add current location to as a fake stop
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    add_faux = [faux_stop] + bus.stops_remaining
    max_possible_ix = len(add_faux)
    if (dest):
        try:
            #limit stop checking to the destination
            max_possible_ix = add_faux.index(dest)
        except ValueError:
            return (None, None, None, None)
    #get the cost for each demand to walk to each stop
    costs_by_stop = {}
    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux[:max_possible_ix], bus.stops_remaining)):
        nxt_chk = None;
        #next checkpoint for slack time calculations
        for s in bus.stops_remaining[ix:]:
            if s.dep_t:
                nxt_chk = s
                break
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        if st < 0:
            continue
        #check distance and arrival times
        ddist, ddist_x, ddist_y = stats.check_distance(demand.o, cur_stop, next_stop)
        walk_dir = 'x' if ddist_x > ddist_y else ddist_y
        max_walk_dist = stats.get_max_walk_distance(bus, demand.d, t, chkpts, sim)
        max_drive_dist = (st - cf.WAITING_TIME) * (cf.BUS_SPEED / 3600) 
        max_distance_possible = max_walk_dist * 2 + max_drive_dist
        if ddist <= max_distance_possible:
            xdist, ydist = stats.calculate_closest_walk(demand.o, cur_stop, next_stop)
            #prioritizes the longer distance
            if walk_dir == 'x':
                #ddist_x/y is not accurate when the stop falls outside the two points
                #I use the closest point to the rectangle of the two points
                walk_dist = min(np.abs([ddist_x, xdist])) - max_drive_dist
                new_o = Point(demand.o.xy.x +  np.sign(xdist)* walk_dist,
                              demand.o.xy.y + np.sign(ydist) * np.min([max_walk_dist - walk_dist, min(ddist_y, ydist)]))
            else:
                #prioritizes driving over walking
                walk_dist = min(np.abs([ddist_y, ydist])) - max_drive_dist
                new_o = Point(demand.o.xy.x +  np.sign(xdist)* np.min([max_walk_dist - walk_dist, min(ddist_x, xdist)]),
                              demand.o.xy.y + np.sign(ydist) * walk_dist)
            walk_arr_t = t + (np.abs(new_o.x - demand.o.xy.x) + np.abs(new_o.y - demand.o.xy.y)) / (cf.W_SPEED / 3600.)
            bus_arr_t = t + bus.hold_time + (np.abs(faux_stop.xy.x - new_o.x) + np.abs(new_o.y - faux_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t < walk_arr_t:
                pass
            else: 
                #record cost of walking to this new stop
                new_o_stop = stop.Stop(sim.next_stop_id, new_o, "walk", None)
                sim.next_stop_id += 1
                ddist, x, y = stats.added_distance(new_o_stop, cur_stop, next_stop)
                delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
                if (not stats.check_feasible(x, y, delta_t, st)):
                    continue
                min_cost = stats.calculate_cost(bus, nxt_chk, ix, delta_t, ddist)
                costs_by_stop[new_o_stop.id] =  (new_o_stop, ix, min_cost, (nxt_chk, delta_t), walk_arr_t)
                if (ix >= len(bus.stops_remaining) or ix < 0):
                    import pdb; pdb.set_trace();
                    
    #compare all available stops to find minimum cost one.
    min_ix = None
    min_stop = None
    min_nxt_chk = None
    min_cost = 9999
    min_time = None
    for k, v in costs_by_stop.items():
        if v[2] < min_cost:
            min_stop = v[0]
            min_ix = v[1]
            min_cost = v[2]
            min_nxt_chk = v[3]
            min_time = walk_arr_t - t
    #debugging
    if (min_stop):
        print("WALK || " + str(min_stop.xy.x) + "," + str(min_stop.xy.y) + "cost: " + str(min_cost))
    return (min_cost, min_stop, min_ix, min_nxt_chk, min_time)

