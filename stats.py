import numpy as np
import config as cf
from shapely.geometry import Point
import stop

w1, w2, w3 = cf.WEIGHT_EXTRAMILES, cf.WEIGHT_EXTRA_PSGRT, cf.WEIGHT_EXTRA_PSGWT

def added_distance(demand, cur_stop, next_stop):
    daqx = demand.xy.x - cur_stop.xy.x 
    daqy = demand.xy.y - cur_stop.xy.y 
    dqbx = next_stop.xy.x - demand.xy.x
    dqby = next_stop.xy.y - demand.xy.y
    
    dabx = next_stop.xy.x - cur_stop.xy.x
    daby = next_stop.xy.y - cur_stop.xy.y
    #ddist = travel distance added
    ddist = np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
    return (ddist, daqx, dqbx)

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

def calculate_cost(bus, nxt_chk, ix, delta_t, ddist):
    delta_WT = 0
    for p in bus.passengers_assigned.values():
        if p.type not in {"RPD", "RPRD"}:
            continue
        try:
            oix = bus.stops_remaining.index(p.o)
        except ValueError:
            import pdb; pdb.set_trace()
        if oix < bus.stops_remaining.index(nxt_chk) and oix > ix:
            delta_WT += delta_t
    delta_RT = delta_t
    for p in list(bus.passengers_on_board.values()) + list(bus.passengers_assigned.values()):
        try:
            dix = bus.stops_remaining.index(p.d)
        except ValueError:
            import pdb; pdb.set_trace()
        try:
            oix = bus.stops_remaining.index(p.o)
        except ValueError:
            oix = 0
        if bus.stops_remaining.index(nxt_chk) >= dix and oix <= ix:
            delta_RT += delta_t
    if (ddist < 0 or delta_RT < 0 or delta_WT < 0):
        print("d " + str(ddist) + " RT " + str(delta_RT) + " WT " + str(delta_WT))
    return w1 * ddist + w2 * delta_RT + w3 * delta_WT

def check_feasible(daqx, dqbx, delta_t, st):
    feasible = True
    if (delta_t > st):
        feasible = False
    elif (daqx < 0 and np.abs(daqx) > cf.MAX_BACK):
        feasible = False
    elif (dqbx < 0 and np.abs(dqbx) > cf.MAX_BACK):
        feasible = False
    return feasible

def check_normal(demand_point, bus, t, chkpts, sim, cost_only = False, origin = None, destination = None):
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    remaining_stops = bus.stops_remaining;
    start_index = 0
    end_index = len(remaining_stops)
    if (origin):
        t_now = t - bus.start_t
        if origin.typ == "chk" and t_now > origin.dep_t:
            return None
        try:
            start_index = bus.stops_remaining.index(origin)
        except ValueError:
            start_index = -1
        if start_index == -1:
            remaining_stops = [bus.stops_visited[-1]] + bus.stops_remaining
            start_index = 0
    else:
        remaining_stops = [faux_stop] + bus.stops_remaining
        end_index = len(remaining_stops)
    if (destination):
        try:
            end_index = remaining_stops.index(destination) + 1
        except ValueError:
            return None
    min_cost = 99999999
    min_ix = None
    min_nxt_chk = None
    nxt_chk = None
    for ix, (cur_stop, next_stop) in enumerate(zip(remaining_stops[start_index:end_index], remaining_stops[start_index + 1:])):
        ddist, daqx, dqbx = added_distance(demand_point, cur_stop, next_stop)
        delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
        for s in remaining_stops[ix + 1:]:
            if s.dep_t:
                nxt_chk = s
                break
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        if (not check_feasible(daqx, dqbx, delta_t, st)):
            continue
        if (cf.ALLOW_MERGE):
            merged_stop = check_merge(ix + start_index, demand_point, cur_stop, bus, t, sim)
            if (merged_stop):
                print("MERGED || " + str(cur_stop.xy.x) + " " + str(cur_stop.xy.y)+ "," + 
                      str(demand_point.xy.x) + " " + str(demand_point.xy.y))
                return (0, merged_stop, ix + start_index, (nxt_chk, 0))
        cost = calculate_cost(bus, nxt_chk, ix + start_index, delta_t, ddist)
        if cost < min_cost:
            min_cost = cost
            min_ix = ix + start_index
            min_nxt_chk = (nxt_chk, delta_t)
    if (min_ix is None):
        return None
    else:
        if(not cost_only):
            print ("NORMAL")
        if(origin):
            min_ix += 1
        return min_cost, demand_point, min_ix, min_nxt_chk

def check_merge(index, demand_point, merge_stop, bus, t, sim):
    cur_stop = bus.stops_remaining[0];
    ddist_x = demand_point.xy.x - merge_stop.xy.x
    ddist_y = demand_point.xy.y - merge_stop.xy.y
    ddist = np.sum(np.abs([ddist_x, ddist_y]))
    max_dist = cf.W_SPEED * cf.MAX_MERGE_TIME/60
    if (ddist > max_dist):
        return None
    walk_arr_t = t + (np.abs(merge_stop.xy.x - demand_point.xy.x) + 
                      np.abs(merge_stop.xy.y - demand_point.xy.y)) / (cf.W_SPEED / 3600.)
    bus_arr_t = t + bus.hold_time + (np.abs(merge_stop.xy.x - cur_stop.xy.x) + 
                                 np.abs(merge_stop.xy.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
    if (bus_arr_t < walk_arr_t):
        return None
    new_stop = stop.Stop(sim.next_stop_id, Point(merge_stop.xy.x, merge_stop.xy.y), "merge", None)
    return new_stop