from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from backend.app.mcp_server.models.nutrition_calculator import food_list
from backend.app.utils.rag_store import hybrid_search, ingest_text


#Define the calculate input
class calculateInput(BaseModel):
    last_period_date: str
    food_intake: food_list
    sleep_hours: str
    water_intake: str
    stress_level: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


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

@app.post("/ask")
def rag_ask(data: str):
    return "ans"

@app.post("/ingest-txt")
async def ingest_txt(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".txt"):
        return {"error": "Only .txt files are supported"}

    content = await file.read()
    text = content.decode("utf-8")

    return ingest_text(file.filename, text)


@app.post("/search")
def search(request: SearchRequest):
    results = hybrid_search(request.query, request.top_k)

    return {
        "query": request.query,
        "results": results,
    }
