import csv

output1 = open("helloworld.csv", "w", newline = '')
request = csv.writer(output1, delimiter = ",")

a = (1,2,3,4,5)
b = ('6','7','8','9','10')

request.writerow(list(a)+list(b))
output1.close()