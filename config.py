OUTPUT_REQUEST = "request"
OUTPUT_NODE = "node"
OUTPUT_BUS = "bus"
OUTPUT_COST = "output_cost.csv"
OUTPUT_OVERALL = "output_overall.csv"

FILE_NUM_START = 1
SIM_ITERATIONS = 1

PRESET_PASSENGERS = False
PASSENGER_CSV = 'passengers.csv'

BUS_SPEED = 25 # bus speed (mph)
W_SPEED = 3 # walk speed (mph)

R_LENGTH = 10 # ride length(miles)
R_TIME = 1.2*60*R_LENGTH/BUS_SPEED # ride time(mins)
MAX_DEV = .1 # max y deviation. grid is R_LENGTH x (2*MAX_DEV)
MAX_R = 0 # max walking radius from 3 main checkpoints? (unclear)
MIN_DIST = 0.25

N_RIDES = 5 # number of buses that will come through
HEADWAY = 10 # headway (mins)
N_INT_POINTS = 1 # number of intermediate checkpoints
WAITING_TIME = 10 # bus waiting time to allow load / unload (secs)

N_CUSTOMERS_PER_HR = 30
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

ADVANCE_DEMAND = 10 # MINUTES of customer demand in advance of first ride

WEIGHT_EXTRAMILES = .25 #0.25
WEIGHT_EXTRA_PSGM = 0
WEIGHT_EXTRA_PSGRT = .25   #0.25
WEIGHT_EXTRA_PSGWT = .5     #0.5
WEIGHT_EXTRA_PSGDLY = 0
assert (WEIGHT_EXTRAMILES + WEIGHT_EXTRA_PSGM + WEIGHT_EXTRA_PSGRT + WEIGHT_EXTRA_PSGWT + WEIGHT_EXTRA_PSGDLY - 1) < .000001

MIN_PI=(2*MAX_DEV/BUS_SPEED*60+WAITING_TIME/60)/((R_TIME-R_LENGTH/BUS_SPEED*60)/(N_INT_POINTS+1))
MIN_INIT_SLACK =0.7  # b/w 0 and 1, pi in the paper
MAX_BACK = 1 # max backtracking (miles)

ALLOW_STEPS = False 

T_STEP = 1 # time step (seconds)

ALLOW_MERGE = True
ALLOW_WALKING = True
WALK_MULTIPLIER = 1.0
MAX_WALK_TIME = 10 #max walking time (minutes)
MAX_MERGE_TIME = 2 #max walking time (minutes)

COST_RT = 0.0
COST_WT = 0.0


COST_D = 1.0
