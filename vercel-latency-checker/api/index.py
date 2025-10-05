import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Initialize the FastAPI app
app = FastAPI()

# --- Enable CORS ---
# This allows any website to make POST requests to our API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Loading ---
# Load the telemetry data from the NEW JSON file.
df = pd.read_json("api/q-vercel-latency.json")

# --- Define the structure of the incoming request body ---
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int = Field(..., example=180)

# --- API Endpoint ---
@app.post("/api")
def get_latency_stats(request: LatencyRequest):
    """
    Calculates latency and uptime metrics for specified regions.
    """
    results = {}
    threshold = request.threshold_ms

    for region in request.regions:
        # Filter data for the current region
        region_df = df[df['region'] == region].copy()

        if region_df.empty:
            results[region] = {"error": "Region not found"}
            continue

        # Calculate all the required metrics
        avg_latency = region_df['latency_ms'].mean()
        p95_latency = region_df['latency_ms'].quantile(0.95)
        avg_uptime = region_df['uptime_percent'].mean()
        breaches = int((region_df['latency_ms'] > threshold).sum())

        # Store the results
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches,
        }

    return results

# A simple root endpoint to confirm the API is running
@app.get("/")
def read_root():
    return {"message": "Latency Pings API is running. Use the /api endpoint with a POST request."}
