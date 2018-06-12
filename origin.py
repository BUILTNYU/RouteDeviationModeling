import numpy as np
from shapely.geometry import Point

import config as cf
import stop
import stats

def check_origin(demand, bus, t, chkpts, sim, d):
    results = stats.check_normal(demand.o, bus, t, chkpts, sim, destination = d)
    if (results):
        if (results[4]):
            return (True, results)
        else:
            return (False, results)
    else:
        if cf.ALLOW_WALKING:
            walk_origin = check_origin_walk(demand, bus, t, chkpts, sim, d)
            if (walk_origin[1]):
                return (True, walk_origin)
        return None

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
        max_distance_possible = max_walk_dist * 2 + max_drive_dist 
        if ddist <= max_distance_possible:
            xdist, ydist = stats.calculate_closest_walk(demand.o, cur_stop, next_stop)
            if walk_dir == 'x':
                walk_dist = min(ddist_x, xdist) - max_drive_dist/2
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist,
                              demand.o.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, min(ddist_y, ydist)]))
            else:
                walk_dist = min(ddist_y, ydist) - max_drive_dist
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* np.min([max_walk_dist - walk_dist, min(ddist_x, xdist)]),
                              demand.o.xy.y + np.sign(ddist_y) * walk_dist)
            walk_arr_t = t + (np.abs(new_o.x - demand.o.xy.x) + np.abs(new_o.y - demand.o.xy.y)) / (cf.W_SPEED / 3600.)
            bus_arr_t = t + bus.hold_time + (np.abs(faux_stop.xy.x - new_o.x) + np.abs(new_o.y - faux_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t < walk_arr_t:
                pass
            else: 
                new_o_stop = stop.Stop(sim.next_stop_id, new_o, "walk", None)
                sim.next_stop_id += 1
                old_o = demand.o
                demand.o = new_o_stop
                ddist, x, y = stats.added_distance(demand.o, cur_stop, next_stop)
                delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
                if (not stats.check_feasible(x, y, delta_t, st)):
                    continue
                min_cost = stats.calculate_cost(bus, nxt_chk, ix, delta_t, ddist)
                costs_by_stop[new_o_stop.id] =  (new_o_stop, ix, min_cost, (nxt_chk, delta_t))
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
    if (min_stop):
        print("WALK || " + str(min_stop.xy.x) + "," + str(min_stop.xy.y) + "cost: " + str(min_cost))
    return (min_cost, min_stop, min_ix, min_nxt_chk)

