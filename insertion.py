import numpy as np

import config as cf
import stop

w1, w2, w3 = cf.WEIGHT_EXTRAMILES, cf.WEIGHT_EXTRA_PSGRT, cf.WEIGHT_EXTRA_PSGWT

def feasible(demand, bus, t, chkpts):
    if demand.type == "PD":
        return pd_feasible(demand, bus, t, chkpts)
    if demand.type == "RPD":
        return rpd_feasible(demand, bus, t, chkpts)
    if demand.type == "PRD":
        return prd_feasible(demand, bus, t, chkpts)

def pd_feasible(demand, bus, t, chkpts):
    # only feasibility condition: we havent left the origin stop
    t_now = t - bus.start_t
    if t_now < demand.o.dep_t:
        bus.passengers_assigned[demand.id] = demand
        return True
    elif t_now == demand.o.dep_t:
        bus.passengers_on_board[demand.id] = demand
        demand.pickup_t = t
        return True
    return None

def rpd_feasible(demand, bus, t, chkpts):

    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    add_faux = [faux_stop] + bus.stops_remaining
    min_cost = 99999999
    min_ix = None
    #print(add_faux)
    #print(bus.stops_remaining)
    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux, bus.stops_remaining)):
        print("-=-0-=-")
        #print(cur_stop)
        #print(next_stop)
        #print(demand.o)
        #first, check immediate insertion
        daqx = demand.o.xy.x - cur_stop.xy.x 
        daqy = demand.o.xy.y - cur_stop.xy.y 
        dqbx = next_stop.xy.x - demand.o.xy.x
        dqby = next_stop.xy.y - demand.o.xy.y
        dabx = next_stop.xy.x - cur_stop.xy.x
        daby = next_stop.xy.y - cur_stop.xy.y
        ddist = np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
        #print("ddist is {}".format(ddist))
        delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
        #print("delta_t is {}".format(delta_t))

        nxt_chk = None;
        for s in bus.stops_remaining[ix:]:
            if s.dep_t:
                nxt_chk = s
                break
        #print("ix is {}".format(ix))
        #print("nxt_chk is {}".format(nxt_chk))

        # c1 : we have enough slack time
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        #print("st is {}".format(st))
        if delta_t > st:
            continue

        # c2, c3: backtracking
        if daqx < 0 and np.abs(daqx) > cf.MAX_BACK:
            continue
        
        if dqbx < 0 and np.abs(dqbx) > cf.MAX_BACK:
            continue

        delta_WT = 0
        for p in bus.passengers_assigned.values():
            if p.type not in {"RPD", "RPRD"}:
                continue

            oix = bus.stops_remaining.index(p.o)
            if oix < bus.stops_remaining.index(nxt_chk) and oix > ix:
                print(str(p) + " must wait longer because of this assignment")
                delta_WT += delta_t

        
        #print("delta_wt is {}".format(delta_WT))
        # initialize to include this customer
        # for some reason
        delta_RT = delta_t
        for p in list(bus.passengers_on_board.values()) + list(bus.passengers_assigned.values()):
            dix = bus.stops_remaining.index(p.d)
            try:
                oix = bus.stops_remaining.index(p.o)
            except ValueError:
                oix = 0
            if bus.stops_remaining.index(nxt_chk) >= dix:
                print(str(p) + " is arriving later because of this dropoff insertion")
                delta_RT += delta_t
            if p.type in {"RPD", "RPRD"} and oix > ix and dix > bus.stops_remaining.index(nxt_chk):
                print(str(p) + " saves travel time because picked up later")
                delta_RT -= delta_t

        cost = w1 * (ddist) + w2 * delta_RT + w3 * delta_WT
        if cost < min_cost:
            min_cost = cost
            min_ix = ix

    if min_ix is not None:
        bus.passengers_assigned[demand.id] = demand
        bus.stops_remaining.insert(min_ix, demand.o)
    return min_ix

