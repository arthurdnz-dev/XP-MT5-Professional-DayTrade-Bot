# XP-MT5-Professional-DayTrade-Bot

## 📈 XP/MT5 Professional Algorithmic Trading System

Fully automated system focused on **Senior Risk Management** and **Highly Reliable Context Analysis**. Uses Python for advanced market analysis (indicators and filters) and XP Investimentos' MetaTrader 5 (MT5) for robust order routing.

⚠️ **RISK DISCLAIMER:** Algorithmic trading, especially Day Trading, involves significant risks. This system was built to maximize robustness and minimize errors, but **DOES NOT GUARANTEE PROFITS**. Always trade first on the MT5 **DEMO** account.

### ⚙️ Prerequisites

1. **XP Investimentos Account** and **XP MetaTrader 5 (MT5) Terminal** (Simulation or Real).

2. Python 3.10+ installed.

3. Dependencies installed (`pip install -r requirements.txt`).

### 🔑 Security Configuration

Your MT5 credentials are read from the **`.env`** file and should **NEVER** be committed to Git.

Create the `.env` file in the root directory:

```ini
MT5_LOGIN=YOUR_MT5_LOGIN MT5_PASSWORD=YOUR_MT5_PASSWORD
MT5_SERVER=XP-DEMO