import origin
import destination

def modify_stops(demand, bus, new_o, new_d):
    old_o = None
    old_d = None
    if (new_o[1]):
        old_o = demand.o
        demand.o = new_o[1][1]
        bus.stops_remaining.insert(new_o[1][2], new_o[1][1])
        bus.avail_slack_times[new_o[1][3][0].id] -= new_o[1][3][1]
    if (new_d[1]):
        old_d = demand.d
        demand.d = new_d[1][1]
        if (new_d[1][2] + 1 >= len(bus.stops_remaining)):
            import pdb; pdb.set_trace()
        #indexing correction
        index = 1
        bus.stops_remaining.insert(new_d[1][2] + index, new_d[1][1])
        bus.avail_slack_times[new_d[1][3][0].id] -= new_d[1][3][1]
    bus.passengers_assigned[demand.id] = demand
    if (new_o[0] and new_d[0]):
        return (True, old_o, old_d)
    elif (new_o[0] and not new_d[0]):
        return (True, old_o, None)
    elif (not new_o[0] and new_d[0]):
        return (True, None, old_d)
    else:
        return (True, None, None)
    
def insert_stop(demand, bus, t, chkpts, sim):
    if demand.type == "PD":
        t_now = t - bus.start_t
        if t_now < demand.o.dep_t:
            bus.passengers_assigned[demand.id] = demand
            return (True, None, None)
        elif t_now == demand.o.dep_t:
            bus.passengers_on_board[demand.id] = demand
            demand.pickup_t = t
            return (True, None, None)
        return (False, None, None)
    elif demand.type == "RPD":
        new_stop = origin.check_origin(demand, bus, t, chkpts, sim, demand.d)
        if (new_stop):
            return modify_stops(demand, bus, new_stop, (None, None))
        return (False, None, None)
    elif demand.type == "PRD":
        new_stop = destination.check_destination(demand, bus, t, chkpts, sim, demand.o)
        if(new_stop):
            return modify_stops(demand, bus, (None,None), new_stop)
        return (False, None, None)
    elif demand.type == "RPRD":
        old_d = demand.d
        demand.d = chkpts[-1]
        #subsitute the destination temporarily to find origin
        for stop in chkpts[1:]:
            if stop.xy.x > demand.d.xy.x:
                demand.d = stop
        new_o = origin.check_origin(demand, bus, t, chkpts, sim, demand.d)
        demand.d = old_d
        if (new_o):
            #add the origin found temporarily to help find destination
            bus.stops_remaining.insert(new_o[1][2], new_o[1][1])
            new_d = destination.check_destination(demand, bus, t, chkpts, sim, new_o[1][1], rprd = True)
            bus.stops_remaining.remove(new_o[1][1])
            if (new_d):
                return modify_stops(demand, bus, new_o, new_d)
        #(succesfully added point, new point for origin visual, new point of destingation visual)
        return (False, None, None)
            