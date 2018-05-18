"""
A simple example of an animated plot
"""
import logging
lg = logging.getLogger()
#lg.setLevel(logging.DEBUG)
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import main
import stop

fig, ax = plt.subplots()
bus_states = {}
demand_states = {}
sim = main.Sim()

def run():

    stop.plot_stops(sim.chkpts, ax=ax)

    ani = animation.FuncAnimation(fig, anfunc, interval=1)
    plt.show()

def anfunc(i):
    sim.step()
    for bus in sim.active_buses:
        if bus.id not in bus_states:
            bus_states[bus.id] = ax.scatter(bus.cur_xy.x, bus.cur_xy.y)
        else:
            bus_states[bus.id].set_offsets([bus.cur_xy.x, bus.cur_xy.y])


        for demand in bus.passengers_assigned.values():
            if demand.id not in demand_states:
                demand_states[demand.id] = demand.plot(ax=ax)

        for demand in bus.passengers_on_board.values():
            if demand.id in demand_states:
                o, d = demand_states[demand.id]
                o.set_visible(False)
            if demand.id not in demand_states:
                o, d = demand.plot(ax=ax)
                o.set_visible(False)
                demand_states[demand.id] = (o, d)

        for demand in bus.serviced_passengers:
            if demand.id in demand_states:
                o, d = demand_states[demand.id]
                d.set_visible(False)

    for demand in sim.unserviced_demand.values():
        if demand.id not in demand_states:
            print("happening for {}".format(demand.id))
            demand_states[demand.id] = demand.plot(ax=ax)


if __name__ == "__main__":
    run()
