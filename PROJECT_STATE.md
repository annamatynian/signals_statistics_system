# 📊 Signal Statistics System - Project State

**Last Updated:** 2025-11-18
**Current Branch:** `claude/setup-windows-testing-01XvKvtJugH1YWC9cXnYMEs7`
**Status:** ✅ Fully Implemented & Tested

---

## 🎯 Project Purpose

Track and analyze **winrate of Telegram trading signal channels**.

- Add signals with **channel_name**, **TP**, **SL**
- System automatically determines **WIN/LOSS** when price hits TP or SL
- Calculate **winrate per channel** (wins / total closed signals)
- View statistics in **Gradio web UI**

---

## 📦 Data Models

### 1. SignalTarget (`src/models/signal.py`)

**Complete field list:**

```python
# Basic Info
id: Optional[str]                    # Unique identifier (UUID)
name: str                            # Signal name
symbol: str                          # Trading pair (BTCUSDT, ETHUSDT)
exchange: Optional[ExchangeType]     # binance/bybit/coinbase

# Channel Tracking (KEY FIELD!)
channel_name: str                    # Telegram channel name

# Price Levels
target_price: float                  # Entry target price
take_profit: Optional[float]         # TP level (single)
take_profit_targets: list[TakeProfitTarget]  # TP ladder (tp1, tp2, tp3)
stop_loss: Optional[float]           # SL level
condition: SignalCondition           # above/below/equal

# Position Tracking
position_open_date: Optional[datetime]     # When position opened
position_entry_price: Optional[float]      # Actual entry price
closed_at: Optional[datetime]              # When position closed (TP/SL hit)

# Status & Outcome
status: SignalStatus                 # active/closed/triggered/paused/expired
outcome: SignalOutcome               # win/loss/pending
active: bool                         # Boolean flag

# Dates
created_at: datetime                 # Signal creation time
updated_at: datetime                 # Last update
last_triggered_at: Optional[datetime]  # Last trigger time

# Other
triggered_count: int                 # Number of triggers
user_id: Optional[str]              # User identifier
notes: Optional[str]                # User notes
percentage_threshold: Optional[float]  # For percent_change condition
max_triggers: Optional[int]         # Max number of triggers
```

**Enums:**
- `SignalStatus`: active, triggered, paused, expired, closed
- `SignalOutcome`: win, loss, pending
- `SignalCondition`: above, below, equal, percent_change
- `ExchangeType`: binance, bybit, coinbase, okex, kraken

---

### 2. Channel (`src/models/channel.py`)

```python
id: Optional[str]           # Unique channel ID (hash of name)
name: str                   # Channel name (REQUIRED)
telegram_url: Optional[str] # Telegram channel URL
description: Optional[str]  # Channel description
is_active: bool            # Whether channel is active
created_at: datetime       # Creation timestamp
updated_at: datetime       # Last update
```

---

### 3. ChannelStatistics (`src/models/channel.py`)

```python
channel_id: str            # Channel identifier
channel_name: str          # Channel name

# Counts
total_signals: int         # Total signals
active_signals: int        # Currently active
closed_signals: int        # Closed signals

# Outcomes
wins: int                  # Winning signals (TP hit)
losses: int                # Losing signals (SL hit)
pending: int              # Still pending

# Metrics
winrate: float            # Win rate % (wins/closed * 100)
last_updated: datetime    # Stats last updated
```

**Formula:**
```
winrate = (wins / closed_signals) * 100
```

---

## 🗂️ Storage Structure

**File:** `data/signals.json`

```json
{
  "signals": [
    {
      "id": "uuid-here",
      "name": "BTC Long Position",
      "channel_name": "VIP Crypto Signals",
      "symbol": "BTCUSDT",
      "exchange": "binance",
      "target_price": 90000,
      "take_profit": 100000,
      "stop_loss": 85000,
      "status": "active",
      "outcome": "pending",
      "position_open_date": null,
      "position_entry_price": null,
      "closed_at": null,
      "created_at": "2025-11-18T10:00:00",
      ...
    }
  ],
  "channels": [
    {
      "id": "channel#abc123",
      "name": "VIP Crypto Signals",
      "is_active": true,
      "created_at": "2025-11-18T09:00:00",
      ...
    }
  ],
  "statistics": {
    "VIP Crypto Signals": {
      "channel_name": "VIP Crypto Signals",
      "total_signals": 12,
      "closed_signals": 10,
      "wins": 7,
      "losses": 3,
      "winrate": 70.0
    }
  },
  "users": {}
}
```

---

## 🛠️ Services

### 1. ChannelManager (`src/services/channel_manager.py`)

