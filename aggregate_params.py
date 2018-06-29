import config as cf
import csv

def aggregate():
    start = cf.FILE_NUM_START
    runs = cf.SIM_ITERATIONS
    
    overall_node = open('output_' + cf.OUTPUT_NODE + '.csv', 'w', newline = '')
    overall_request = open('output_' + cf.OUTPUT_REQUEST + '.csv', 'w', newline = '')
    overall_bus = open('output_' + cf.OUTPUT_BUS + '.csv', 'w', newline = '')
    
    w_node = csv.writer(overall_node, delimiter = ',')
    w_request = csv.writer(overall_request, delimiter = ',')
    w_bus = csv.writer(overall_bus, delimiter = ',')
    
    for i in range(start, runs + start):
        ending = str(i) + '.csv'
        node = open(cf.OUTPUT_NODE + ending, 'r', newline = '')
        request = open(cf.OUTPUT_REQUEST + ending, 'r', newline = '')
        bus = open(cf.OUTPUT_BUS + ending, 'r', newline = '')
        
        r_node = csv.reader(node, delimiter = ',')
        w_node.writerow(['SIM', i])
        for row in r_node:
            w_node.writerow(row)
        w_node.writerow([])
        
        r_request = csv.reader(request, delimiter = ',')
        w_request.writerow(['SIM', i])
        for row in r_request:
            w_request.writerow(row)
        w_request.writerow(row)
        
        r_bus = csv.reader(bus, delimiter = ',')
        w_bus.writerow(['SIM', i])
        for row in r_bus:
            w_bus.writerow(row)
        w_bus.writerow(row)
        
    overall_node.close()
    overall_request.close()
    overall_bus.close()