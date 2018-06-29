import main
import config as cf
import average_statistics as astat
import aggregate_params as aparam

runs = cf.SIM_ITERATIONS
start = cf.FILE_NUM_START
for i in range(start, runs + start):
    s = main.Sim(i)
    while True:
        try:
            s.step()
        except ValueError:
            break;
        
stats = astat.overall_statistics()
stats.get_stats(start, runs + start)
aparam.aggregate()

