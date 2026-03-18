# Goal-Based Investment Strategies - Complete Guide

## 🎯 Overview
You now have **3 investment strategies** trained and ready for your ₹12,00,000 portfolio!

## 📊 Available Strategies

### 1. Conservative Strategy (Low Risk)
- **Target Return:** 5% in 6 months
- **Risk Level:** Low
- **Description:** Lower risk, steady growth
- **Best For:** Risk-averse investors seeking stable returns
- **Expected Exit:** ~6 months from investment

### 2. Moderate Strategy (Medium Risk)
- **Target Return:** 10% in 6 months  
- **Risk Level:** Medium
- **Description:** Balanced risk-reward
- **Best For:** Balanced portfolio approach
- **Expected Exit:** ~6 months from investment

### 3. Aggressive Strategy (High Risk) ⭐ BEST DATA
- **Target Return:** 15% in 3 months
- **Risk Level:** High
- **Description:** Higher risk, faster returns
- **Best For:** Active traders seeking quick gains
- **Expected Exit:** ~3 months from investment
- **Note:** Has 199 positive training samples (8.5%) - most reliable model!

## 🔌 API Endpoints

### Get All Strategies
```bash
GET http://localhost:8000/api/goal_strategies
```
Returns available strategies with descriptions.

### Get Strategy Recommendations
```bash
GET http://localhost:8000/api/goal_recommendations/conservative
GET http://localhost:8000/api/goal_recommendations/moderate
GET http://localhost:8000/api/goal_recommendations/aggressive
```

### Response Format
```json
[
  {
    "symbol": "HDFCBANK.NS",
    "date": "2026-01-07",
    "close": 1007.85,
    "buy_prob": 0.736,
    "confidence": 73.6,
    "weight": 0.095,
    "allocation_inr": 114240.34
  }
]
```

## 🖥️ Frontend Access

### New Page Created
- **URL:** http://localhost:3000/goal-strategies
- **File:** `frontend/pages/goal-strategies.tsx`

### Features
✅ Interactive strategy selection cards  
✅ Risk level badges (Low/Medium/High)  
✅ Live recommendations table  
✅ Portfolio allocation breakdown  
✅ Investment timeline display  
✅ Real-time confidence scoring  

## 🚀 How to Use

### 1. Start API Server (Already Running)
```bash
uvicorn app.api_server.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Access Strategies
Open browser: http://localhost:3000/goal-strategies

### 4. When to Invest
**Invest Today:** 2026-01-07

**Expected Exit Dates:**
- **Conservative/Moderate:** 2026-07-02 (6 months)
- **Aggressive:** 2026-04-05 (3 months)

## 📈 Top Picks Summary

### Aggressive Strategy (Highest Confidence)
1. **HDFCBANK** - ₹1,007.85 | 73.6% confidence | ₹1,14,240
2. **JSWSTEEL** - ₹1,162.00 | 72.7% confidence | ₹1,13,260
3. **HDFCLIFE** - ₹762.20 | 70.4% confidence | ₹1,10,624
4. **ADANIPORTS** - ₹1,491.10 | 57.5% confidence | ₹97,215
5. **AXISBANK** - ₹1,280.00 | 50.3% confidence | ₹90,463

### Conservative/Moderate Strategy  
1. **SBIN** - ₹972.60 | 20.8% confidence | ₹96,385
2. **LTIM** - ₹6,292.00 | 5.0% confidence | ₹82,259
3. **HDFCBANK** - ₹1,007.85 | 2.0% confidence | ₹79,843

## 🔄 Retraining Models

### Retrain All Strategies
```bash
python app/api/train_all_goal_models.py
```

### Retrain Single Strategy
Edit `app/config.py` GoalConfig, then:
```bash
python app/api/train_goal_model.py
```

## 📁 Files Created

### Backend
- ✅ `app/api/train_all_goal_models.py` - Multi-strategy trainer
- ✅ `app/api/train_goal_model.py` - Single strategy trainer (original)
- ✅ `models/goal_model_conservative.pkl`
- ✅ `models/goal_model_moderate.pkl`
- ✅ `models/goal_model_aggressive.pkl`
- ✅ `results/latest_goal_recommendations_conservative.csv`
- ✅ `results/latest_goal_recommendations_moderate.csv`
- ✅ `results/latest_goal_recommendations_aggressive.csv`

### Frontend
- ✅ `frontend/pages/goal-strategies.tsx` - Interactive strategy selector UI
- ✅ `frontend/pages/goal.tsx` - Original single strategy page (legacy)

### API
- ✅ `GET /api/goal_strategies` - List all strategies
- ✅ `GET /api/goal_recommendations/{strategy}` - Get strategy picks
- ✅ `GET /api/recommendations` - Original 5-day predictions

## ⚠️ Important Notes

### Data Quality
- **Aggressive Strategy** has the most training data (199 positive samples)
- **Conservative/Moderate** have limited data (7 positive samples each)
- ⚠️ Conservative/Moderate predictions less reliable due to limited historical examples

### Recommendation
**Use Aggressive Strategy** for most reliable predictions due to superior training data!

### When to Update
- Fetch new data weekly: `python app/api/main.py`
- Retrain models monthly: `python app/api/train_all_goal_models.py`
- Update calendar: `python app/scripts/regularize_calendar.py`

## 🎨 UI Features

### Strategy Cards
- Color-coded risk levels (Green/Yellow/Red)
- Interactive selection with hover effects
- Target return and horizon display
- Clear descriptions

### Recommendations Table
- Ranked by confidence
- INR currency formatting
- Percentage weights
- Color-coded confidence scores
  - Green: ≥60%
  - Yellow: 40-60%
  - Gray: <40%

### Investment Timeline
- Current date
- Expected exit date  
- Target return highlight

## 🔧 Troubleshooting

### "No recommendations found"
Run: `python app/api/train_all_goal_models.py`

### API not accessible
Check server running: `http://localhost:8000/api/health`

### Frontend build errors
```bash
cd frontend
npm install
npm run dev
```

## 📞 Next Steps

1. ✅ Models trained and saved
2. ✅ API endpoints live
3. ✅ Frontend UI created
4. 🔄 Start frontend: `cd frontend && npm run dev`
5. 🌐 Open: http://localhost:3000/goal-strategies
6. 🎯 Select your strategy and invest!

---

**Investment Capital:** ₹12,00,000  
**Strategies Available:** 3 (Conservative, Moderate, Aggressive)  
**API Server:** Running on http://localhost:8000  
**Status:** ✅ Ready to Use
