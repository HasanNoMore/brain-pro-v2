from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="THE BRAIN PRO", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://the-brain-pro.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "operational", "version": "2.0"}

@app.get("/api/portfolio")
def portfolio():
    return {"total_equity": 2844, "assets": ["LRC", "THETA", "PI", "ICP", "TRX"]}

@app.post("/api/emergency/stop")
def emergency_stop():
    return {"status": "STOPPED"}
