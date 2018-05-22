import numpy as np

import config as cf
import stop

w1, w2, w3 = cf.WEIGHT_EXTRAMILES, cf.WEIGHT_EXTRA_PSGRT, cf.WEIGHT_EXTRA_PSGWT


# NOTE: all functions in this file set state.

def feasible(demand, bus, t, chkpts, cost_only=False):
    if demand.type == "PD":
        return pd_feasible(demand, bus, t, chkpts)
    if demand.type == "RPD":
        return rpd_feasible(demand, bus, t, chkpts, cost_only=cost_only)
    if demand.type == "PRD":
        return prd_feasible(demand, bus, t, chkpts)
    if demand.type == "RPRD":
        return rprd_feasible(demand, bus, t, chkpts)

def pd_feasible(demand, bus, t, chkpts):
    # only feasibility condition: we havent left the origin stop
    # for this demand
    t_now = t - bus.start_t
    if t_now < demand.o.dep_t:
        bus.passengers_assigned[demand.id] = demand
        return True
    elif t_now == demand.o.dep_t:
        bus.passengers_on_board[demand.id] = demand
        demand.pickup_t = t
        return True
    return None

def rpd_feasible(demand, bus, t, chkpts, cost_only=False):

    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    add_faux = [faux_stop] + bus.stops_remaining
    try:
        max_possible_ix = add_faux.index(demand.d)
    # weve already passed their checkpoint, not possible
    except ValueError:
        return None

    min_cost = 99999999
    min_ix = None
    min_nxt_chk = None
    #print(add_faux)
    #print(bus.stops_remaining)
    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux[:max_possible_ix], bus.stops_remaining)):
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
                #print(str(p) + " must wait longer because of this assignment")
                delta_WT += delta_t

        
        #print("delta_wt is {}".format(delta_WT))
        # initialize to include this customer
        # for some reason
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
            if bus.stops_remaining.index(nxt_chk) >= dix:
                #print(str(p) + " is arriving later because of this dropoff insertion")
                delta_RT += delta_t
            if p.type in {"RPD", "RPRD"} and oix > ix and dix > bus.stops_remaining.index(nxt_chk):
                #print(str(p) + " saves travel time because picked up later")
                delta_RT -= delta_t

        cost = w1 * (ddist) + w2 * delta_RT + w3 * delta_WT
        if cost < min_cost:
            min_cost = cost
            min_ix = ix
            min_nxt_chk = (nxt_chk, delta_t)

    if min_ix is not None and not cost_only:
        bus.passengers_assigned[demand.id] = demand
        bus.stops_remaining.insert(min_ix, demand.o)
        bus.avail_slack_times[min_nxt_chk[0].id] -= min_nxt_chk[1]
        #print("bus {} has st {} before {}".format(bus.id, bus.avail_slack_times[min_nxt_chk[0].id], min_nxt_chk[0].id))
        #print("stops remaining is {}".format(bus.stops_remaining))
    elif min_ix is None:
        return None

    return min_ix, min_cost, min_nxt_chk

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
    min_nxt_chk = None
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
            min_ix = ix + ((1 + earliest_ix) if earliest_ix != -1 else 0)
            #print("min_ix is {}".format(min_ix))
            min_nxt_chk = (nxt_chk, delta_t)

    if min_ix is not None:
#        if demand.id == 9:
#            import pdb; pdb.set_trace()
        if earliest_ix == -1:
            bus.passengers_on_board[demand.id] = demand
            demand.pickup_t = t
        else:
            bus.passengers_assigned[demand.id] = demand
        bus.stops_remaining.insert(min_ix, demand.d)
        bus.avail_slack_times[min_nxt_chk[0].id] -= min_nxt_chk[1]
        #print("bus {} has st {} before {}".format(bus.id, bus.avail_slack_times[min_nxt_chk[0].id], min_nxt_chk[0].id))
        #print("stops remaining is {}".format(bus.stops_remaining))
    return min_ix

