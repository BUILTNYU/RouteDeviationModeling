import numpy as np
from shapely.geometry import Point

import config as cf
import insertion as ins
import stop

#merge walking:
    #we want to merge and infeasible stop with a feasible stop to make both feasible
def check_merge_walking(demand, bus, t, chkpts, sim):
    if demand.type == "PD":
        return None

    if demand.type == "RPD":
        return rpd_merge_walk(demand, bus, t, chkpts, sim)
    if demand.type == "PRD":
        return prd_merge_walk(demand, bus, t, chkpts, sim)
    if demand.type == "RPRD":
        return rprd_merge_walk(demand, bus, t, chkpts, sim)
    
def rpd_merge_walk(demand, bus, t, chkpts, sim):
    #when we are merging stops together we do not want to merge with the faux stop.
    try:
        #finds the last index where the demand is
        max_possible_ix = bus.stops_remaining.index(demand.d)
    # weve already passed their checkpoint, not possible
    except ValueError:
        return None
    
    costs_by_stop = {}
    #check all other stops as candidates for merging
    for index, merge_stop in enumerate(bus.stops_remaining[:max_possible_ix]):
        if (index == 0):
            # if it is the first stop, then treat the current location as the previous stop
            prev_stop = stop.Stop(-1, bus.cur_xy, "fake", None)
        else:
            prev_stop = bus.stops_remaining[index-1]
            
        nxt_chk = None
        for s in bus.stops_remaining[index:]:
            if s.dep_t:
                nxt_chk = s
                break
        st = bus.usable_slack_time(t, nxt_chk.id, chkpts) - cf.WAITING_TIME
        if st < 0:
            continue
        
        ddist_x = demand.o.xy.x - merge_stop.xy.x
        ddist_y = demand.o.xy.y - merge_stop.xy.y
        ddist = np.sum(np.abs([ddist_x, ddist_y]))
        
        # initial walk direction - pick the shortest walking direction
        max_walk_dist = cf.W_SPEED * (cf.MAX_WALK_TIME / 60) # mph * (1 hr / 60 min)
        
        max_distance_possible = max_walk_dist * 2 #Furthest two stops may be brought together.
        if ddist > max_distance_possible:
            pass
        else:
            new_o = Point(demand.o.xy.x +  np.sign(ddist_x)* ddist_x/2,
                          demand.o.xy.y + np.sign(ddist_y) * ddist_y/2)
            walk_arr_t = t + (np.abs(new_o.x - demand.o.xy.x) + np.abs(new_o.y - demand.o.xy.y)) / (cf.W_SPEED / 3600.)
            bus_arr_t = t + bus.hold_time + (np.abs(new_o.x - prev_stop.xy.x) + np.abs(new_o.y - prev_stop.xy.y)) / (cf.BUS_SPEED / 3600.)
            if bus_arr_t <= walk_arr_t:
                pass
            else:
                new_o_stop = stop.Stop(sim.next_stop_id, new_o, "walk", None)
                sim.next_stop_id += 1
                old_o = demand.o
                demand.o = new_o_stop
                result = ins.feasible(demand, bus, t, chkpts, cost_only = True)
                if result:
                    min_ix, min_cost, min_nxt_chk = result
                    costs_by_stop[new_o_stop.id] =  (new_o_stop, min_ix, min_cost, min_nxt_chk, bus_arr_t, walk_arr_t)
                demand.o = old_o
    min_ix = None
    min_stop = None
    min_nxt_chk = None
    min_cost = 9999
    for k, v in costs_by_stop.items():
        if v[2] < min_cost:
            min_stop = v[0]
            min_ix = v[1]
            min_cost = v[2]
            min_nxt_chk = v[3]
            #make sure it was feasible
            print("MERGE || Bus Time: " + str(v[4]) + ", Walk Time: " + str(v[5]))

    return (min_cost, min_stop, min_ix, min_nxt_chk)

def prd_merge_walk(demand, bus, t, chkpts, sim):
    pass
def rprd_merge_walk(demand, bus, t, chkpts, sim):
    pass