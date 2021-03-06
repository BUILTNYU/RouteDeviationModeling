import numpy as np
from shapely.geometry import Point

import config as cf
import stop
import stats

def check_destination(demand, bus, t, chkpts, sim, o):
    #check normal
    results = stats.check_normal(demand.d, bus, t, chkpts, sim, origin = o, dem = demand)
    if (results):
        if (results[4]):
            #merge type stop
            if results[1].typ == "chk":
                sim.output.dropoff_assignment(demand.id, results[1].id, results[5], results[3][1], results[0], checkpoint = True)
            else:
                sim.output.dropoff_assignment(demand.id, results[1].id, results[5], results[3][1], results[0])
            return ("MERGE", results)
        #normal type stop
        else:
            sim.output.dropoff_assignment(demand.id, results[1].id, 0., results[3][1], results[0])
            return ("NORMAL", results)
    else:
        #check walking type stop
        if cf.ALLOW_WALKING:
            walk_dest = check_destination_walk(demand, bus, t, chkpts, sim, o)
            if (walk_dest[1]):
                sim.output.dropoff_assignment(demand.id, walk_dest[1].id, walk_dest[4], walk_dest[3][1], walk_dest[0])
                return ("WALK", walk_dest)
        return None
    
def check_destination_walk(demand, bus, t, chkpts, sim, ori):
    stops_remaining = bus.stops_remaining
    start_index = 0
    extra = 0
    
    if (ori):
        t_now = t - bus.start_t
        #check we are not past origin point
        if ori.typ == "chk" and t_now > ori.dep_t:
            return (None, None, None, None)
    for ix, s in enumerate(add_faux):
        if s.dep_t:
            if demand.o.xy.x > s.xy.x:
                end_index = ix
            else:
                break
    ix = end_index
    while ix > 0:
        ix -= 1
        if add_faux[ix].dep_t:
            start_index = ix
            if start_index == 0:
                stops_remaining = [bus.stops_visited[-1]] + bus.stops_remaining
                exta = -1
            break
        
    costs_by_stop = {}
    #methodology is identical to origin walking
    for ix, (cur_stop, next_stop) in enumerate (zip(stops_remaining[start_index:end_index-1], stops_remaining[start_index+1: end_index])):
        nxt_chk = None
        for s in stops_remaining[start_index + ix:]:
            if s.dep_t:
                nxt_chk = s
                break
        if (nxt_chk == None):
            import pdb; pdb.set_trace()
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        ddist, daqx, dqbx = stats.added_distance(demand.d, cur_stop, next_stop)
        if st < 0:
            continue
        elif (daqx < 0 and np.abs(daqx) > cf.MAX_BACK):
            continue
        elif (dqbx < 0 and np.abs(dqbx) > cf.MAX_BACK):
            continue
        ddist, ddist_x, ddist_y = stats.check_distance(demand.d, cur_stop, next_stop)
        walk_dir = 'x' if ddist_x > ddist_y else ddist_y
        max_walk_dist = stats.get_max_walk_distance(bus, demand.d, t, chkpts, sim)
        max_drive_dist = (st - cf.WAITING_TIME) * (cf.BUS_SPEED / 3600) 
        max_distance_possible = max_walk_dist * 2 + max_drive_dist 
        if ddist <= max_distance_possible:
            xdist, ydist = stats.calculate_closest_walk(demand.d, cur_stop, next_stop)
            if walk_dir == 'x':
                dist = min(ddist_x, xdist)
                walk_dist = np.sign(dist)*(np.abs(dist - max_drive_dist/2))
                new_d = Point(demand.d.xy.x +  np.sign(ddist_x)* walk_dist,
                              demand.d.xy.y + np.sign(ddist_y) * np.abs(np.min([max_walk_dist - walk_dist, min(ddist_y, ydist)])))
            else:
                dist = min(ddist_y, ydist)
                walk_dist = np.sign(dist)*(np.abs(dist - max_drive_dist/2))
                new_d = Point(demand.d.xy.x +  np.sign(ddist_x)* np.abs(np.min([max_walk_dist - walk_dist, min(ddist_x, xdist)])),
                              demand.d.xy.y + np.sign(ddist_y) * walk_dist)
            walk_arr_t = t + (np.abs(new_d.x - demand.d.xy.x) + np.abs(new_d.y - demand.d.xy.y)) / (cf.W_SPEED / 3600.)
            bus_arr_t = t + bus.hold_time + (np.abs(cur_stop.xy.x - new_d.x) + np.abs(new_d.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t > walk_arr_t:
                new_d_stop = stop.Stop(sim.next_stop_id, new_d, "walk", None)
                sim.next_stop_id += 1
                ddist, x, y = stats.added_distance(new_d_stop, cur_stop, next_stop)
                delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
                if (not stats.check_feasible(x, y, delta_t, st)):
                    continue
                min_cost = stats.calculate_cost(bus, nxt_chk, ix + start_index, delta_t, ddist)
                costs_by_stop[new_d_stop.id] =  (new_d_stop, ix + start_index + extra, min_cost, (nxt_chk, delta_t), walk_arr_t-t)

    min_ix = None
    min_stop = None
    min_nxt_chk = None
    min_cost = 9999
    min_t = None
    for k, v in costs_by_stop.items():
        if v[2] < min_cost:
            min_stop = v[0]
            min_ix = v[1]
            min_cost = v[2]
            min_nxt_chk = v[3]
            min_t = v[4]
    if (min_ix and min_ix + 1 >= len(stops_remaining)):
        import pdb; pdb.set_trace()
    if (min_stop):
        print("WALK || MAX: " + str(max_walk_dist))
    return (min_cost, min_stop, min_ix, min_nxt_chk, min_t)

        
