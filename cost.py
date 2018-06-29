import config as cf
import csv
import itertools
import numpy as np

stop_file = cf.OUTPUT_NODE
bus_file = cf.OUTPUT_BUS
request_file = cf.OUTPUT_REQUEST
cost_file = cf.OUTPUT_COST

num_buses = cf.N_RIDES
num_chkpts = cf.N_INT_POINTS + 1

w1 = cf.COST_D
w2 = cf.COST_RT
w3 = cf.COST_WT

class Cost(object):
    def __init__(self):
        self.stop_file = open(cf.OUTPUT_NODE, 'r', newline = '')
        self.r_stops = csv.reader(self.stop_file, delimiter = ',')
        
        self.bus_file = open (cf.OUTPUT_BUS, 'r', newline = '')
        self.r_buses = csv.reader(self.bus_file, delimiter = ',')
        
        self.request_file = open(cf.OUTPUT_REQUEST, 'r', newline = '')
        self.r_requests = csv.reader(self.request_file, delimiter =',')
        
        self.cost_file = open (cf.OUTPUT_COST, 'w', newline = '')
        self.w_costs = csv.writer(self.cost_file, delimiter = ',')
        
        self.chkpts = {}        #[bus id] = (all checkpoints)
        self.stops = {}         #[stop id] = position
        self.sets = {}          #[(bus id, chkpt end)] = (full powerset)
        self.buses = {}         #[bus id] = (all stop id s)
        self.requests = {}      #[request id] = (pickup.id, dropoff.id)
        self.costs = {}         #[stop id] = cost
        
    def get_data(self):
        i = 0
        for row in self.r_requests:
            if i == 0:
                i += 1
                continue
            elif row[7] == "True":
                try:
                    self.requests[int(row[0])] = (int(row[8]), int(row[17]))
                except ValueError:
                    import pdb; pdb.set_trace()
                
        self.chkpts[0] = (0,0.5)    #default starting position
        self.stops[0] = (0,0.5)
        i = 0
        for row in self.r_stops:
            if i == 0:
                i += 1
                continue
            if row[3] == "chk":
                self.chkpts[int(row[0])] = (float(row[1]), float(row[2]))
            self.stops[int(row[0])] = (float(row[1]), float(row[2]))
        
        i = 0
        temp_stops = []
        for i in range(num_buses):
            temp_stops.append([])

        i = 0
        for row in self.r_buses:
            if i == 0:
                i += 1
                continue
            if (int(row[1]) not in temp_stops[int(row[0])]):
                temp_stops[int(row[0])].append(int(row[1]))
        for index, s in enumerate(temp_stops):
            self.buses[index] = tuple(s)
        
        for index, stops in self.buses.items():
            temp_stops = []
            for s in stops:
                if s in self.chkpts:
                    self.sets[(index, s)] = tuple(self.powerset(temp_stops))
                    temp_stops = []
                else:
                    temp_stops.append(s)
    
    def run(self):   
        self.calculate_costs()
        self.write_requests()
        self.cost_file.close()
        self.bus_file.close()
        self.request_file.close()
        self.stop_file.close()
        
    def powerset(self, stops):
        return itertools.chain.from_iterable(itertools.combinations(stops, r) for r in range(len(stops)+1))
                    
    def calculate_cost(self, stop, previous_stops, next_stops, distance):
        rt = 0
        wt = 0
        print("CHECK SET: " + str(previous_stops) + " " + str(stop) + " " + str(next_stops) + " -> " + str(distance))
        """"NOT NEEDED FOR NOW
        delta_t = cf.WAITING_TIME + (distance / (cf.W_SPEED/3600.))
        for passengers in self.requests.values():
            if passengers[0] in previous_stops:
                rt += delta_t
            if passengers[0] in next_stops:
                rt += delta_t
            elif passengers[1] in next_stops:
                wt += delta_t
        """
        return w1 * distance + w2 * rt + w3 * wt;
    
    def shapely(self, stop, sets):
        costs = []
        for cur_set in sets:
            prev = []
            aft = []
            p = True
            for s in cur_set:
                if s == stop:
                    p = False
                elif p:
                    prev.append(s)
                else:
                    aft.append(s)
            costs.append(self.calculate_cost(stop, prev, aft, self.distance(stop, prev[-1], aft[0])))
        return np.sum(costs)/len(costs)
    
    def distance(self, cur_stop, prev_stop, next_stop):
        daqx = self.stops[cur_stop][0] - self.stops[prev_stop][0]
        daqy = self.stops[cur_stop][1] - self.stops[prev_stop][1]
        dqbx = self.stops[next_stop][0] - self.stops[cur_stop][0]
        dqby = self.stops[next_stop][1] - self.stops[cur_stop][1]
        
        dabx = self.stops[next_stop][0] - self.stops[prev_stop][0]
        daby = self.stops[next_stop][1] - self.stops[prev_stop][1]
        dist =  np.sum(np.abs([daqx, daqy, dqbx, dqby])) - np.sum(np.abs([dabx, daby]))
        return dist
        
    def calculate_costs(self):
        for bus, stops in self.buses.items():
            chkpt = 1
            cur_powerset = self.sets[(bus,chkpt)]
            for stop in stops:
                if (stop in self.chkpts):
                    chkpt += 1
                    self.costs[stop] = 0.
                    if (chkpt <= num_chkpts):
                        cur_powerset = self.sets[(bus,chkpt)]
                    continue
                c_set = []
                for cur_set in cur_powerset:
                    if stop in cur_set:
                        c_set.append([chkpt -1] + list(cur_set) + [chkpt])
                self.costs[stop] = self.shapely(stop, c_set)
         
    def write_requests(self):
        self.w_costs.writerow(["DEMAND ID", "PICKUP ID", "PICKUP COST", "DROPOFF ID", "DROPOFF COST", "TOTAL COST"])
        for passenger, (origin, destination) in self.requests.items():
            self.w_costs.writerow([passenger, origin, self.costs[origin], destination, self.costs[destination], self.costs[origin] + self.costs[destination]])
            