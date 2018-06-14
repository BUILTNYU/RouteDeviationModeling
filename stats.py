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
    minX = min(np.abs([daqx, dqbx]))
    minY = min(np.abs([daqy, dqby]))
    return (np.sign(dqbx) * minX, np.sign(dqby) * minY)

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
    for p in list(bus.passengers_on_board.values()):
        try:
            dix = bus.stops_remaining.index(p.d)
        except ValueError:
            import pdb; pdb.set_trace()
        try:
            oix = bus.stops_remaining.index(p.o)
        except ValueError:
            oix = 0
        if bus.stops_remaining.index(nxt_chk) >= dix:
            delta_RT += delta_t
        #delete subtraction part
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

def check_normal(demand_point, bus, t, chkpts, sim, cost_only = False, origin = None, destination = None, d = None):
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    remaining_stops = bus.stops_remaining;
    start_index = 0
    end_index = len(remaining_stops)
    extra = 0
    
    time = 0    # to calculate walk dist in cost_only
    min_time = 0
    
    #get start_index of earliest stop
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
            start_index= 0
            #to compensate for adding the stop. Results in index errors otherwise
            extra = -1
    else:
        remaining_stops = [faux_stop] + bus.stops_remaining
        end_index = len(remaining_stops) - 1
    if (destination):
        try:
            end_index = remaining_stops.index(destination) - 1
        except ValueError:
            return None
    min_cost = 99999999
    min_ix = None
    min_nxt_chk = None
    nxt_chk = None
    for ix, (cur_stop, next_stop) in enumerate(zip(remaining_stops[start_index:end_index], remaining_stops[start_index + 1:])):
        for s in remaining_stops[ix + 1:]:
            if s.dep_t:
                nxt_chk = s
                break
        ddist, daqx, dqbx = added_distance(demand_point, cur_stop, next_stop)
        delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        if (not check_feasible(daqx, dqbx, delta_t, st)):
            continue
        if (cf.ALLOW_MERGE and not cost_only and ix != 0):
            new_stop = check_merge(demand_point, cur_stop, bus, t)
            if (new_stop):
                print("MERGE")
                return (0, new_stop, ix + start_index + extra, (nxt_chk, 0), True)
        cost = calculate_cost(bus, nxt_chk, ix + start_index, delta_t, ddist)
        if (cost_only):
             dabx = next_stop.xy.x - cur_stop.xy.x
             daby = next_stop.xy.y - cur_stop.xy.y
             time += np.sum(np.abs([dabx, daby]))/(cf.BUS_SPEED / 3600)
        if cost < min_cost:
            min_cost = cost
            min_ix = ix + start_index + extra
            min_nxt_chk = (nxt_chk, delta_t)
            min_time = time
            if (min_ix + 1>= len(bus.stops_remaining)):
                import pdb; pdb.set_trace()
    if (min_ix is None):
        return None
    else:
        if (cost_only):
            return min_time
        else:
            return min_cost, demand_point, min_ix, min_nxt_chk, False

def check_merge(demand_point, merge_stop, bus, t):
    #return checkpoint_merge(demand_point, merge_stop, bus, t);
    if (merge_stop.typ == "chk"):
        return checkpoint_merge(demand_point, merge_stop, bus, t);
    else:
        return stop_merge(demand_point, merge_stop, bus, t);
    

def checkpoint_merge(demand_point, merge_stop, bus, t):
    cur_stop = bus.stops_remaining[0];
    ddist_x = demand_point.xy.x - merge_stop.xy.x
    ddist_y = demand_point.xy.y - merge_stop.xy.y
    ddist = np.sum(np.abs([ddist_x, ddist_y]))
    max_dist = cf.W_SPEED * cf.MAX_MERGE_TIME/60
    if (ddist > max_dist):
        return None
    walk_arr_t = t + (np.abs(ddist_x) + np.abs(ddist_y)) / (cf.W_SPEED / 3600.)
    bus_arr_t = t + bus.hold_time + (np.abs(merge_stop.xy.x - cur_stop.xy.x) + 
                                 np.abs(merge_stop.xy.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
    if (bus_arr_t < walk_arr_t):
        return None
    return merge_stop

def stop_merge(demand_point, merge_stop, bus, t):
    cur_stop = bus.stops_remaining[0];
    ddist_x = (merge_stop.xy.x - demand_point.xy.x)/2
    ddist_y = (merge_stop.xy.y - demand_point.xy.y)/2
    ddist = np.sum(np.abs([ddist_x, ddist_y]))
    max_dist = cf.W_SPEED * 2 * cf.MAX_MERGE_TIME/60
    if (ddist > max_dist):
        return None
    walk_arr_t = t + (np.abs(ddist_x) + np.abs(ddist_y)) / (cf.W_SPEED / 3600.)
    bus_arr_t = t + bus.hold_time + (np.abs(merge_stop.xy.x - cur_stop.xy.x) + 
                                 np.abs(merge_stop.xy.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
    if (bus_arr_t < walk_arr_t):
        return None
    
    new_stop = stop.Stop(merge_stop.id, Point(demand_point.xy.x + ddist_x, demand_point.xy.y + ddist_y), "merge", None)
    modify = False
    bus.stops_remaining[bus.stops_remaining.index(merge_stop)] = new_stop
    for p in bus.passengers_assigned.values():
        if p.o == merge_stop:
            p.o = new_stop
            modify = True
        if p.d == merge_stop:
            p.d = new_stop
            modify = True
    for p in bus.passengers_on_board.values():
        if p.d == merge_stop:
            p.d = new_stop
            modify = True
    if (not modify):
        import pdb; pdb.set_trace()
    print("MERGED FROM " + str(merge_stop.xy) + " TO " + str(new_stop.xy))
    return new_stop
    
def get_max_walk_distance(current_bus, demand_point, t, chkpts, sim):
    #TO DO: get current location?
    min_time = cf.MAX_WALK_TIME
    #get the first stop available
    for bus in sim.active_buses[sim.active_buses.index(current_bus) + 1:]:
        result = check_normal(demand_point, bus, t, chkpts, cost_only = True);
        if (result and result < min_time):
            min_time = result
    #if it is not feasible for next bus?
    return min_time