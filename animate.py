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
sim = main.Sim(1)
global step
step = True
global continious
continious = not cf.ALLOW_STEPS

def run(): 
    stop.plot_stops(sim.chkpts, ax=ax, label="Checkpoints")
    ani = animation.FuncAnimation(fig, anfunc, interval=1)
    #ani.save("ani.gif", dpi=80, writer='imagemagick')
    plt.show()
    
new = False
def anfunc(i):
    global new
    global step
    global continious
    new_o, new_d = None, None
    if (step):
        #gets a new origin, new destination to disply, if valid.
            #change is a step function - can pause the simulation after each checkpoint
        new_o, new_d, change = sim.step()
        step = not change
    else:
        #if encountered checkpoint, pause for input
        if (not continious):
            x = input("Step")
            #type continue in cmd to continue simulation
            if x == "continue":
                continious = True
        step = True
    #if there are points to display, add points
    if new_o:
        ax.scatter(new_o.xy.x, new_o.xy.y, color='purple', s=10) 
        new = True
    if new_d: 
        ax.scatter(new_d.xy.x, new_d.xy.y, color='purple', s=10) 
        new = True
    #update bus locations
    for bus in sim.active_buses:
        #activates bus 
        if bus.id not in bus_states:
            lbs = len(bus_states)
            bus_states[bus.id] = ax.scatter(bus.cur_xy.x, bus.cur_xy.y, label="Buses", color='orange', marker='s')
            if lbs == 0:
                ax.legend()
        #updates existing bus
        else:
            bus_states[bus.id].set_offsets([bus.cur_xy.x, bus.cur_xy.y])
        #adds new stops
        for demand in bus.passengers_assigned.values():
            if demand.id not in demand_states:
                demand_states[demand.id] = demand.plot(ax=ax)
        #removes pick up passengers
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
        #removes dropped off passengers
        for demand in bus.serviced_passengers:
            if demand.id in demand_states:
                o, l, d = demand_states[demand.id]
                l[0].set_visible(False)
                d.set_visible(False)
        #adds new stops not serviced
    for demand in sim.unserviced_demand.values():
        if demand.id not in demand_states:
            print("happening for {}".format(demand.id))
            demand_states[demand.id] = demand.plot(ax=ax, legend=(True if len(demand_states) == 0 else False))


if __name__ == "__main__":
    run()
