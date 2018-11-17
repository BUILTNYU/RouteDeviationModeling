import numpy as np
import config as cf
from shapely.geometry import Point
import stop

w1, w2, w3 = cf.WEIGHT_EXTRAMILES, cf.WEIGHT_EXTRA_PSGRT, cf.WEIGHT_EXTRA_PSGWT

#distance calculations, with distance between current stops
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

#distance calculations, with total x and y distance of path
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

#returns the closest point to the rectangle
def calculate_closest_walk(demand, cur_stop, next_stop):
    daqx = demand.xy.x - cur_stop.xy.x 
    daqy = demand.xy.y - cur_stop.xy.y 
    dqbx = next_stop.xy.x - demand.xy.x
    dqby = next_stop.xy.y - demand.xy.y
    minX = min(np.abs([daqx, dqbx]))
    minY = min(np.abs([daqy, dqby]))
    return (np.sign(dqbx) * minX, np.sign(dqby) * minY)

#calculate ride and wait time delays
def calculate_cost(bus, nxt_chk, ix, delta_t, ddist):
    delta_WT = 0
    #waittime delays
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
    #ridetime delays
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
    #weighted cost 
    return w1 * ddist + w2 * delta_RT + w3 * delta_WT

#check backtracking and slack time used
def check_feasible(daqx, dqbx, delta_t, st):
    feasible = True
    if (delta_t > st):
        feasible = False
    elif (daqx < 0 and np.abs(daqx) > cf.MAX_BACK):
        feasible = False
    elif (dqbx < 0 and np.abs(dqbx) > cf.MAX_BACK):
        feasible = False
    return feasible

#check_normal works for both origin and destination points
def check_normal(demand_point, bus, t, chkpts, sim, origin = None, destination = None, dem = None, cost_only = False):
    #addes current location as fake stop
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    # if origin is not possible, return
    if (origin):
        t_now = t - bus.start_t
        if origin.typ == "chk" and t_now > origin.dep_t:
            return None
    # Get next checkpoint as last possible stop
    remaining_stops = [faux_stop] + bus.stops_remaining
    nxt_chk = faux_stop
    start_index = 0
    end_index = 0
    for ix, s in enumerate(remaining_stops):
        if s.dep_t:
            if demand_point.xy.x > s.xy.x:
                nxt_chk = s
                end_index = ix
            else:
                break
    ix = end_index
    #Get first checkpoint if possible, current location otherwise.
    while ix > 0:
        ix -= 1
        if remaining_stops[ix].dep_t:
            start_index = ix
            break
    
    
    min_cost = 99999999
    min_ix = None
    min_nxt_chk = None
    nxt_chk = None
    min_time = cf.MAX_WALK_TIME
    time = 0
    extra_time = 0
    
    for ix, (cur_stop, next_stop) in enumerate(zip(remaining_stops[start_index:end_index], remaining_stops[start_index + 1:])):
        #get next checkpoint for slack time
        for s in remaining_stops[start_index + ix + 1:]:
            if s.dep_t:
                nxt_chk = s
                break
        ddist, daqx, dqbx = added_distance(demand_point, cur_stop, next_stop)
        delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        #if cost only, we are looking for the time until pickup
        if (cost_only):
            dabx = next_stop.xy.x - cur_stop.xy.x
            daby = next_stop.xy.y - cur_stop.xy.y
            #include hold time? -- not implemented
            extra_time =  np.sum(np.abs([dabx, daby]))/(cf.BUS_SPEED / 3600)
        #check if the stop is valid
        if (not check_feasible(daqx, dqbx, delta_t, st)):
            time += extra_time
            continue
        #check possibility of merging with nearby stop
        if (cf.ALLOW_MERGE and not cost_only and ix != 0):
            new_stop = check_merge(demand_point, cur_stop, bus, t)
            if (new_stop):
                return (0, new_stop[0], ix + start_index + extra, (nxt_chk, 0), True, new_stop[1])
        #check if this is the quickest pickup for cost only(walking)
        if (cost_only):
            if (time + delta_t < min_time):
                min_time = time + delta_t
            else:
                time += extra_time
        else:
            #calculate the cost of the stop
            cost = calculate_cost(bus, nxt_chk, ix + start_index, delta_t, ddist)
            if cost < min_cost:
                min_cost = cost
                min_ix = ix + start_index + extra
                min_nxt_chk = (nxt_chk, delta_t)
    if (cost_only):
        return min_time
    if (min_ix is None):
        return None
    else:
        return min_cost, demand_point, min_ix, min_nxt_chk, False

