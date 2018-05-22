import numpy as np
from shapely.geometry import Point

import config as cf
import insertion as ins
import stop

def check_walking(demand, bus, t, chkpts, sim):
    if demand.type == "PD":
        return None

    if demand.type == "RPD":
        return rpd_walk(demand, bus, t, chkpts, sim)
    if demand.type == "PRD":
        return prd_feasible(demand, bus, t, chkpts)
    if demand.type == "RPRD":
        return rprd_feasible(demand, bus, t, chkpts)


def rpd_walk(demand, bus, t, chkpts, sim):
    faux_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
    add_faux = [faux_stop] + bus.stops_remaining
    try:
        max_possible_ix = add_faux.index(demand.d)
    # weve already passed their checkpoint, not possible
    except ValueError:
        return None

    costs_by_stop = {}
    for ix, (cur_stop, next_stop) in enumerate(zip(add_faux[:max_possible_ix], bus.stops_remaining)):

        nxt_chk = None;
        for s in bus.stops_remaining[ix:]:
            if s.dep_t:
                nxt_chk = s
                break
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts) - cf.WAITING_TIME
        if st < 0:
            continue
        daqx = demand.o.xy.x - cur_stop.xy.x 
        daqy = demand.o.xy.y - cur_stop.xy.y 
        dqbx = next_stop.xy.x - demand.o.xy.x
        dqby = next_stop.xy.y - demand.o.xy.y
        dabx = next_stop.xy.x - cur_stop.xy.x
        daby = next_stop.xy.y - cur_stop.xy.y
        ddist = np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
        ddist_x = np.sum(np.abs([daqx, dqbx])) - np.abs(dabx)
        ddist_y = np.sum(np.abs([daqy, dqby])) - np.abs(daby)

        # initial walk direction
        walk_dir = 'x' if ddist_x > ddist_y else ddist_y
        max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60) # mph * (1 hr / 60 min)
        max_drive_dist = st * (cf.BUS_SPEED / 3600)
        # make sure we can actually cover the distance
        if 2 * max_walk_dist  + max_drive_dist < ddist:
            print("max walk dist in {} mins is {}".format(cf.MAX_WALK_TIME, max_walk_dist))
            print("max drive dist is {}".format(max_drive_dist))
            print("ddist is {}".format(ddist))
            continue

        if walk_dir == 'x':
            walk_dist = np.min([ddist_x, max_walk_dist])
            if walk_dist < max_walk_dist and ddist_y > 0:
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist,
                              demand.o.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, ddist_y]))
            else:
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist, demand.o.xy.y)
        else:
            walk_dist = np.min([ddist_y, max_walk_dist])
            if walk_dist < max_walk_dist and ddist_x > 0:
                new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* walk_dist,
                              demand.o.xy.y + np.sign(ddist_y) * np.min([max_walk_dist - walk_dist, ddist_y]))
            else:
                new_o = Point(demand.o.xy.x,
                              np.sign(ddist_y)* walk_dist +  demand.o.xy.y)

        #TODO: make sure that the walker arrives before the bus
        walk_arr_t = t + (np.abs(new_o.x - demand.o.xy.x) + np.abs(new_o.y - demand.o.xy.y)) / (cf.W_SPEED / 3600.)
        bus_arr_t = t + (np.abs(cur_stop.xy.x - new_o.x) + np.abs(new_o.y - cur_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
        if bus_arr_t <= walk_arr_t:
            print(bus_arr_t)
            print(walk_arr_t)
            print("doesnt work")
            continue


        new_o_stop = stop.Stop(sim.next_stop_id, new_o, "walk", None)
        old_o = demand.o
        demand.o = new_o_stop
        min_ix, min_cost, min_nxt_chk = ins.feasible(demand, bus, t, chkpts, cost_only=True)
        demand.o = old_o
        costs_by_stop[new_o_stop] =  (min_ix, min_cost, min_nxt_chk)

    min_ix = None
    min_stop = None
    min_nxt_chk = None
    min_cost = 99999
    for k, v in costs_by_stop.items():
        if v[1] < min_cost:
            min_cost = v[1]
            min_ix = v[0]
            min_nxt_chk = v[2]
            min_stop = k

    if min_stop:
        demand.o = min_stop
        bus.stops_remaining.insert(min_ix, min_stop)
        bus.avail_slack_times[min_nxt_chk[0]] -= min_nxt_chk[1]
        bus.passengers_assigned.append(demand)

    sim.next_stop_id += 1
    return min_stop
