import config as cf
import csv

class overall_statistics(object):
    def __init__(self):
        
        self.overall_file = open(cf.OUTPUT_OVERALL, 'w', newline = '')
        self.w_overall = csv.writer(self.overall_file, delimiter = ',')
        
        self.request_file = open(cf.OUTPUT_REQUEST, 'r', newline = '')
        self.r_request = csv.reader(self.request_file, delimiter = ',')
        
    def get_stats(self):
        total_waitTime = 0.
        total_rideTime = 0.
        total_slackTime = 0.
        total_pickupWalk = 0.
        total_dropoffWalk = 0.
        total_requests = 0
        for row in self.r_request:
            if row[7] == "True":
                total_waitTime += float(row[11])
                total_rideTime += float(row[18])
                total_slackTime += float(row[13]) + float(row[20])
                total_pickupWalk += float(row[12])
                total_dropoffWalk += float(row[19])
                total_requests += 1
        
        max_slack = cf.R_TIME - (cf.R_LENGTH / (cf.W_SPEED * 3600.))
        self.w_overall.writerow(["STATISTICS", "AVERAGE"])
        self.w_overall.writerow(["AVERAGE WAIT TIME", (total_waitTime/60.)/total_requests])
        self.w_overall.writerow(["AVERAGE RIDE TIME", (total_rideTime/60.)/total_requests])
        self.w_overall.writerow(["AVERAGE PICKUP WALK TIME", (total_pickupWalk/60.)/total_requests])
        self.w_overall.writerow(["AVERAGE DROPOFF WALK TIME", (total_dropoffWalk/60.)/total_requests])
        
        self.w_overall.writerow(["SLACK TIME USED (%)", total_slackTime/max_slack])
        
        self.overall_file.close()
        
stats = overall_statistics()
stats.get_stats()