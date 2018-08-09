import origin
import destination

#adds origin and destination into bus schedule
def add_stops(demand, bus, new_o, new_d, o_type, d_type, sim):
    old_o = None
    old_d = None
    #write to request.csv -> accepted
    sim.output.request_accepted(demand.id)
    #if walking/ merging, change demand
    if (o_type[1]):
        old_o = demand.o
        demand.o = new_o[1]
    if (d_type[1]):
        old_d = demand.d
        demand.d = new_d[1]
    #remove slack time and insert stop
    if (o_type[0]):
        bus.stops_remaining.insert(new_o[2], new_o[1])
        bus.avail_slack_times[new_o[3][0].id] -= new_o[3][1]
        if (bus.avail_slack_times[new_o[3][0].id] < 0):
            print("SLACK TIME ERROR")
        
        sim.output.imposed_delay(demand.id, new_o[1], bus, new_o[3][0], new_o[3][1])
        #print("BUS ID: " + str(bus.id) +"TIME: " + str(sim.t) + " SLACK REMAINING: " + str(bus.avail_slack_times[new_o[3][0].id]))  
    if (d_type[0]):
        index = 1
        if (new_d[2] + 1 >= len(bus.stops_remaining)):
            index = 0
            print("INDEX CORRECTION")
        #indexing correction
        bus.stops_remaining.insert(new_d[2] + index, new_d[1])
        bus.avail_slack_times[new_d[3][0].id] -= new_d[3][1]
        if (bus.avail_slack_times[new_d[3][0].id] < 0):
            print("Slack Time Error")
        #write imposed ride time and wait time delays to request.csv
        sim.output.imposed_delay(demand.id, new_d[1], bus, new_d[3][0], new_d[3][1])
        #print("BUS ID: " + str(bus.id) +"TIME: " + str(sim.t) + " SLACK REMAINING: " + str(bus.avail_slack_times[new_d[3][0].id]))
    #assign passenger for pickup and dropoff in schedule
    bus.passengers_assigned[demand.id] = demand
    #return (success/failure, origin point, destination point)
    return (True, old_o, old_d)
    
#assigns stops based on demand type.
    #returns (success/failure, display origin points, display destination point)
def insert_stop(demand, bus, t, chkpts, sim):
    #checkpoint pick up and drop off
    if demand.type == "PD":
        #check that we have not passed the checkpoint
        t_now = t - bus.start_t
        if t_now <= demand.o.dep_t: 
            sim.output.request_accepted(demand.id)
            sim.output.pickup_assignment(demand.id, demand.o.id, 0., 0., 0., checkpoint = True)
            sim.output.dropoff_assignment(demand.id, demand.d.id, 0., 0., 0., checkpoint = True)
            bus.passengers_assigned[demand.id] = demand
            return (True, None, None)
        return (False, None, None)
    #random pickup, checkpoint dropoff
    elif demand.type == "RPD":
        #check origin is valid through deviation, walking, or merging
        new_stop = origin.check_origin(demand, bus, t, chkpts, sim, demand.d)
        if (new_stop):
            #write the stops assigned to request.csv
            sim.output.dropoff_assignment(demand.id, demand.d.id, 0., 0., 0., checkpoint = True)
            #different ways of adding stops in add_stop
                #add_o = (X, Y) Y is true when the demand needs to be modified.
                               #X is true when the stop needs to be inserted into the schedule
            if (new_stop[0] == "NORMAL"):
                add_o = (True, False)
            elif (new_stop[0] == "WALK"):
                add_o = (True, True)
            else: #merge
                add_o = (False, True)
            return add_stops(demand, bus, new_stop[1], (None, None), add_o, (False, False), sim)
        return (False, None, None)
    #checkpoint pickup and random drop off
    elif demand.type == "PRD":
        #check destination is valid through deviation, walking, or merging
        new_stop = destination.check_destination(demand, bus, t, chkpts, sim, demand.o)
        if(new_stop):
            #write the stops assigned to request.csv
            sim.output.pickup_assignment(demand.id, demand.o.id, 0., 0., 0., checkpoint = True)
            #different ways of adding stops
            if (new_stop[0] == "NORMAL"):
                add_d = (True, False)
            elif (new_stop[0] == "WALK"):
                add_d = (True, True)
            else: #merge
                add_d = (False, True)
            return add_stops(demand, bus, (None,None), new_stop[1], (False, False), add_d, sim)
        return (False, None, None)
    #random pickup and drop off
    elif demand.type == "RPRD":
        #fake destination to find possible origin
        old_d = demand.d
        demand.d = chkpts[-1]
        #subsitute the destination temporarily to find origin
        for stop in chkpts[1:]:
            if stop.xy.x > demand.d.xy.x:
                demand.d = stop
        #find origin stop
        new_o = origin.check_origin(demand, bus, t, chkpts, sim, demand.d)
        #revert destination changes
        demand.d = old_d
        if (new_o):
            #add the origin found temporarily to help find destination
            bus.stops_remaining.insert(new_o[1][2], new_o[1][1])
            old_o = demand.o
            demand.o = new_o[1][1]
            #temporarily subtract the slack times to account for lost time
            bus.avail_slack_times[new_o[1][3][0].id] -= new_o[1][3][1]
            #find destination stop
            new_d = destination.check_destination(demand, bus, t, chkpts, sim, new_o[1][1])
            #revert temporary changes
            bus.stops_remaining.remove(new_o[1][1])
            demand.o = old_o
            bus.avail_slack_times[new_o[1][3][0].id] += new_o[1][3][1]
            #if both destination and origin are valid at this point, add to schedule
            if (new_d):
                if (new_o[0] == "NORMAL"):
                    add_o = (True, False)
                elif (new_o[0] == "WALK"):
                    add_o = (True, True)
                else: #merge
                    add_o = (False, True)
                if (new_d[0] == "NORMAL"):
                    add_d = (True, False)
                elif (new_d[0] == "WALK"):
                    add_d = (True, True)
                else: #merge
                    add_d = (False, True)
                return add_stops(demand, bus, new_o[1], new_d[1], add_o, add_d, sim)
        #(succesfully added point, new point for origin visual, new point of destingation visual)
        return (False, None, None)
            