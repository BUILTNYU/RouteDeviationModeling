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
        bus.stops_remaining.insert(new_d[1][2] + 1, new_d[1][1])
        bus.avail_slack_times[new_d[1][3][0].id] -= new_d[1][3][1]
    bus.passengers_assigned[demand.id] = demand
    if (new_o[0] and new_d[0]):
        return (True, old_o, old_d)
    elif (new_o[0] and not new_d[0]):
        return (True, old_o, None)
    elif (not new_o[0] and new_d[0]):
        return (True, None, old_d)
    else:
        return (False, None, None)
    

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
            print(str(demand.id) + " " + str(new_stop[1][0]))
            return modify_stops(demand, bus, new_stop, (None, None))
        return (False, None, None)
    elif demand.type == "PRD":
        new_stop = destination.check_destination(demand, bus, t, chkpts, sim, demand.o)
        if(new_stop):
            return modify_stops(demand, bus, (None,None), new_stop)
        return (False, None, None)
    elif demand.type == "RPRD":
        old_d = demand.d
        for stop in chkpts:
            if stop.xy.x > demand.d.xy.x:
                demand.d = stop
        new_o = origin.check_origin(demand, bus, t, chkpts, sim, demand.d)
        if (new_o):
            demand.d = old_d
            bus.stops_remaining.insert(new_o[1][2], new_o[1][1])
            new_d = destination.check_destination(demand, bus, t, chkpts, sim, new_o[1][1])
            bus.stops_remaining.remove(new_o[1][1])
            if (new_d):
                return modify_stops(demand, bus, new_o, new_d)
            
        return (False, None, None)
            