def rprd_feasible(demand, bus, t, chkpts):
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    add_faux = [faux_stop] + bus.stops_remaining
    min_cost = 99999999
    min_indices = None
    min_chks = None
    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux, add_faux[1:])):
        daqx = demand.o.xy.x - cur_stop.xy.x 
        daqy = demand.o.xy.y - cur_stop.xy.y 
        dqbx = next_stop.xy.x - demand.o.xy.x
        dqby = next_stop.xy.y - demand.o.xy.y
        dabx = next_stop.xy.x - cur_stop.xy.x
        daby = next_stop.xy.y - cur_stop.xy.y
        ddist = np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
        #print("ddist is {}".format(ddist))
        delta_t = -cf.WAITING_TIME + ddist / (cf.BUS_SPEED / 3600)
        #print("delta_t is {}".format(delta_t))

        nxt_chk = None
        for s in bus.stops_remaining[ix:]:
            if s.dep_t:
                nxt_chk = s
                break
        prv_chk = chkpts[nxt_chk.id - 1]

        st = bus.usable_slack_time(t, nxt_chk.id, chkpts)

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
                #print(str(p) + " must wait longer because of this assignment")
                delta_WT += delta_t

        
        #print("delta_wt is {}".format(delta_WT))
        # initialize to include this customer
        # for some reason
        delta_RT = delta_t
        for p in list(bus.passengers_on_board.values()) + list(bus.passengers_assigned.values()):
            try:
                dix = bus.stops_remaining.index(p.d)
            except:
                import pdb; pdb.set_trace()
            try:
                oix = bus.stops_remaining.index(p.o)
            except ValueError:
                oix = 0
            if bus.stops_remaining.index(nxt_chk) >= dix:
                #print(str(p) + " is arriving later because of this dropoff insertion")
                delta_RT += delta_t
            if p.type in {"RPD", "RPRD"} and oix > ix and dix > bus.stops_remaining.index(nxt_chk):
                #print(str(p) + " saves travel time because picked up later")
                delta_RT -= delta_t

        outer_cost = w1 * (ddist) + w2 * delta_RT + w3 * delta_WT

        potential_dests = [demand.o] + bus.stops_remaining[ix:]
        for ix2, (cur_2, next_2) in enumerate(zip(potential_dests, potential_dests[1:])):
            daqx_2 = demand.d.xy.x - cur_2.xy.x 
            daqy_2 = demand.d.xy.y - cur_2.xy.y 
            dqbx_2 = next_2.xy.x - demand.d.xy.x
            dqby_2 = next_2.xy.y - demand.d.xy.y
            dabx_2 = next_2.xy.x - cur_2.xy.x
            daby_2 = next_2.xy.y - cur_2.xy.y
            ddist_2 = np.sum(np.abs([daqx_2, daqy_2, dqbx_2, dqby_2])) - np.sum(np.abs([dabx_2, daby_2]))
            #print("-=-=-=-")
            #print("ddist is {}".format(ddist))
            delta_t_2 = cf.WAITING_TIME + ddist_2 / (cf.BUS_SPEED / 3600)
            #print("delta_t is {}".format(delta_t))

            nxt_chk_2 = None
            for s in potential_dests[ix2 + 1:]:
                if s.typ == "chk":
                    nxt_chk_2 = s
                    break
            if nxt_chk_2 == nxt_chk:
                st2 = st - delta_t
            else:
                st2 = bus.usable_slack_time(t, nxt_chk_2.id, chkpts)
            
            if delta_t_2 > st2:
                continue

            # c2, c3: backtracking
            if daqx_2 < 0 and np.abs(daqx_2) > cf.MAX_BACK:
                continue
            
            if dqbx_2 < 0 and np.abs(dqbx_2) > cf.MAX_BACK:
                continue

            delta_WT_2 = 0
            for p in bus.passengers_assigned.values():
                if p.type not in {"RPD", "RPRD"}:
                    continue

                oix = bus.stops_remaining.index(p.o)
                if oix < bus.stops_remaining.index(nxt_chk) and oix > ix2 + ix:
                    #print(str(p) + " must wait longer because of this assignment")
                    delta_WT_2 += delta_t_2

            
            #print("delta_wt is {}".format(delta_WT))
            # initialize to include this customer
            # for some reason
            delta_RT_2 = delta_t_2
            for p in list(bus.passengers_on_board.values()) + list(bus.passengers_assigned.values()):
                dix = bus.stops_remaining.index(p.d)
                try:
                    oix = bus.stops_remaining.index(p.o)
                except ValueError:
                    oix = 0
                if bus.stops_remaining.index(nxt_chk) >= dix:
                    #print(str(p) + " is arriving later because of this dropoff insertion")
                    delta_RT_2 += delta_t_2
                if p.type in {"RPD", "RPRD"} and oix > ix2 + ix and dix > bus.stops_remaining.index(nxt_chk):
                    #print(str(p) + " saves travel time because picked up later")
                    delta_RT_2 -= delta_t_2

            #print("delta_rt is {}".format(delta_RT))

            inner_cost = w1 * (ddist) + w2 * delta_RT + w3 * delta_WT
            total_cost = outer_cost + inner_cost
            if total_cost < min_cost:
                min_cost = total_cost
                min_indices = (ix, ix2)
                min_chks = (nxt_chk, delta_t, nxt_chk_2, delta_t_2)
    
    if min_indices is not None:
        ix1, ix2 = min_indices
        bus.passengers_assigned[demand.id] = demand
        bus.stops_remaining.insert(ix1 + ix2, demand.d)
        bus.stops_remaining.insert(ix1, demand.o)
        bus.avail_slack_times[min_chks[0].id] -= min_chks[1]
        bus.avail_slack_times[min_chks[2].id] -= min_chks[3]
        #print("bus {} has st {} before {}".format(bus.id, bus.avail_slack_times[min_chks[0].id], min_chks[0].id))
        #print("bus {} has st {} before {}".format(bus.id, bus.avail_slack_times[min_chks[2].id], min_chks[2].id))
        #print("stops remaining is {}".format(bus.stops_remaining))

    return min_indices
