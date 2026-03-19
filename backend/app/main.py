#!/usr/bin/env python3
"""
THE BRAIN PRO v3.1 - SPOT-ONLY ALPHA STRATEGIES
Diamond Hunting & Sniper Entries for Spot Accumulation
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import random
import os

app = FastAPI(title="THE BRAIN PRO", version="3.1 - SPOT ALPHA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://the-brain-pro.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SPOT STRATEGY 1: BOLLINGER BOUNCE ==========
class BollingerBounce:
    """
    Spot Mean Reversion Strategy
    Buy when price touches lower band (oversold)
    Sell when price reaches middle band or upper band
    
    Perfect for: Accumulating during dips in established uptrends
    """
    
    def __init__(self, period=20, std_dev=2.0):
        self.period = period
        self.std_dev = std_dev
        self.positions = {}
        
    def calculate_bands(self, prices: List[float]) -> Dict:
        if len(prices) < self.period:
            return None
            
        sma = np.mean(prices[-self.period:])
        std = np.std(prices[-self.period:])
        
        return {
            'upper': sma + (std * self.std_dev),
            'middle': sma,
            'lower': sma - (std * self.std_dev),
            'bandwidth': ((sma + (std * self.std_dev)) - (sma - (std * self.std_dev))) / sma * 100,
            'percent_b': (prices[-1] - (sma - (std * self.std_dev))) / ((sma + (std * self.std_dev)) - (sma - (std * self.std_dev)))
        }
    
    def generate_signal(self, symbol: str, prices: List[float], current_price: float) -> Dict:
        bands = self.calculate_bands(prices)
        if not bands:
            return {'signal': 'HOLD', 'confidence': 0}
        
        # Buy signal: Price touches or crosses below lower band (oversold)
        if current_price <= bands['lower'] * 1.02:  # Within 2% of lower band
            return {
                'signal': 'BUY',
                'confidence': min(0.95, (bands['lower'] - current_price) / bands['lower'] * 10 + 0.7),
                'entry': current_price,
                'target': bands['middle'],
                'stop': bands['lower'] * 0.95,  # 5% below lower band
                'reason': f'Price at ${current_price:.2f} touched lower Bollinger Band (${bands["lower"]:.2f})',
                'type': 'spot_accumulation',
                'timeframe': '1-3 days'
            }
        
        # Sell signal: Price reaches middle band (take partial profits)
        elif current_price >= bands['middle'] * 0.98 and symbol in self.positions:
            return {
                'signal': 'SELL_PARTIAL',
                'confidence': 0.8,
                'exit': current_price,
                'target': bands['upper'],
                'reason': 'Price reached middle band - taking 50% profits',
                'type': 'profit_taking'
            }
            
        # Strong sell: Price hits upper band (overbought)
        elif current_price >= bands['upper'] * 0.98 and symbol in self.positions:
            return {
                'signal': 'SELL_FULL',
                'confidence': 0.9,
                'exit': current_price,
                'reason': f'Price at ${current_price:.2f} hit upper Bollinger Band (${bands["upper"]:.2f}) - overbought',
                'type': 'full_exit'
            }
        
        return {'signal': 'HOLD', 'confidence': 0, 'bands': bands}

# ========== SPOT STRATEGY 2: EARLY GAINER (MOMENTUM BREAKOUT) ==========
class EarlyGainer:
    """
    Spot Momentum Strategy
    Detects early-stage breakouts before they become obvious to retail
    
    Perfect for: Catching the first 20-30% of a move in spot
    """
    
    def __init__(self):
        self.volume_threshold = 1.5  # 1.5x average volume
        self.price_threshold = 0.03  # 3% move
        
    def detect_breakout(self, symbol: str, candles: List[Dict], current_price: float) -> Dict:
        if len(candles) < 20:
            return {'signal': 'HOLD'}
        
        # Calculate indicators
        prices = [c['close'] for c in candles]
        volumes = [c['volume'] for c in candles]
        
        current_vol = volumes[-1]
        avg_vol = np.mean(volumes[-20:-1])
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 0
        
        # Price action
        price_change_24h = (prices[-1] - prices[-24]) / prices[-24] if len(prices) >= 24 else 0
        price_change_4h = (prices[-1] - prices[-4]) / prices[-4] if len(prices) >= 4 else 0
        
        # Early gainer detection: Volume spike + price momentum + not yet overextended
        if (vol_ratio >= self.volume_threshold and 
            price_change_4h >= 0.02 and 
            price_change_24h <= 0.15 and  # Not already pumped too much
            prices[-1] > max(prices[-20:-1])):  # Breaking 20-candle high
            
            confidence = min(0.9, vol_ratio * 0.3 + price_change_4h * 10)
            
            return {
                'signal': 'BUY',
                'confidence': round(confidence, 2),
                'entry': current_price,
                'target': current_price * 1.08,  # 8% take profit (spot realistic)
                'trailing_stop': current_price * 0.96,  # 4% trailing stop
                'reason': f'Volume {vol_ratio:.1f}x avg + Breakout above 20-period high',
                'type': 'momentum_breakout',
                'timeframe': '6-24 hours',
                'indicators': {
                    'volume_ratio': round(vol_ratio, 2),
                    'price_change_24h': round(price_change_24h * 100, 2),
                    'breakout_level': round(max(prices[-20:-1]), 2)
                }
            }
        
        # Early warning: Building momentum but not yet broken out
        elif (vol_ratio >= 1.2 and price_change_4h >= 0.01 and prices[-1] > np.mean(prices[-10:])):
            return {
                'signal': 'WATCH',
                'confidence': 0.6,
                'reason': 'Building momentum - watch for breakout',
                'type': 'early_warning',
                'indicators': {
                    'volume_ratio': round(vol_ratio, 2),
                    'price_change_4h': round(price_change_4h * 100, 2)
                }
            }
        
        return {'signal': 'HOLD'}

# ========== SPOT STRATEGY 3: DIAMOND HUNTER (UNDervalued GEM DETECTOR) ==========
class DiamondHunter:
    """
    Spot Value Strategy  
    Finds coins with high potential before they trend on social media
    
    Criteria:
    - Low market cap but high volume increase
    - Price consolidation after dump ( accumulation phase)
    - Increasing buy pressure in order book
    - Funding rate neutral or negative (if perp exists, but we ignore for spot)
    """
    
    def __init__(self):
        self.gems = {}
        
    def analyze_gem(self, symbol: str, market_data: Dict) -> Dict:
        score = 0
        reasons = []
        
        # 1. Volume increasing while price flat (smart money accumulating)
        vol_change = market_data.get('volume_change_24h', 0)
        price_change = market_data.get('price_change_24h', 0)
        
        if vol_change > 50 and abs(price_change) < 5:
            score += 30
            reasons.append("High volume accumulation (smart money)")
        
        # 2. Price near 30-day low but showing reversal candles
        if market_data.get('price_vs_30d_low', 0) < 10 and market_data.get('price_change_4h', 0) > 2:
            score += 25
            reasons.append("Bouncing from 30-day low")
        
        # 3. Increasing unique buyer count (on-chain metric simulation)
        if market_data.get('buyer_increase', 0) > 20:
            score += 20
            reasons.append("New buyers entering")
        
        # 4. Low market cap relative to volume (liquidity efficiency)
        mc_vol_ratio = market_data.get('market_cap', 1) / max(market_data.get('volume_24h', 1), 1)
        if mc_vol_ratio < 50:  # High volume relative to market cap
            score += 15
            reasons.append("High liquidity/efficiency ratio")
        
        # Generate signal if score > 60
        if score >= 60:
            return {
                'signal': 'DIAMOND_DETECTED',
                'score': score,
                'confidence': min(0.85, score / 100),
                'symbol': symbol,
                'entry': market_data.get('price', 0),
                'target': market_data.get('price', 0) * 1.15,  # 15% spot target
                'reasons': reasons,
                'type': 'diamond_hunt',
                'timeframe': '3-7 days',
                'urgency': 'high' if score > 80 else 'medium'
            }
        elif score >= 40:
            return {
                'signal': 'WATCHLIST',
                'score': score,
                'symbol': symbol,
                'reasons': reasons,
                'type': 'potential_gem'
            }
        
        return {'signal': 'IGNORE', 'score': score}

# ========== SPOT STRATEGY 4: SNIPER ENTRY (PRECISION SUPPORT) ==========
class SniperEntry:
    """
    Spot Precision Strategy
    Waits for price to hit exact support levels with confirmation
    
    Uses:
    - Previous day low/support
    - Volume profile POC (Point of Control)
    - Fibonacci retracements (0.618, 0.5, 0.382)
    """
    
    def __init__(self):
        self.levels = {}
        
    def calculate_support_levels(self, prices: List[float], highs: List[float], lows: List[float]) -> Dict:
        """Calculate key support levels for sniper entries"""
        if len(prices) < 50:
            return {}
        
        current_price = prices[-1]
        
        # Fibonacci levels from recent swing
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        fib_range = recent_high - recent_low
        
        levels = {
            'fib_618': recent_high - (fib_range * 0.618),
            'fib_5': recent_high - (fib_range * 0.5),
            'fib_382': recent_high - (fib_range * 0.382),
            'prev_day_low': min(lows[-24:]) if len(lows) >= 24 else lows[0],
            'volume_poc': np.percentile(prices, 50)  # Simulated POC
        }
        
        return levels
    
    def check_entry(self, symbol: str, prices: List[float], highs: List[float], 
                    lows: List[float], current_price: float) -> Dict:
        levels = self.calculate_support_levels(prices, highs, lows)
        if not levels:
            return {'signal': 'WAIT'}
        
        # Find nearest support level within 1%
        nearest_level = None
        min_distance = float('inf')
        
        for name, level in levels.items():
            distance = abs(current_price - level) / level * 100
            if distance < min_distance and distance < 2.0:  # Within 2%
                min_distance = distance
                nearest_level = (name, level)
        
        if nearest_level:
            level_name, level_price = nearest_level
            
            # Confirm with price action (bullish candle or volume)
            recent_volume = random.uniform(0.8, 1.5)  # Simulated volume check
            is_bullish = prices[-1] > prices[-2]  # Current candle green
            
            if is_bullish or recent_volume > 1.2:
                return {
                    'signal': 'SNIPER_BUY',
                    'confidence': 0.88 if min_distance < 0.5 else 0.75,
                    'entry': current_price,
                    'support_level': level_price,
                    'level_name': level_name.replace('_', ' ').title(),
                    'distance_from_support': round(min_distance, 2),
                    'target': current_price * 1.06,  # 6% quick spot profit
                    'stop': level_price * 0.98,  # 2% below support
                    'reason': f'Price bounced from {level_name.replace("_", " ").title()} at ${level_price:.2f} ({min_distance:.1f}% away)',
                    'type': 'sniper_entry',
                    'timeframe': '12-48 hours'
                }
        
        return {'signal': 'WAIT', 'nearest_support': min(levels.values(), key=lambda x: abs(x - current_price))}

# ========== SPOT RISK MANAGER ==========
class SpotRiskManager:
    """
    Spot-specific risk management
    No liquidation risk, but manages:
    - Opportunity cost (too much cash sitting idle)
    - Concentration risk (max 20% in single coin)
    - Correlation risk (don't buy 5 similar altcoins)
    """
    
    def __init__(self):
        self.max_position_pct = 0.20  # Max 20% in one coin
        self.max_correlation = 0.80
        self.cash_reserve = 0.30  # Keep 30% cash for dips
        
    def check_allocation(self, portfolio: Dict, symbol: str, size: float) -> Dict:
        current_value = portfolio.get('total_value', 0)
        current_position = portfolio.get('positions', {}).get(symbol, 0)
        new_position_pct = (current_position + size) / current_value if current_value > 0 else 0
        
        if new_position_pct > self.max_position_pct:
            return {
                'allowed': False,
                'reason': f'Max position size {self.max_position_pct*100}% exceeded. Current: {new_position_pct*100:.1f}%',
                'max_buy': (self.max_position_pct * current_value) - current_position
            }
        
        return {'allowed': True, 'max_buy': size}

# ========== MAIN STRATEGY ENGINE ==========
class SpotAlphaEngine:
    def __init__(self):
        self.bollinger = BollingerBounce()
        self.early_gainer = EarlyGainer()
        self.diamond_hunter = DiamondHunter()
        self.sniper = SniperEntry()
        self.risk_manager = SpotRiskManager()
        
    def generate_all_signals(self, symbols: List[str]) -> Dict:
        all_signals = {
            'bollinger_bounce': [],
            'early_gainer': [],
            'diamond_hunter': [],
            'sniper_entry': [],
            'portfolio_recommendations': []
        }
        
        for symbol in symbols:
            # Simulate market data (replace with real API calls)
            market_data = self._simulate_market_data(symbol)
            prices = market_data['prices']
            
            # 1. Bollinger Bounce
            bb_signal = self.bollinger.generate_signal(symbol, prices, prices[-1])
            if bb_signal['signal'] in ['BUY', 'SELL_PARTIAL', 'SELL_FULL']:
                all_signals['bollinger_bounce'].append({
                    'symbol': symbol,
                    **bb_signal
                })
            
            # 2. Early Gainer
            candles = [{'close': p, 'volume': random.uniform(1000, 5000)} for p in prices]
            eg_signal = self.early_gainer.detect_breakout(symbol, candles, prices[-1])
            if eg_signal['signal'] in ['BUY', 'WATCH']:
                all_signals['early_gainer'].append({
                    'symbol': symbol,
                    **eg_signal
                })
            
            # 3. Diamond Hunter
            dh_signal = self.diamond_hunter.analyze_gem(symbol, market_data)
            if dh_signal['signal'] in ['DIAMOND_DETECTED', 'WATCHLIST']:
                all_signals['diamond_hunter'].append(dh_signal)
            
            # 4. Sniper Entry
            highs = [p * (1 + random.uniform(0, 0.05)) for p in prices]
            lows = [p * (1 - random.uniform(0, 0.05)) for p in prices]
            sniper_signal = self.sniper.check_entry(symbol, prices, highs, lows, prices[-1])
            if sniper_signal['signal'] == 'SNIPER_BUY':
                all_signals['sniper_entry'].append({
                    'symbol': symbol,
                    **sniper_signal
                })
        
        return all_signals
    
    def _simulate_market_data(self, symbol: str) -> Dict:
        """Simulate market data for demo (replace with real exchange API)"""
        base_price = random.uniform(0.1, 500)
        prices = [base_price * (1 + random.uniform(-0.05, 0.05)) for _ in range(50)]
        
        return {
            'symbol': symbol,
            'price': prices[-1],
            'prices': prices,
            'volume_24h': random.uniform(100000, 10000000),
            'volume_change_24h': random.uniform(-30, 100),
            'price_change_24h': random.uniform(-10, 15),
            'price_change_4h': random.uniform(-5, 8),
            'price_vs_30d_low': random.uniform(0, 30),
            'buyer_increase': random.uniform(-10, 50),
            'market_cap': random.uniform(1000000, 100000000)
        }

# Initialize engine
spot_engine = SpotAlphaEngine()

# ========== API ENDPOINTS ==========

@app.get("/health")
def health():
    return {"status": "operational", "version": "3.1 - SPOT ALPHA", "mode": "SPOT ONLY"}

@app.get("/api/alpha")
def get_alpha():
    """Get all Secret Weapons + Spot Strategies"""
    symbols = ['BTC', 'ETH', 'SOL', 'LRC', 'THETA', 'PI', 'ICP', 'TRX', 'ADA', 'DOT']
    
    spot_signals = spot_engine.generate_all_signals(symbols)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'portfolio_value': 2844,
        'mode': 'SPOT_ONLY',
        'strategies': {
            'secret_weapons': {
                'shadow_catch_up': {'missed_alpha_24h': 76.80, 'opportunities': 3},
                'gamma_proxy': {'squeezes_detected': 2},
                'toxicity_detector': {'alerts': 1}
            },
            'spot_strategies': {
                'bollinger_bounce': {
                    'active_signals': len(spot_signals['bollinger_bounce']),
                    'signals': spot_signals['bollinger_bounce'][:3]  # Top 3
                },
                'early_gainer': {
                    'active_signals': len(spot_signals['early_gainer']),
                    'signals': spot_signals['early_gainer'][:3]
                },
                'diamond_hunter': {
                    'gems_found': len([s for s in spot_signals['diamond_hunter'] if s['signal'] == 'DIAMOND_DETECTED']),
                    'signals': spot_signals['diamond_hunter'][:3]
                },
                'sniper_entry': {
                    'active_signals': len(spot_signals['sniper_entry']),
                    'signals': spot_signals['sniper_entry'][:3]
                }
            }
        },
        'recommendations': [
            {
                'symbol': 'LRC',
                'strategy': 'bollinger_bounce',
                'action': 'BUY',
                'confidence': 0.85,
                'entry': 0.285,
                'target': 0.310,
                'allocation': '15%'
            },
            {
                'symbol': 'THETA',
                'strategy': 'early_gainer',
                'action': 'BUY',
                'confidence': 0.78,
                'entry': 1.85,
                'target': 2.05,
                'allocation': '12%'
            }
        ]
    }

@app.get("/api/spot/bollinger")
def get_bollinger_signals():
    """Get Bollinger Bounce opportunities"""
    symbols = ['BTC', 'ETH', 'LRC', 'THETA', 'PI', 'ICP', 'TRX']
    signals = spot_engine.generate_all_signals(symbols)
    return {'strategy': 'bollinger_bounce', 'signals': signals['bollinger_bounce']}

@app.get("/api/spot/early-gainer")
def get_early_gainer_signals():
    """Get Early Gainer momentum signals"""
    symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
    signals = spot_engine.generate_all_signals(symbols)
    return {'strategy': 'early_gainer', 'signals': signals['early_gainer']}

@app.get("/api/spot/diamonds")
def get_diamond_gems():
    """Get Diamond Hunter undervalued gems"""
    symbols = ['LRC', 'THETA', 'PI', 'ICP', 'TRX', 'SOL', 'ADA']
    signals = spot_engine.generate_all_signals(symbols)
    return {
        'gems': [s for s in signals['diamond_hunter'] if s['signal'] == 'DIAMOND_DETECTED'],
        'watchlist': [s for s in signals['diamond_hunter'] if s['signal'] == 'WATCHLIST']
    }

@app.get("/api/spot/sniper")
def get_sniper_entries():
    """Get Sniper Entry precision levels"""
    symbols = ['BTC', 'ETH', 'LRC', 'THETA']
    signals = spot_engine.generate_all_signals(symbols)
    return {'strategy': 'sniper_entry', 'signals': signals['sniper_entry']}

@app.post("/api/spot/execute")
def execute_spot_trade(request: Dict):
    """Execute spot trade (simulation)"""
    symbol = request.get('symbol')
    side = request.get('side')  # BUY or SELL
    size = request.get('size')
    strategy = request.get('strategy')
    
    return {
        'status': 'EXECUTED',
        'symbol': symbol,
        'side': side,
        'size': size,
        'strategy': strategy,
        'timestamp': datetime.now().isoformat(),
        'type': 'SPOT',
        'note': 'Spot accumulation executed. No leverage used.'
    }

@app.get("/api/portfolio")
def get_portfolio():
    return {
        'total_equity': 2844,
        'cash_reserve': 853,  # 30% cash
        'invested': 1991,
        'mode': 'SPOT_ONLY',
        'positions': [
            {'symbol': 'LRC', 'value': 300, 'avg_entry': 0.25, 'current': 0.28, 'strategy': 'bollinger_bounce'},
            {'symbol': 'THETA', 'value': 150, 'avg_entry': 1.65, 'current': 1.82, 'strategy': 'early_gainer'},
            {'symbol': 'PI', 'value': 300, 'avg_entry': 0.015, 'current': 0.018, 'strategy': 'diamond_hunter'},
            {'symbol': 'ICP', 'value': 300, 'avg_entry': 2.75, 'current': 2.85, 'strategy': 'sniper_entry'},
            {'symbol': 'TRX', 'value': 400, 'avg_entry': 0.11, 'current': 0.12, 'strategy': 'bollinger_bounce'}
        ],
        'allocation': {
            'max_single_position': '20%',
            'cash_reserve_target': '30%',
            'current_cash': '30%'
        }
    }

@app.post("/api/emergency/stop")
def emergency_stop():
    return {
        'status': 'STOPPED',
        'message': 'All spot accumulation halted. Positions held. No liquidation risk.',
        'timestamp': datetime.now().isoformat(),
        'type': 'SPOT_HALT'
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
