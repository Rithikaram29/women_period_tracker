######## create next period date here
from datetime import timedelta, datetime

## keeping the average menstrual cycle time,
# 28 day average, 
# 1-5 - menstrual days
# 6-11 - follicular phase
# 12-15 - ovulation phase
# 15-28 - luteal phase
menstrual_days = 5
follicular_days = 11
ovluation_days = 15
luteal_days = 28
def get_next_date(date_in:str):
    today = datetime.today()
    last_date = datetime.strptime(date_in, "%Y-%m-%d")
    
    day_since = (today - last_date).days
    cycle_day = (day_since % 28) + 1
    
    if cycle_day <= menstrual_days:
        phase = "menstrual"
    elif cycle_day <= follicular_days:
        phase = "follicular"
    elif cycle_day <= ovluation_days:
        phase = "ovulation"
    else:
        phase = "luteal"
    
    next_period = last_date + timedelta(days=28)

    
    return {
        "days_since": day_since,
        "cycle_day": cycle_day,
        "cycle_phase": phase,
        "next_period_date": next_period.date()
    }