### depreciated ### - only one type of merge
def check_merge(demand_point, merge_stop, bus, t):
    return checkpoint_merge(demand_point, merge_stop, bus, t);
    """ FOR IF WE WANT TO MERGE STOPS TOGETHER HALFWAY
    if (merge_stop.typ == "chk"):
        return checkpoint_merge(demand_point, merge_stop, bus, t);
    else:
        return stop_merge(demand_point, merge_stop, bus, t, sim);
    """
# demand will merge into the point
def checkpoint_merge(demand_point, merge_stop, bus, t):
    cur_stop = bus.stops_remaining[0];
    ddist_x = demand_point.xy.x - merge_stop.xy.x
    ddist_y = demand_point.xy.y - merge_stop.xy.y
    ddist = np.sum(np.abs([ddist_x, ddist_y]))
    max_dist = cf.W_SPEED/60 * cf.MAX_MERGE_TIME
    if (ddist > max_dist):
        return None
    walk_arr_t = t + (np.abs(ddist_x) + np.abs(ddist_y)) / (cf.W_SPEED / 3600.)
    bus_arr_t = t + bus.hold_time + (np.abs(merge_stop.xy.x - cur_stop.xy.x) + 
                                 np.abs(merge_stop.xy.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
    if (bus_arr_t < walk_arr_t):
        return None
    return (merge_stop, walk_arr_t - t)

### DEPRECIATED ### new stop will the average between two points        
def stop_merge(demand_point, merge_stop, bus, t, sim):
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
            merge_time = abs(p.o.xy.x - new_stop.xy.x) + abs(p.o.xy.y - new_stop.xy.y)/(cf.W_SPEED / 3600.)
            sim.output.pickup_add_walktime(p.id, merge_time)
        if p.d == merge_stop:
            p.d = new_stop
            modify = True
            merge_time = abs(p.d.xy.x - new_stop.xy.x) + abs(p.d.xy.y - new_stop.xy.y)/(cf.W_SPEED / 3600.)
            sim.output.dropoff_add_walktime(p.id, merge_time)
    for p in bus.passengers_on_board.values():
        if p.d == merge_stop:
            p.d = new_stop
            modify = True
            merge_time = abs(p.d.xy.x - new_stop.xy.x) + abs(p.d.xy.y - new_stop.xy.y)/(cf.W_SPEED / 3600.)
            sim.output.dropoff_add_walktime(p.id, merge_time)
    if (not modify):
        import pdb; pdb.set_trace()
    print("MERGED FROM " + str(merge_stop.xy) + " TO " + str(new_stop.xy))
    return (new_stop, walk_arr_t - t)
    
#max walk distance based on time it takes for next bus to arrive and pickup
def get_max_walk_distance(current_bus, demand_point, t, chkpts, sim):
    min_time = cf.MAX_WALK_TIME
    #get the first stop available
    for bus in sim.active_buses[sim.active_buses.index(current_bus) + 1:]:
        #this is an best case estimate
        result = check_normal(demand_point, bus, t, chkpts, sim, cost_only = True)
        if (result < min_time):
            min_time = result
    #if it is not feasible for next bus?
    return cf.WALK_MULTIPLIER * min_time * (cf.W_SPEED / 60.) # minutes in min_tim cancel with walk_speed

#NOT sure this is used
def get_feasible_time(demand_point, bus, t, chkpts, sim):
    time = 0.
    for ix, (cur_stop, next_stop) in enumerate(zip(bus.stops_remaining, bus.stops_remaining[1:])):
        for s in bus.stops_remaining[ix + 1:]:
            if s.dep_t:
                nxt_chk = s
                break
        ddist, daqx, dqbx = added_distance(demand_point, cur_stop, next_stop)
        delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        dabx = next_stop.xy.x - cur_stop.xy.x
        daby = next_stop.xy.y - cur_stop.xy.y
        time += np.sum(np.abs([dabx, daby]))/(cf.BUS_SPEED / 3600)
        if (not check_feasible(daqx, dqbx, delta_t, st)):
            continue
        else:   #if we find a feasible point, return the time it takes for bus to get there
            return time
    return time #will be maximum time

def get_bus_arrival_time(new, bus, remaining_stops, start, end_index):
    time = bus.hold_time
    current = start
    for i in range(start + 1, end_index):
        cur_stop = remaining_stops[current]
        nxt_stop = remaining_stops[i]
        time += bus.hold_time + (np.abs(nxt_stop.xy.x - cur_stop.xy.x) + np.abs(nxt_stop.xy.y - cur_stop.xy.y))/(cf.BUS_SPEED/3600.)
        current += 1
    return time + (np.abs(new.x - remaining_stops[current].xy.x) + np.abs(new.y - remaining_stops[current].xy.y))/(cf.BUS_SPEED/3600.)
        
        
