import csv
import config as cf

class record_stats(object):
    def __init__(self, file_num):
        end = str(file_num) + '.csv'
        self.output1 = open(cf.OUTPUT_REQUEST + end, "w", newline = '')
        self.request = csv.writer(self.output1, delimiter = ",")
        
        self.output2 = open(cf.OUTPUT_NODE + end, "w", newline = '')
        self.node = csv.writer(self.output2, delimiter = ",")
        
        self.output3 = open(cf.OUTPUT_BUS + end, "w", newline = '')
        self.bus = csv.writer(self.output3, delimiter = ",")
        
        self.request_rows = {}
        self.request_origin = {}
        self.request_destination = {}
    
        self.write_headers()
        
        self.p_extra_RT = {}         #(imposed RT)
        self.p_extra_WT = {}
        self.p_delay_RT = {}         #(delayed RT)
        self.p_delay_WT = {}
        
    def write_headers(self):
        self.request.writerow(["REQUEST ID", "TIME OF REQUEST", "REQUEST TYPE", "ODEMAND X", "ODEMAND Y", "DDEMAND X", "DDEMAND Y", "ACCEPTED/REJECTED",
                               "PICKUP ID", "PICKUP X", "PICKUP Y", "INITIAL WT", "EXTRA WT", "P WALK TIME", "DELTA_T", "COST", "EXTRA MILAGE",
                               "DROPOFF ID", "DROPOFF X", "DROPOFF Y", "INITIAL RT", "EXTRA RT", "D WALK TIME", "DELTA_T", "COST" , "EXTRA MILAGE",
                               "IMPOSED WT", "IMPOSED RT"])
        self.bus.writerow(["BUS ID", "STOP ID", "REQUEST ID", "REQUEST TYPE", "TIME OF ARRIVAL", "XCOORD", "YCOORD"])
        self.node.writerow(["STOP ID", "X-COORDINATE", "Y-COORDINATE", "STOP TYPE"])
        
    def write_node(self, num, x, y, stop_type):
        #node id, x coord, y coord
        self.node.writerow([num, x, y, stop_type])
        
    def write_bus(self, num, node_num, request_num, request_type, time, x, y):
        #bus id, node id, request id, request type, time of arrival at stop
        self.bus.writerow([num, node_num, request_num, request_type, time, x, y])
        
    #IN PASSGENERS.PY - MAY HAVE TO EXPAND TO TESTS
    def request_creation(self, request_num, request_time, request_type, origin, dest):
        #Request id, time of request, request type, demand origin, demand destinatino, accepted/rejected
        self.request_rows[request_num] = (request_num, request_time, request_type, origin.xy.x, origin.xy.y, dest.xy.x, dest.xy.y, False)
        
    #IN ADD_STOP.ADDSTOP()
    def request_accepted(self, request_num):
        r = self.request_rows[request_num]
        self.request_rows[request_num] = (r[0], r[1], r[2], r[3], r[4], r[5], r[6], True)
        self.p_extra_RT[request_num] = 0
        self.p_extra_WT[request_num] = 0
        self.p_delay_RT[request_num] = 0
        self.p_delay_WT[request_num] = 0
        
    #IN ADD_STOP.ADDSTOP()
    def imposed_delay(self, request_num, stop, bus, next_chk, delta_t):
        after = False
        upcoming_stops = []
        for s in bus.stops_remaining:
            if not after:
                if s == stop:
                    after = True
            else:
                if s == next_chk:
                    upcoming_stops.append(s)
                    break
                upcoming_stops.append(s)
        for passenger in bus.passengers_assigned.values():
            if passenger.o in upcoming_stops:
                self.p_extra_WT[request_num] += delta_t
                self.p_delay_WT[passenger.id] += delta_t
        for passenger in bus.passengers_on_board.values():
            if passenger.d in upcoming_stops:
                self.p_extra_RT[request_num] += delta_t
                self.p_delay_RT[passenger.id] += delta_t
        
    #IN ORIGIN.CHECK_ORIGIN()
    def pickup_assignment(self, request_num, node_num, walk_time, delta_t, cost, checkpoint = False):
        #nod id, walk_time to pick up, delta_T, cost
        if checkpoint:
            milage = 0.
        else:
            milage = (delta_t - cf.WAITING_TIME) * (cf.BUS_SPEED / 3600.)
        self.request_origin[request_num] = (node_num, None , None , None, None, walk_time, delta_t, cost, milage)
        
    #IN STATS.MERGE_STOP()
    def pickup_add_walktime(self, request_num, extra_time):
        r = self.request_origin[request_num]
        self.request_origin[request_num] = (r[0], r[1], r[2], r[3], r[4], r[5] + extra_time, r[6], r[7], r[8])
        
    #IN DESTINATION.CHECK_DESTINATION()
    def dropoff_assignment(self, request_num, node_num, walk_time, delta_t, cost, checkpoint = False):
        if checkpoint:
            milage = 0.
        else:
            milage = (delta_t - cf.WAITING_TIME) * (cf.BUS_SPEED / 3600.)
        self.request_destination[request_num] = (node_num, None, None, None, None, walk_time, delta_t, cost, milage)
        
    #IN STATS.MERGE_STOP()
    def dropoff_add_walktime(self, request_num, extra_time):
        r = self.request_destination[request_num]
        self.request_destination[request_num] = (r[0], r[1], r[2], r[3], r[4], r[5] + extra_time, r[6], r[7], r[8])
        
    #IN BUS.HANDLE_ARRIVAL()
    def pickup_arrival(self, request_num, coordinates, time):
        r = self.request_origin[request_num]
        request_time = self.request_rows[request_num][1] 
        self.request_origin[request_num] = (r[0], coordinates.xy.x, coordinates.xy.y, 
                           time - request_time - self.p_delay_WT[request_num]- r[5], self.p_delay_WT[request_num], r[5], r[6], r[7], r[8])
        
    #IN BUS.HANDLE_ARRIVAL()
    def dropoff_arrival(self, request_num, coordinates, time):
        r = self.request_destination[request_num]
        request_time = self.request_rows[request_num][1]
        pickup_time = self.request_origin[request_num][3] + request_time #request_time + wait_time = pickup_time
        self.request_destination[request_num] = (r[0], coordinates.xy.x, coordinates.xy.y, 
                                time - pickup_time - self.p_delay_RT[request_num], self.p_delay_RT[request_num], r[5], r[6], r[7], r[8])
        
        self.write_request(request_num)
        
    def write_request(self, request_num):
        r = self.request_rows.pop(request_num)
        o = self.request_origin.pop(request_num)
        d = self.request_destination.pop(request_num)
        rt = self.p_extra_RT.pop(request_num)
        wt = self.p_extra_WT.pop(request_num)
        self.request.writerow(list(r) +  list(o) + list(d) + [wt , rt])
        
    def end(self):
        o = (None, None, None, None, None, None, None)
        d = (None, None, None, None, None, None, None)
        for row in self.request_rows.values():
            self.request.writerow(list(row) + list(o) + list(d))
        self.output1.close()
        self.output2.close()
        self.output3.close()