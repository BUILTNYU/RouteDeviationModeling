import config as cf
import csv

class overall_statistics(object):
    def __init__(self):
        
        self.overall_file = open(cf.OUTPUT_OVERALL, 'w', newline = '')
        self.w_overall = csv.writer(self.overall_file, delimiter = ',')
        
        self.request_file = None
        self.r_request = None
        
    def get_stats(self, start, end):
        for i in range(start, end):
            file_end = str(i) + '.csv'
            self.request_file = open(cf.OUTPUT_REQUEST + file_end, 'r', newline = '')
            self.r_request = csv.reader(self.request_file, delimiter = ',')
            self.w_overall.writerow(['SIMULATION', i])
            
            total_initialWait = 0.
            total_extraWait = 0.
            total_initialRide = 0.
            total_extraRide = 0.
            total_slackTime = 0.
            total_pickupWalk = 0.
            total_dropoffWalk = 0.
            total_extraMilage = 0.
            total_requests = 0
            accepted = 0
            rejected = 0
            for row in self.r_request:
                if row[7] == "True":
                    total_initialWait += float(row[11])
                    total_extraWait += float(row[12])
                    total_pickupWalk += float(row[13])
                    total_initialRide += float(row[20])
                    total_extraRide += float(row[21])
                    total_dropoffWalk += float(row[22])
                    total_extraMilage += float(row[25]) + float(row[16])
                    total_slackTime += float(row[14]) + float(row[23])
                    total_requests += 1
                    accepted += 1
                else:
                    rejected += 1
            
            max_slack = cf.R_TIME - (cf.R_LENGTH / (cf.W_SPEED * 3600.))
            total_distance_normal = cf.R_LENGTH
            self.w_overall.writerow(["STATISTICS", "AVERAGE", "TOTAL"])
            self.w_overall.writerow(["INITIAL WAIT TIME", (total_initialWait/60.)/total_requests, total_initialWait/60.])
            self.w_overall.writerow(["EXTRA WAIT TIME", (total_extraWait/60.)/total_requests, total_extraWait/60.])
            self.w_overall.writerow(["INITIAL RIDE TIME", (total_initialRide/60.)/total_requests, total_initialRide/60.])
            self.w_overall.writerow(["EXTRA RIDE TIME", (total_extraRide/60.)/total_requests, total_extraRide/60.])
            self.w_overall.writerow(["PICKUP WALK TIME", (total_pickupWalk/60.)/total_requests, total_pickupWalk/60.])
            self.w_overall.writerow(["DROPOFF WALK TIME", (total_dropoffWalk/60.)/total_requests, total_dropoffWalk/60.])
            
            self.w_overall.writerow(["TOTAL MILAGE", None, total_extraMilage + total_distance_normal])
            self.w_overall.writerow(["SLACK TIME USED", None, total_slackTime/max_slack])
            self.w_overall.writerow(["ACCEPTED", accepted, "REJECTED", rejected, "ACCEPTANCE", (accepted*1.)/(accepted+rejected)])
            
            self.w_overall.writerow([])
            
        self.overall_file.close()
        