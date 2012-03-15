#!/usr/bin/env python2.7
"""Create mappings.
"""
import random
import csv

if __name__ == "__main__":
    fleet = [  random.randint(1000,5000) for i in range(300) ]
    routes = [  random.randint(1,100) for i in range(80) ]
    directions = [ 1, 2 ]
    tps = list( range(1000) )
    stops = list( range(3200) )

    with open("vehicle.csv","w") as vehicle:
        wtr= csv.DictWriter( vehicle, ['vid','bus'] )
        wtr.writeheader()
        for v in fleet:
            wtr.writerow( dict(vid=v, bus=6000-v) )