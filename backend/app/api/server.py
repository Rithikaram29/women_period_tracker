from fastapi import FastAPI
from pydantic import BaseModel


#Define the calculate input
class calculateInput(BaseModel):
    last_period_date: str
    food_intake: list[str]
    sleep_hours: str
    water_intake: str
    stress_level: int

app = FastAPI()

@app.get("/health")
def getHealth():
    return {"Health": "ok"}

# @app.get("/periodDate")


@app.post("/calculate")
def calculate(data: calculateInput):
    last_period_date = data.last_period_date
    food_intake = data.food_intake
    sleep_hours = data.sleep_hours
    water_intake = data.water_intake
    stress_level = data.stress_level
    
    
    # we need to take the last_period_date and give it to cycle_prediction.py to get the next period date.
    
    return data