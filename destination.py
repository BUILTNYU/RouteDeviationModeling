import numpy as np
from shapely.geometry import Point

import config as cf
import stop
import stats

def check_destination(demand, bus, t, chkpts, sim, o):
    results = stats.check_normal(demand.d, bus, t, chkpts, sim, origin = o)
    if (results):
        return (True, results)
    else:
        if cf.ALLOW_WALKING:
            walk_dest = check_destination_walk(demand, bus, t, chkpts, sim, o)
            if (walk_dest[1]):
                return (False, walk_dest)

def check_destination_walk(demand, bus, t, chkpts, sim, ori):
    stops_remaining = bus.stops_remaining
    start_index = 0
    if (ori):
        t_now = t - bus.start_t
        if t_now > ori.dep_t:
            return (None, None, None, None)
        try:
            start_index = bus.stops_remaining.index(demand.o)
        except ValueError:
            start_index = -1
        if start_index == -1:
            stops_remaining = [bus.stops_visited[-1]] + bus.stops_remaining
            start_index = 0
        costs_by_stop = {}
        for ix, (cur_stop, next_stop) in enumerate (zip(stops_remaining[start_index:], stops_remaining[start_index + 1:])):
            nxt_chk = None
            for s in bus.stops_remaining[ix:]:
                if s.dep_t:
                    nxt_chk = s
                    break
            st = bus.usable_slack_time(t, nxt_chk.id, chkpts) - cf.WAITING_TIME
            if st < 0:
                continue
            ddist, ddist_x, ddist_y = stats.check_distance(demand.d, cur_stop, next_stop)
            walk_dir = 'x' if ddist_x > ddist_y else ddist_y
            max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60)
            max_drive_dist = st * (cf.BUS_SPEED / 3600) 
            max_distance_possible = max_walk_dist + max_drive_dist 
            if ddist <= max_distance_possible:
                xdist, ydist = stats.calculate_closest_walk(demand.d, cur_stop, next_stop)
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
                if bus_arr_t > walk_arr_t:
                    new_d_stop = stop.Stop(sim.next_stop_id, new_d, "walk", None)
                    sim.next_stop_id += 1
                    old_d = demand.d
                    demand.d = new_d_stop
                    result = stats.check_normal(demand.d, bus, t, chkpts, sim, cost_only=True, origin = ori)
                    if result:
                        min_cost, min_stop, min_ix, min_nxt_chk = result
                        costs_by_stop[new_d_stop.id] =  (new_d_stop, min_ix, min_cost, min_nxt_chk, bus_arr_t, walk_arr_t)
                    demand.d = old_d

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
            print("WALK || " + str(min_stop.xy.x) + ", " + str(min_stop.xy.y) + " |cost: " + str(min_cost))
    return (min_cost, min_stop, min_ix, min_nxt_chk)

        