**Methods:**
- `add_channel(name, telegram_url, description)` - Add new channel
- `get_channel(channel_id)` - Get channel by ID
- `get_channel_by_name(name)` - Get channel by name
- `list_channels()` - List all channels
- `get_channel_statistics(channel_name)` - Get stats for channel

---

### 2. StatsCalculator (`src/services/stats_calculator.py`)

**Methods:**
- `calculate_channel_stats(channel_name)` - Calculate stats for one channel
- `calculate_all_stats()` - Calculate stats for all channels
- `get_overall_stats()` - Get overall system stats
- `get_best_channel()` - Get channel with highest winrate
- `get_worst_channel()` - Get channel with lowest winrate

---

### 3. SignalManager (`src/services/signal_manager.py`)

**Methods:**
- `add_signal(signal)` - Add new signal
- `get_active_signals()` - Get all active signals
- `close_signal(signal_id, outcome, closed_price)` - Close signal (WIN/LOSS)
- `update_signal_status()` - Update signal status

**Logic:**
- When price hits **TP** → outcome = WIN, status = CLOSED
- When price hits **SL** → outcome = LOSS, status = CLOSED
- Automatically updates channel statistics after closing

---

### 4. SheetsImporter (`src/services/sheets_importer.py`)

**Methods:**
- `read_signals_from_sheet(sheet_name)` - Read signals from Google Sheets
- `import_signals(sheet_name, auto_create_channels)` - Import into database
- `test_connection()` - Test Google Sheets connection

**Required Google Sheets columns:**
- `channel_name` (required)
- `symbol` (required)
- `take_profit` (required)
- `stop_loss` (required)
- `exchange` (optional, default: binance)
- `active` (optional, default: TRUE)
- `name` (optional, auto-generated)

---

## 🖥️ User Interfaces

### 1. Gradio Web UI (`src/ui/gradio_interface.py`)

**Tabs:**
1. **➕ Add Signal** - Form to add new signals
2. **📋 Active Signals** - Table of active signals
3. **📊 Channel Statistics** - Winrate per channel
4. **📈 Summary Statistics** - Overall stats, best/worst channels

**Launch:** `python3 run_simple.py` → http://localhost:7860

---

### 2. Google Sheets Import (`import_from_sheets.py`)

**Usage:**
```bash
# Set environment variables
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
export GOOGLE_SHEETS_SPREADSHEET_ID='your-sheet-id'

# Run import
python3 import_from_sheets.py [sheet_name]
```

**Features:**
- Preview signals before import
- Auto-create channels
- Validation (TP > SL, required fields)
- Detailed import report

---

## 🚀 How to Run

### Option 1: UI Only (Recommended for Testing)

```bash
# 1. Add demo data (optional)
python3 add_demo_data.py

# 2. Launch UI
python3 run_simple.py

# 3. Open browser
http://localhost:7860
```

### Option 2: Full System (with background price checking)

```bash
python3 run.py
```

**Note:** Requires Bybit API setup (optional - can run without it)

---

## 📁 Project Structure

```
signals_statistics_system/
├── data/
│   └── signals.json              # Database (auto-created)
│
├── src/
│   ├── models/
│   │   ├── signal.py            # SignalTarget, SignalStatus, SignalOutcome
│   │   ├── channel.py           # Channel, ChannelStatistics
│   │   └── price.py             # Price models
│   │
│   ├── services/
│   │   ├── signal_manager.py    # Signal CRUD + TP/SL logic
│   │   ├── channel_manager.py   # Channel management
│   │   ├── stats_calculator.py  # Winrate calculations
│   │   ├── sheets_importer.py   # Google Sheets import
│   │   ├── price_checker.py     # Price monitoring
│   │   └── sheets_reader.py     # (legacy, use sheets_importer)
│   │
│   ├── storage/
│   │   ├── base.py              # Storage interface
│   │   └── json_storage.py      # JSON file storage
│   │
│   ├── ui/
│   │   └── gradio_interface.py  # Gradio web UI
│   │
│   ├── exchanges/
│   │   ├── binance.py           # Binance exchange
│   │   ├── bybit.py             # Bybit exchange (optional)
│   │   └── coinbase.py          # Coinbase exchange
│   │
│   └── main_new.py              # Main application entry
│
├── run.py                       # Full system launcher
├── run_simple.py                # UI-only launcher (NO asyncio conflicts)
├── run_ui_only.py               # Alternative UI launcher
├── import_from_sheets.py        # Google Sheets import script
├── add_demo_data.py             # Demo data generator
├── test_integration.py          # Integration tests
│
├── docs/
│   ├── PROJECT_STATE.md         # THIS FILE - Current state snapshot
│   ├── README_STATISTICS.md     # Main documentation
│   ├── TESTING_GUIDE.md         # Testing instructions
│   ├── GOOGLE_SHEETS_IMPORT.md  # Sheets import guide
│   ├── SHEETS_QUICKSTART.md     # Quick start for sheets
│   └── QUICK_TEST.md            # Quick test commands
│
├── google_sheets_template.csv   # Template for Google Sheets
├── requirements.txt             # Dependencies
└── .env.example                 # Environment variables template
```

