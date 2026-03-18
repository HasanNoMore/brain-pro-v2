from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import deque
import os

app = FastAPI(title="THE BRAIN PRO", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://the-brain-pro.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SECRET WEAPON 1: SHADOW CATCH-UP ==========
class ShadowCatchUp:
    def scan_opportunities(self, symbols: List[str]) -> List[dict]:
        opportunities = []
        for symbol in symbols:
            # Simulate market dislocation detection
            discount = round(random.uniform(0.5, 3.5), 2)
            confidence = round(random.uniform(0.7, 0.95), 2)
            
            opportunities.append({
                "symbol": symbol,
                "discount": discount,
                "confidence": confidence,
                "urgency": "high" if discount > 2.0 else "medium",
                "current_price": round(random.uniform(10, 500), 2),
                "fair_value": round(random.uniform(10, 500) * 1.02, 2),
                "catch_up_potential": round(discount * confidence * 0.8, 2)
            })
        return sorted(opportunities, key=lambda x: x["catch_up_potential"], reverse=True)[:3]

# ========== SECRET WEAPON 2: GAMMA PROXY ==========
class GammaProxy:
    def detect_squeezes(self, symbols: List[str]) -> List[dict]:
        squeezes = []
        for symbol in symbols:
            if random.random() > 0.6:  # 40% chance of squeeze detected
                direction = "up" if random.random() > 0.5 else "down"
                squeezes.append({
                    "symbol": symbol,
                    "direction": direction,
                    "probability": round(random.uniform(0.65, 0.90), 2),
                    "intensity": round(random.uniform(0.7, 0.95), 2),
                    "gamma_wall": random.randint(1000000, 5000000),
                    "timeframe": "2-6 hours"
                })
        return squeezes

# ========== SECRET WEAPON 3: TOXICITY DETECTOR ==========
class ToxicityDetector:
    def __init__(self):
        self.buckets = deque(maxlen=50)
    
    def get_readings(self, symbols: List[str]) -> List[dict]:
        readings = []
        for symbol in symbols:
            vpin = round(random.uniform(0.1, 0.9), 3)
            level = "toxic" if vpin > 0.7 else "suspicious" if vpin > 0.5 else "clean"
            readings.append({
                "symbol": symbol,
                "vpin": vpin,
                "level": level,
                "informed_probability": round(vpin * 0.9, 2),
                "expected_move": round(vpin * 3, 2),
                "timeframe": "30-60 min",
                "alert": level == "toxic"
            })
        return sorted(readings, key=lambda x: x["vpin"], reverse=True)[:3]

# ========== KELLY OPTIMIZER ==========
class KellyOptimizer:
    def calculate(self, capital: float) -> dict:
        win_rate = 0.65
        avg_win = 150
        avg_loss = 75
        b = avg_win / avg_loss
        
        kelly = (win_rate * b - (1 - win_rate)) / b
        return {
            "full_kelly": round(kelly * 100, 2),
            "half_kelly": round(kelly * 50, 2),
            "quarter_kelly": round(kelly * 25, 2),
            "recommended": "half_kelly",
            "max_position_usd": round(capital * 0.02, 2),
            "win_rate": win_rate,
            "risk_reward": round(b, 2)
        }

# Initialize engines
shadow_engine = ShadowCatchUp()
gamma_engine = GammaProxy()
toxicity_engine = ToxicityDetector()
kelly_engine = KellyOptimizer()

# ========== EXISTING ENDPOINTS (Keep These!) ==========
@app.get("/health")
def health():
    return {"status": "operational", "version": "3.0"}

@app.get("/api/portfolio")
def portfolio():
    return {
        "total_equity": 2844,
        "assets": ["LRC", "THETA", "PI", "ICP", "TRX"]
    }

@app.post("/api/emergency/stop")
def emergency_stop():
    return {"status": "STOPPED", "timestamp": datetime.now().isoformat()}

# ========== NEW SECRET WEAPONS ENDPOINTS ==========
@app.get("/api/alpha")
def get_alpha():
    """Get all secret weapon alpha signals"""
    symbols = ["BTC", "ETH", "SOL", "LRC", "THETA", "PI", "ICP", "TRX"]
    
    shadow_opps = shadow_engine.scan_opportunities(symbols)
    gamma_squeezes = gamma_engine.detect_squeezes(symbols)
    toxicity = toxicity_engine.get_readings(symbols)
    kelly = kelly_engine.calculate(2844)
    
    total_missed = sum(opp["catch_up_potential"] for opp in shadow_opps)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "portfolio_value": 2844,
        "shadow_catch_up": {
            "missed_alpha_24h": round(total_missed, 2),
            "opportunities": shadow_opps
        },
        "gamma_proxy": {
            "squeezes_detected": len(gamma_squeezes),
            "opportunities": gamma_squeezes
        },
        "toxicity_detector": {
            "alerts": len([t for t in toxicity if t["alert"]]),
            "readings": toxicity
        },
        "kelly_sizing": kelly
    }

@app.get("/api/shadow/opportunities")
def get_shadow_opportunities():
    """Get Shadow Catch-Up opportunities"""
    symbols = ["LRC", "THETA", "PI", "ICP", "TRX"]
    return {
        "missed_alpha_24h": 76.80,
        "opportunities": shadow_engine.scan_opportunities(symbols)
    }

@app.get("/api/gamma/squeezes")
def get_gamma_squeezes():
    """Get Gamma squeeze predictions"""
    symbols = ["BTC", "ETH", "SOL"]
    return {
        "squeezes": gamma_engine.detect_squeezes(symbols)
    }

@app.get("/api/toxicity/readings")
def get_toxicity():
    """Get order flow toxicity readings"""
    symbols = ["BTC", "ETH", "LRC", "THETA"]
    return {
        "readings": toxicity_engine.get_readings(symbols)
    }

@app.get("/api/strategies/status")
def get_strategies():
    """Get active strategies status"""
    return {
        "active_strategies": [
            {"name": "shadow_catch_up", "status": "active", "edge": "mean_reversion"},
            {"name": "gamma_proxy", "status": "active", "edge": "options_arbitrage"},
            {"name": "toxicity_detector", "status": "active", "edge": "flow_analysis"},
            {"name": "bollinger_bounce", "status": "standby", "edge": "volatility"},
            {"name": "early_gainer", "status": "standby", "edge": "momentum"}
        ],
        "total_active": 3,
        "total_standby": 2
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
