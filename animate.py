"""
A simple example of an animated plot
"""
import logging
lg = logging.getLogger()
#lg.setLevel(logging.DEBUG)
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import config as cf
import main
import stop

fig, ax = plt.subplots()
bus_states = {}
demand_states = {}
sim = main.Sim()

def run():

    stop.plot_stops(sim.chkpts, ax=ax, label="Checkpoints")

    ani = animation.FuncAnimation(fig, anfunc, interval=1)
    #ani.save("ani.gif", dpi=80, writer='imagemagick')
    plt.show()

new = False
def anfunc(i):
    global new
    new_stop = sim.step()
    if new_stop:
        print("?!??!")
        ax.scatter(new_stop.xy.x, new_stop.xy.y, color='purple', s=10) 
        new = True

    for bus in sim.active_buses:
        if bus.id not in bus_states:
            lbs = len(bus_states)
            bus_states[bus.id] = ax.scatter(bus.cur_xy.x, bus.cur_xy.y, label="Buses", color='orange', marker='s')
            if lbs == 0:
                ax.legend()
        else:
            bus_states[bus.id].set_offsets([bus.cur_xy.x, bus.cur_xy.y])

        if new:
            bus_can_go = bus.usable_slack_time(sim.t, 2, sim.chkpts) * (cf.BUS_SPEED / 3600)
            ax.plot([bus.cur_xy.x, bus.cur_xy.x - bus_can_go], [bus.cur_xy.y, bus.cur_xy.y])
            print("bus can go {}".format(bus_can_go))


        for demand in bus.passengers_assigned.values():
            if demand.id not in demand_states:
                print("yeah?")
                demand_states[demand.id] = demand.plot(ax=ax)

        for demand in bus.passengers_on_board.values():
            if demand.id in demand_states:
                o, l, d = demand_states[demand.id]
                o.set_visible(False)
                l[0].set_visible(False)
            if demand.id not in demand_states:
                o, l, d = demand.plot(ax=ax)
                o.set_visible(False)
                l[0].set_visible(False)
                demand_states[demand.id] = (o, l, d)

        for demand in bus.serviced_passengers:
            if demand.id in demand_states:
                o, l, d = demand_states[demand.id]
                l[0].set_visible(False)
                d.set_visible(False)

    for demand in sim.unserviced_demand.values():
        if demand.id not in demand_states:
            print("happening for {}".format(demand.id))
            demand_states[demand.id] = demand.plot(ax=ax, legend=(True if len(demand_states) == 0 else False))


if __name__ == "__main__":
    run()