---

## 🌿 Git Branches

### Main Development Branch
**`claude/adapt-signal-statistics-01UcVyaKgAYXmqwmrXiHChP8`** ✅ Current

All features implemented and tested:
- ✅ Channel statistics system
- ✅ Gradio web UI
- ✅ Google Sheets import
- ✅ TP/SL win/loss detection
- ✅ Winrate calculations
- ✅ Demo data generator
- ✅ Integration tests
- ✅ Full documentation

### Other Branches
- `main` - Protected, merge via PR
- `claude/setup-project-base-019GdzcsWhuKnd64BpwdvhmB` - Old base
- `claude/setup-windows-testing-01XvKvtJugH1YWC9cXnYMEs7` - Windows testing

---

## 🔑 Environment Variables

Required for Google Sheets import:

```bash
# .env file
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_SHEETS_SPREADSHEET_ID=1abc...xyz
```

Optional (for exchange APIs):
```bash
BINANCE_API_KEY=your-key
BINANCE_API_SECRET=your-secret
```

---

## ✅ What's Implemented

### Core Features
- ✅ Signal model with channel_name, TP, SL
- ✅ Channel model
- ✅ Statistics model and calculations
- ✅ JSON storage with channels/statistics support
- ✅ WIN/LOSS detection (TP/SL logic)
- ✅ Winrate calculation per channel
- ✅ Overall system statistics

### User Interfaces
- ✅ Gradio web UI (4 tabs)
- ✅ Google Sheets import (CLI)
- ✅ Demo data generator
- ✅ Integration tests

### Services
- ✅ ChannelManager
- ✅ StatsCalculator
- ✅ SignalManager (with TP/SL logic)
- ✅ SheetsImporter
- ✅ PriceChecker (Binance, Bybit optional)

---

## ❌ What's NOT Implemented

- ❌ Authentication system (removed)
- ❌ Push notifications (removed)
- ❌ Telegram bot (not needed)
- ❌ DynamoDB storage (only JSON storage)
- ❌ AWS Lambda deployment (local only)

---

## 🧪 Testing

### Quick Test (2 minutes)
```bash
python3 add_demo_data.py
python3 run_simple.py
# Open http://localhost:7860
```

**Expected results:**
- 34 signals (4 active, 30 closed)
- 3 channels with winrates:
  - Pro Traders Hub: 80%
  - VIP Crypto Signals: 70%
  - Budget Trading Channel: 40%

### Integration Test
```bash
python3 test_integration.py
# Should print: ✅ ALL TESTS PASSED!
```

### Manual Testing Steps
See `TESTING_GUIDE.md` for detailed 6-step testing plan.

---

## 🐛 Known Issues

1. **Bybit not available** - pybit installation fails, marked as optional
2. **403 error on git push to main** - main branch is protected (normal)
3. **Gradio asyncio conflicts** - use `run_simple.py` instead of `run.py`

---

## 📝 Key Files to Remember

| File | Purpose |
|------|---------|
| `src/models/signal.py` | **Signal model** - ALL fields are here! |
| `src/models/channel.py` | **Channel + Statistics models** |
| `src/services/stats_calculator.py` | **Winrate calculations** |
| `src/services/sheets_importer.py` | **Google Sheets import** |
| `src/ui/gradio_interface.py` | **Web UI** |
| `data/signals.json` | **Database** (signals, channels, statistics) |
| `run_simple.py` | **Launch UI** (recommended) |
| `PROJECT_STATE.md` | **THIS FILE** - Read first! |

---

## 🎯 Quick Reference

**Add signal via UI:**
```
python3 run_simple.py → http://localhost:7860 → "➕ Add Signal" tab
```

**Import from Google Sheets:**
```bash
export GOOGLE_SERVICE_ACCOUNT_JSON='...'
export GOOGLE_SHEETS_SPREADSHEET_ID='...'
python3 import_from_sheets.py
```

**View statistics:**
```
python3 run_simple.py → "📊 Channel Statistics" tab
```

**Add demo data:**
```bash
python3 add_demo_data.py
```

---

## 📞 Next Steps

1. **Test on Windows** - Pull branch, run `python run_simple.py`
2. **Setup Google Sheets** - Follow `SHEETS_QUICKSTART.md`
3. **Import real signals** - Use `import_from_sheets.py`
4. **Monitor winrates** - View in Gradio UI

---

**🔄 Remember to update this file when:**
- Adding new models or fields
- Creating new services
- Changing storage structure
- Adding new features
- Changing branch strategy
