
INITIAL_CAPITAL = 100_000_000

FEE_RATE = 0.002

MAX_POSITIONS = 3
MAX_ALLOCATION = 0.30

# Pengamanan forward test
MAX_ORDERBOOK_AGE_SECONDS = 3600
DAILY_LOSS_LIMIT_PERCENT = 0.05

PAIR_RULES = {
    "btcidr": {
        "min_idr": 10_000,
        "min_quantity": 0.00000745,
        "quantity_increment": 0.00000001,
    },
    "ethidr": {
        "min_idr": 10_000,
        "min_quantity": 0.00026851,
        "quantity_increment": 0.00000001,
    },
    "xrpidr": {
        "min_idr": 10_000,
        "min_quantity": 0.52287582,
        "quantity_increment": 0.00000001,
    },
    "solidr": {
        "min_idr": 10_000,
        "min_quantity": 0.00658036,
        "quantity_increment": 0.00000001,
    },
    "pepeidr": {
        "min_idr": 10_000,
        "min_quantity": 111100.001111,
        "quantity_increment": 1,
    },
    "hypeidr": {
        "min_idr": 10_000,
        "min_quantity": 0.00764363,
        "quantity_increment": 0.00000001,
    },
}
