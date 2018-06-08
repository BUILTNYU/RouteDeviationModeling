import origin
import destination

def modify_stops(demand, bus, new_o, new_d):
    old_o = None
    old_d = None
    if (new_o):
        if(new_o[0]):
            old_o = demand.o
            demand.o = new_o[1][1]
        new_o = new_o[1]
        bus.stops_remaining.insert(new_o[2], new_o[1])
        bus.avail_slack_times[new_o[3][0].id] -= new_o[3][1]
    if (new_d):
        if (new_d[0]):
            old_d = demand.d
            demand.d = new_d[1][1]
        new_d = new_d[1]
        bus.stops_remaining.insert(new_d[2], new_d[1])
        bus.avail_slack_times[new_d[3][0].id] -= new_d[3][1]
    bus.passengers_assigned[demand.id] = demand
    return (True, old_o, old_d)

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
    if demand.type == "RPD":
        new_stop = origin.check_origin(demand, bus, t, chkpts, sim, demand.d)
        if (new_stop):
            return modify_stops(demand, bus, new_stop, None)
        return (False, None, None)
    if demand.type == "PRD":
        new_stop = destination.check_origin(demand, bus, t, chkpts, sim, demand.o)
        if (new_stop):
            t_now = t - bus.start_t
            if t_now < demand.o.dep_t:
                bus.passengers_assigned[demand.id] = demand
            elif t_now == demand.o.dep_t:
                bus.passengers_on_board[demand.id] = demand
                demand.pickup_t = t
            return modify_stops(demand, bus, None, new_stop)
        return (False, None, None)
    if demand.type == "RPRD":
        new_o = destination.check_origin(demand, bus, t, chkpts, sim, None)
        if (new_o):
            new_d = destination.check_origin(demand, bus, t, chkpts, sim, new_o[1][1])
            if (new_d):
                return modify_stops(demand, bus, new_o, new_d)
        return (False, None, None)
            