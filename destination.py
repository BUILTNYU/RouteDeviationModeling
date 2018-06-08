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
        if cf.ALLOW_MERGE_WALKING:
            merge_dest = check_destination_merge(demand, bus, t, chkpts, sim, o)
        if cf.ALLOW_NEW_WALKING:
            walk_dest = check_destination_walk(demand, bus, t, chkpts, sim, o)
        if (merge_dest[1] and walk_dest[1]):
            if (merge_dest[0] < walk_dest[0]):
                return (False, merge_dest)
            else:
                return (False, walk_dest)
        elif (merge_dest[1]):
            return (False, merge_dest)
        elif (walk_dest[1]):
            return (False, walk_dest)
        else:
            return None
def check_destination_merge(demand, bus, t, chkpts, sim, ori):
    start_index = 0
    if (ori):
        t_now = t - bus.start_t
        if t_now > demand.o.dep_t:
            return (None, None, None, None)
        start_index = bus.stops_remaining.index(ori)
    costs_by_stop = {}
    for index, merge_stop in enumerate(bus.stops_remaining[start_index:]):
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
        max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60)# mph * (1 hr / 60 min)
        max_distance_possible = max_walk_dist * 2
        if ddist <= max_distance_possible:
            new_d = Point(demand.d.xy.x +  np.sign(ddist_x)* ddist_x/2,
                          demand.d.xy.y + np.sign(ddist_y) * ddist_y/2)
            walk_arr_t = t + (np.abs(new_d.x - demand.d.xy.x) + np.abs(new_d.y - demand.d.xy.y)) / (cf.W_SPEED / 3600.)
            bus_arr_t = t + bus.hold_time + (np.abs(new_d.x - prev_stop.xy.x) + np.abs(new_d.y - prev_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t <= walk_arr_t:
                pass
            else:
                new_d_stop = stop.Stop(sim.next_stop_id, new_d, "walk", None)
                sim.next_stop_id += 1
                old_d = demand.d
                demand.d = new_d_stop
                result = stats.check_normal(demand.d, bus, t, chkpts, cost_only = True, origin = ori)
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
    return (min_cost, min_stop, min_ix, min_nxt_chk)

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
                result = stats.check_normal(demand.d, bus, t, chkpts, cost_only=True, origin = ori)
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
    return (min_cost, min_stop, min_ix, min_nxt_chk)

        