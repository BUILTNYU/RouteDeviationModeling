import config as cf
import csv

class overall_statistics(object):
    def __init__(self):
        
        self.overall_file = open(cf.OUTPUT_OVERALL, 'w', newline = '')
        self.w_overall = csv.writer(self.overall_file, delimiter = ',')
        
        self.request_file = None
        self.r_request = None
        
    def get_stats(self, start, end):
        overall_IW = 0.
        overall_EW = 0.
        overall_IR = 0.
        overall_ER = 0.
        overall_ST = 0.
        overall_PW = 0.
        overall_DW = 0.
 
        overall_TIW = 0.
        overall_TEW = 0.
        overall_TIR = 0.
        overall_TER = 0.
        overall_TST = 0.
        overall_TPW = 0.
        overall_TDW = 0.
        
        overall_EM = 0.
        overall_TD = 0.
        
        overall_sim = 0
        overall_A = 0
        overall_R = 0
        
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
            
            overall_IW += total_initialWait/total_requests
            overall_EW += total_extraWait/total_requests
            overall_IR += total_initialRide/total_requests
            overall_ER += total_extraRide/total_requests
            overall_ST += total_slackTime/max_slack
            overall_PW += total_pickupWalk/total_requests
            overall_DW += total_dropoffWalk/total_requests

            overall_TIW += total_initialWait
            overall_TEW += total_extraWait
            overall_TIR += total_initialRide
            overall_TER += total_extraRide
            overall_TST += total_slackTime
            overall_TPW += total_pickupWalk
            overall_TDW += total_dropoffWalk

            overall_EM += total_extraMilage
            overall_TD += total_distance_normal
            overall_A += accepted
            overall_R += rejected
            overall_sim += 1
            
            self.w_overall.writerow([])
            
        self.w_overall.writerow(["ALL SIMULATIONS"])
        self.w_overall.writerow(["STATISTICS", "AVERAGE", "TOTAL"])
        self.w_overall.writerow(["INITIAL WAIT TIME", (overall_IW/60.)/overall_sim, (overall_TIW/60.)/overall_sim])
        self.w_overall.writerow(["EXTRA WAIT TIME", (overall_EW/60.)/overall_sim, (overall_TEW/60.)/overall_sim])
        self.w_overall.writerow(["INITIAL RIDE TIME", (overall_IR/60.)/overall_sim, (overall_TIR/60.)/overall_sim])
        self.w_overall.writerow(["EXTRA RIDE TIME", (overall_ER/60.)/overall_sim, (overall_TER/60.)/overall_sim])
        self.w_overall.writerow(["PICKUP WALK TIME", (overall_PW/60.)/overall_sim, (overall_TPW/60.)/overall_sim])
        self.w_overall.writerow(["DROPOFF WALK TIME", (overall_DW/60.)/overall_sim, (overall_TDW/60.)/overall_sim])
        
        self.w_overall.writerow(["TOTAL MILAGE", (overall_EM + overall_TD)/overall_sim])
        self.w_overall.writerow(["SLACK TIME USED", (overall_ST/overall_sim)])
        self.w_overall.writerow(["ACCEPTED", overall_A, "REJECTED", overall_R, "ACCEPTANCE", (overall_A*1.)/(overall_A+overall_R)])
            
        self.overall_file.close()
        