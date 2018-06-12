from shapely.geometry import Point

import stop
import passenger as ps

def add_passengers(self):
        if self.t != 0:
            return
        # some stops for testing
        ds = stop.Stop(self.next_stop_id, Point(1, .75), "dem", None)
        self.next_stop_id += 1
        ds2 = stop.Stop(self.next_stop_id, Point(2, .75), "dem", None)
        self.next_stop_id += 1
        ds3 = stop.Stop(self.next_stop_id, Point(6, .25), "dem", None)
        self.next_stop_id += 1
        ds4 = stop.Stop(self.next_stop_id, Point(7, .75), "dem", None)
        self.next_stop_id += 1
        ds5 = stop.Stop(self.next_stop_id, Point(3, .25), "dem", None)
        self.next_stop_id += 1
        ds6 = stop.Stop(self.next_stop_id, Point(7.5, .25), "dem", None)
        self.next_stop_id += 1

        d = ps.Passenger(0, "PRD", self.chkpts[0], ds, 0)
        d2 = ps.Passenger(1, "RPD", ds2, self.chkpts[1], 0)
        d3 = ps.Passenger(2, "PD", self.chkpts[0], self.chkpts[1], 0)
        d4 = ps.Passenger(3, "PD", self.chkpts[1], self.chkpts[2], 0)
        d5 = ps.Passenger(4, "RPRD", ds2, ds3, 0)
        d6 = ps.Passenger(5, "RPD", ds4, self.chkpts[1], 0)
        d7 = ps.Passenger(6, "RPD", ds6, self.chkpts[1], 0)


        from collections import OrderedDict
        self.unserviced_demand = OrderedDict([(d3.id, d3),
                                              (d4.id, d4),
                                              (d.id, d),
                                              (d2.id, d2),
                                              (d5.id, d5),
                                              (d6.id, d6),
                                              (d7.id, d7)])


def other_passengers(sim):
    s3 = stop.Stop(3, Point(3.196, .896), 'dem', None)
    p0 = ps.Passenger(0, "RPD", s3, sim.chkpts[2], -33)

    s4 = stop.Stop(4, Point(4.078, .017), 'dem', None)
    p1 = ps.Passenger(1, "PRD", sim.chkpts[0], s4, -19)

    s5 = stop.Stop(5, Point(4.354, .476), 'dem', None)
    p2 = ps.Passenger(2, "RPD", s5, sim.chkpts[2], 231)

    p4 = ps.Passenger(4, "PD", sim.chkpts[1], sim.chkpts[2], 486)

    s6 = stop.Stop(6, Point(7.213, .3956), 'dem', None)
    p6 = ps.Passenger(6, "RPD", s6, sim.chkpts[2], 692)

    s7 = stop.Stop(7, Point(8.491, .8873), 'dem', None)
    p7 = ps.Passenger(7, "RPD", s7, sim.chkpts[2], 1104)
    passengers_by_t = {p.request_t: p for p in [p0, p1, p2, p4, p6, p7]}
    if sim.t in passengers_by_t:
        p = passengers_by_t[sim.t]
        sim.unserviced_demand[p.id] = p



def more_other_passengers(sim):
    s4 = stop.Stop(4, Point(3.275415728278608, 0.44705177815616537), 'dem', None)
    p2 = ps.Passenger(2, "RPD", s4, sim.chkpts[2], 78)
    s10 = stop.Stop(10, Point(5.155090654958228, 0.4448823197267098), 'dem', None)
    p12 = ps.Passenger(12, "RPD", s10, sim.chkpts[2], 687)
    s12 = stop.Stop(12, Point(4.149965345980452, 0.8443396422102097), 'dem', None)
    p14 = ps.Passenger(14, "RPD", s12, sim.chkpts[2], 1038)
    s3 = stop.Stop(3, Point(9.353790652373736, 0.10680827193339448), 'dem', None)
    p0 = ps.Passenger(0, "PRD", sim.chkpts[1], s3, -34)
    s8 = stop.Stop(8, Point(6.832153401875233, 0.5361170314735648), 'dem', None)
    p9 = ps.Passenger(9, "PRD", sim.chkpts[1], s8, 453)
    p17 = ps.Passenger(17, "PD", sim.chkpts[1], sim.chkpts[2], 1469)
    s16 = stop.Stop(16, Point(5.158328450613546, 0.6790712724469335), 'dem', None)
    p20 = ps.Passenger(20, "RPD", s16, sim.chkpts[2], 1803)
    passengers_by_t = {p.request_t: p for p in [p2, p12, p14, p0, p9, p17, p20]}
    if sim.t in passengers_by_t:
        p = passengers_by_t[sim.t]
        sim.unserviced_demand[p.id] = p


