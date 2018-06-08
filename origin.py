import numpy as np
from shapely.geometry import Point

import config as cf
import stop
import stats

def check_origin(demand, bus, t, chkpts, sim, d):
    results = stats.check_normal(demand.o, bus, t, chkpts, sim, destination = d)
    if (results):
        print("NORMAL")
        return (True, results)
    else:
        if cf.ALLOW_NEW_WALKING:
            walk_origin = check_origin_walk(demand, bus, t, chkpts, sim, d)
            if (walk_origin[1]):
                return (False, walk_origin)
        else:
            return None
        
def check_origin_merge(demand, bus, t, chkpts, sim, dest):
    max_possible_ix = len(bus.stops_remaining)
    if (dest):
        try:
            max_possible_ix = bus.stops_remaining.index(dest)
        except ValueError:
            return (None, None, None, None)
    costs_by_stop = {}
    for index, merge_stop in enumerate(bus.stops_remaining[:max_possible_ix]):
        if (merge_stop.dep_t):
            continue
        if (index == 0):
            prev_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
        else:
            prev_stop = bus.stops_remaining[index-1]    
        nxt_chk = None
        for s in bus.stops_remaining[index:]:
            if s.dep_t:
                nxt_chk = s
                break
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts) - cf.WAITING_TIME
        if st < 0:
            continue
        ddist_x = demand.o.xy.x - merge_stop.xy.x
        ddist_y = demand.o.xy.y - merge_stop.xy.y
        ddist = np.sum(np.abs([ddist_x, ddist_y]))
        max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60) 
        max_distance_possible = max_walk_dist * 2
        if ddist <= max_distance_possible:
            new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* ddist_x/2,
                          demand.o.xy.y + np.sign(ddist_y) * ddist_y/2)
            walk_arr_t = t + (np.abs(new_o.x - demand.o.xy.x) + np.abs(new_o.y - demand.o.xy.y)) / (cf.W_SPEED / 3600.)
            bus_arr_t = t + bus.hold_time + (np.abs(new_o.x - prev_stop.xy.x) + np.abs(new_o.y - prev_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t <= walk_arr_t:
                pass
            else:
                new_o_stop = stop.Stop(sim.next_stop_id, new_o, "walk", None)
                sim.next_stop_id += 1
                old_o = demand.o
                demand.o = new_o_stop
                result = stats.check_normal(demand.o, bus, t, chkpts, sim, cost_only = True, destination = dest)
                if result:
                    min_cost, temp, min_ix, min_nxt_chk = result
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
            print("MERGE || Bus Time: " + str(v[4]) + ", Walk Time: " + str(v[5]))
    return (min_cost, min_stop, min_ix, min_nxt_chk)

def check_origin_walk(demand, bus, t, chkpts, sim, dest):
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    add_faux = [faux_stop] + bus.stops_remaining
    max_possible_ix = len(add_faux)
    if (dest):
        try:
            max_possible_ix = add_faux.index(dest)
        except ValueError:
            return (None, None, None, None)
    costs_by_stop = {}
    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux[:max_possible_ix], bus.stops_remaining)):
        nxt_chk = None;
        for s in bus.stops_remaining[ix:]:
            if s.dep_t:
                nxt_chk = s
                break
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts) - cf.WAITING_TIME
        if st < 0:
            continue
        ddist, ddist_x, ddist_y = stats.check_distance(demand.o, cur_stop, next_stop)
        walk_dir = 'x' if ddist_x > ddist_y else ddist_y
        max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60)
        max_drive_dist = st * (cf.BUS_SPEED / 3600) 
        max_distance_possible = max_walk_dist + max_drive_dist 
        if ddist <= max_distance_possible:
            xdist, ydist = stats.calculate_closest_walk(demand.o, cur_stop, next_stop)
            if walk_dir == 'x':
                walk_dist = min(ddist_x, xdist) - max_drive_dist
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist,
                              demand.o.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, min(ddist_y, ydist)]))
            else:
                walk_dist = min(ddist_y, ydist) - max_drive_dist
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* np.min([max_walk_dist - walk_dist, min(ddist_x, xdist)]),
                              demand.o.xy.y + np.sign(ddist_y) * walk_dist)
            walk_arr_t = t + (np.abs(new_o.x - demand.o.xy.x) + np.abs(new_o.y - demand.o.xy.y)) / (cf.W_SPEED / 3600.)
            bus_arr_t = t + bus.hold_time + (np.abs(cur_stop.xy.x - new_o.x) + np.abs(new_o.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t <= walk_arr_t:
                pass
            else: 
                new_o_stop = stop.Stop(sim.next_stop_id, new_o, "walk", None)
                sim.next_stop_id += 1
                old_o = demand.o
                demand.o = new_o_stop
                result = stats.check_normal(demand.o, bus, t, chkpts, sim, cost_only=True, destination = dest)
                if result:
                    min_cost, temp, min_ix, min_nxt_chk = result
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
    return (min_cost, min_stop, min_ix, min_nxt_chk)

