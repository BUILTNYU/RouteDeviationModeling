# ride synonymous with route
R_LENGTH = 5 # ride length(miles)
R_TIME = 50 # ride time(mins)
MAX_DEV = .5 # max y deviation. grid is R_LENGTH x (2*MAX_DEV)
MAX_R = 0 # max walking radius from 3 main checkpoints? (unclear)

BUS_SPEED = 25 # bus speed (mph)
W_SPEED = 3 # walk speed (mph)

N_RIDES = 15 # number of buses that will come through
HEADWAY = 10 # headway (mins)
N_INT_POINTS = 1 # number of intermediate checkpoints
WAITING_TIME = 18 # bus waiting time to allow load / unload (secs)

N_CUSTOMERS_PER_HR = 50
PD_PCT = .1
PRD_PCT = .4
RPD_PCT = .4
RPRD_PCT = .1
#PD_PCT = 0
#PRD_PCT = 1
#RPD_PCT = 0
#RPRD_PCT = 0

PTYPE_WEIGHTS = [PD_PCT, PRD_PCT, RPD_PCT, RPRD_PCT]
assert (PD_PCT + PRD_PCT + RPD_PCT + RPRD_PCT - 1) < .000001

ADVANCE_DEMAND = 1 # MINUTES of customer demand in advance of first ride

WEIGHT_EXTRAMILES = .25
WEIGHT_EXTRA_PSGM = 0
WEIGHT_EXTRA_PSGRT = .25
WEIGHT_EXTRA_PSGWT = .5
WEIGHT_EXTRA_PSGDLY = 0
assert (WEIGHT_EXTRAMILES + WEIGHT_EXTRA_PSGM + WEIGHT_EXTRA_PSGRT + WEIGHT_EXTRA_PSGWT + WEIGHT_EXTRA_PSGDLY - 1) < .000001

MIN_INIT_SLACK = .5 # b/w 0 and 1, pi in the paper
MAX_BACK = 10 # max backtracking (miles)



T_STEP = 1 # time step (seconds)

ALLOW_WALKING = True
MAX_WALK_TIME = 5 #max walking time (minutes)

ALLOW_STOP_COMBINE = True