def other_other_passengers(sim):
    s4 = stop.Stop(4, Point(2.275415728278608, 0.64705177815616537), 'dem', None)
    p2 = ps.Passenger(2, "RPD", s4, sim.chkpts[2], 378)
    s5 = stop.Stop(5, Point(.355090654958228, 0.4448823197267098), 'dem', None)
    p3 = ps.Passenger(3, "RPD", s5, sim.chkpts[2], 380)

    passengers_by_t = {p.request_t: p for p in [p2, p3]}
    if sim.t in passengers_by_t:
        p = passengers_by_t[sim.t]
        sim.unserviced_demand[p.id] = p

def merge_walking_passengers(sim):
    s4 = stop.Stop(4, Point(3.2, 0.8), 'dem', None)
    p2 = ps.Passenger(2, "PRD", sim.chkpts[1], s4, 153)
    s10 = stop.Stop(10, Point(3.5, 0.9), 'dem', None)
    p12 = ps.Passenger(12, "RPRD", s4, s10, 152)
    
    s12 = stop.Stop(12, Point(5.0, 0.3), 'dem', None)
    p14 = ps.Passenger(14, "PRD", sim.chkpts[1], s12, 155)
    s3 = stop.Stop(3, Point(5.0, 0.7), 'dem', None)
    p0 = ps.Passenger(0, "RPRD", s12, s3, 251)
    
    s8 = stop.Stop(8, Point(3.7, 0.3), 'dem', None)
    p9 = ps.Passenger(9, "PRD", sim.chkpts[1], s8, 253)
    s16 = stop.Stop(16, Point(4.0, 0.6), 'dem', None)
    p20 = ps.Passenger(20, "RPRD", s8, s16, 301)
    
    s18 = stop.Stop(18, Point(4.0, 0.1), 'dem', None)
    p21 = ps.Passenger(21, "PRD", sim.chkpts[1], s18, 302)
    s19 = stop.Stop(19, Point(4.3, 0.3), 'dem', None)
    p22 = ps.Passenger(22, "RPRD", s18, s19, 302)
    
    s20 = stop.Stop(16, Point(3.7, 0.3), 'dem', None)
    p23 = ps.Passenger(23, "PRD", sim.chkpts[1], s20, 303)
    s21 = stop.Stop(16, Point(3.6, 0.5), 'dem', None)
    p24 = ps.Passenger(24, "RPRD",s20, s21, 305)
    
    s22 = stop.Stop(22, Point(2.0, 0.3), 'dem', None)
    p25 = ps.Passenger(25, "PRD", sim.chkpts[0], s22, -21)
    s23 = stop.Stop(23, Point(5.0, 0.1), 'dem', None)
    p26 = ps.Passenger(26, "RPRD", s22, s23, -20)
    
    s24 = stop.Stop(24, Point(4.0, 0.5), 'dem', None)
    p27 = ps.Passenger(27, "PRD", sim.chkpts[1], s24, 230)
    s25 = stop.Stop(25, Point(3.3, 0.6), 'dem', None)
    p28 = ps.Passenger(28, "RPRD", s24, s25, 240)
    
    s26 = stop.Stop(26, Point(3.6, 0.4), 'dem', None)
    p29 = ps.Passenger(29, "PRD", sim.chkpts[1], s26, 250)
    #p0, p9, p2, p12, p14, p20, p21, p22, p23, p24, p25, p26, p27, p28, p29
    passengers_by_t = {p.request_t: p for p in [p9,p12, p20, p22, p24, p26, p28, p29]}
    if sim.t in passengers_by_t:
        p = passengers_by_t[sim.t]
        sim.unserviced_demand[p.id] = p

def print_passenger(p):
    if p.type == "RPD":
        print("s{} = stop.Stop({}, Point({}, {}), 'dem', None)".format(p.o.id, p.o.id, p.o.xy.x, p.o.xy.y))
        o = "s{}".format(p.o.id)
        d = "sim.chkpts[{}]".format(p.d.id)
    elif p.type == "PRD":
        print("s{} = stop.Stop({}, Point({}, {}), 'dem', None)".format(p.d.id, p.d.id, p.d.xy.x, p.d.xy.y))
        d = "s{}".format(p.d.id)
        o = "sim.chkpts[{}]".format(p.o.id)
    else:
        o = "sim.chkpts[{}]".format(p.o.id)
        d = "sim.chkpts[{}]".format(p.d.id)
    print("p{} = ps.Passenger({}, \"{}\", {}, {}, {})".format(p.id, p.id, p.type, o, d, p.request_t))