def prd_feasible(demand, bus, t, chkpts):
#    print("??? ON BOARD ???")
#    print(bus.passengers_on_board)
#    print("??? ASSIGNED ???")
#    print(bus.passengers_assigned)
#    print("??? SERVICED ???")
#    print(bus.serviced_passengers)
    t_now = t - bus.start_t
    # weve already passed this stop
    if t_now > demand.o.dep_t:
        return None
    
    try:
        earliest_ix = bus.stops_remaining.index(demand.o)
    except ValueError:
        earliest_ix = -1

    if earliest_ix == -1:
        stops_slice = [bus.stops_visited[-1]] + bus.stops_remaining
    else:
        stops_slice = bus.stops_remaining[earliest_ix:]

    #print("slice is")
    #print(stops_slice)
    min_cost = 99999999
    min_ix = None
    for ix, (cur_stop, next_stop) in enumerate(zip(stops_slice, stops_slice[1:])):
        daqx = demand.d.xy.x - cur_stop.xy.x 
        daqy = demand.d.xy.y - cur_stop.xy.y 
        dqbx = next_stop.xy.x - demand.d.xy.x
        dqby = next_stop.xy.y - demand.d.xy.y
        dabx = next_stop.xy.x - cur_stop.xy.x
        daby = next_stop.xy.y - cur_stop.xy.y
        ddist = np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
        #print("-=-=-=-")
        #print("ddist is {}".format(ddist))
        delta_t = cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
        #print("delta_t is {}".format(delta_t))

        nxt_chk = None
        for s in stops_slice[ix + 1:]:
            if s.typ == "chk":
                nxt_chk = s
                break
        #print(nxt_chk)
        #print("^^nxt_chk^^")
        # c1 : we have enough slack time
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)
        #print("st is {}".format(st))
        if delta_t > st:
            continue

        # c2, c3: backtracking
        if daqx < 0 and np.abs(daqx) > cf.MAX_BACK:
            continue
        
        if dqbx < 0 and np.abs(dqbx) > cf.MAX_BACK:
            continue
        
        delta_WT = 0
        for p in bus.passengers_assigned.values():
            if p.type not in {"RPD", "RPRD"}:
                continue

            oix = bus.stops_remaining.index(p.o)
            if oix < bus.stops_remaining.index(nxt_chk) and oix > earliest_ix + ix:
                #print(str(p) + " must wait longer because of this assignment")
                delta_WT += delta_t

        
        #print("delta_wt is {}".format(delta_WT))
        # initialize to include this customer
        # for some reason
        delta_RT = delta_t
        for p in list(bus.passengers_on_board.values()) + list(bus.passengers_assigned.values()):
            dix = bus.stops_remaining.index(p.d)
            try:
                oix = bus.stops_remaining.index(p.o)
            except ValueError:
                oix = 0
            if bus.stops_remaining.index(nxt_chk) >= dix:
                #print(str(p) + " is arriving later because of this dropoff insertion")
                delta_RT += delta_t
            if p.type in {"RPD", "RPRD"} and oix > ix + earliest_ix and dix > bus.stops_remaining.index(nxt_chk):
                #print(str(p) + " saves travel time because picked up later")
                delta_RT -= delta_t

        #print("delta_rt is {}".format(delta_RT))

        cost = w1 * (ddist) + w2 * delta_RT + w3 * delta_WT
        if cost < min_cost:
            min_cost = cost
            min_ix = ix + (1 if earliest_ix != -1 else 0)
            #print("min_ix is {}".format(min_ix))

    if min_ix is not None:
        if min_ix == 0 and earliest_ix == -1:
            bus.passengers_on_board[demand.id] = demand
            demand.pickup_t = t
        else:
            bus.passengers_assigned[demand.id] = demand
        bus.stops_remaining.insert(min_ix, demand.d)
    return min_ix

#def rprd_feasible(demand, bus, t, chkpts):
#    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
#    add_faux = [faux_stop] + bus.stops_remaining
#    min_cost = 99999999
#    min_ix = None
#    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux, add_faux[1:])):
#        daqx = demand.o.xy.x - cur_stop.xy.x 
#        daqy = demand.o.xy.y - cur_stop.xy.y 
#        dqbx = next_stop.xy.x - demand.o.xy.x
#        dqby = next_stop.xy.y - demand.o.xy.y
#        dabx = next_stop.xy.x - cur_stop.xy.x
#        daby = next_stop.xy.y - cur_stop.xy.y
#        ddist = np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
#        #print("ddist is {}".format(ddist))
#        delta_t = -cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
#        #print("delta_t is {}".format(delta_t))
#
#        nxt_chk = None;
#        for s in bus.stops_remaining[ix:]:
#            if s.dep_t:
#                nxt_chk = s
#                break
