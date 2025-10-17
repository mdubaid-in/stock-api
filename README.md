# Stock Market Data Streaming API (Twelve Data)

Real-time Indian stock market data streaming application using Twelve Data API. Automatically fetches live market data during trading hours (9:15 AM - 3:30 PM IST) with intelligent rate limiting and auto-reconnection.

## Features

- ✅ **Simple API Key Authentication**: One-time setup, no daily approvals needed
- 📊 **Indian Stock Market**: Full support for NSE & BSE stocks
- 🚀 **Dual Mode Support**: 
  - **WebSocket** (Real-time streaming, 8 connections, no API credits used)
  - **REST API** (Polling-based, 55 calls/min, uses API credits)
- ⚡ **Smart Rate Limiting**: Built-in rate limiter respects Twelve Data API limits
- 🔄 **Auto-Reconnection**: Automatic reconnection with exponential backoff
- ⏰ **Market Hours Aware**: Automatically starts/stops based on Indian market hours
- 🎯 **Multi-Symbol Support**: Track multiple stocks simultaneously
- 🔐 **Environment-based Config**: Secure credential management via .env file
- 📊 **Database Ready**: Prepared for MongoDB integration for tick data storage
- 🆓 **Free Tier Friendly**: Works with free Twelve Data plan (8 requests/min)
- 💡 **Easy Mode Switch**: One-line config to switch between WebSocket and REST API

## Prerequisites

- Python 3.9 or higher
- Twelve Data account (free signup available)

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd stock-api
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get Your Free API Key

1. Visit [Twelve Data](https://twelvedata.com/)
2. Click **"Sign Up Free"**
3. Complete registration (no credit card required)
4. Go to your [Dashboard](https://twelvedata.com/account/api-keys)
5. Copy your **API Key**

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
# Twelve Data API Key (Required)
TWELVEDATA_API_KEY=your_api_key_here

# MongoDB Configuration (Optional - for data storage)
MONGO_JOB_SERVER_URI=mongodb://localhost:27017/
MONGO_DB_NAME=stock_market
```

## Configuration

### Choose Data Source (WebSocket vs REST API)

**In `main.py`, line 29:**

```python
# Set to True for WebSocket (recommended for paid plans)
USE_WEBSOCKET = True  # Real-time streaming, no API credits used

# Set to False for REST API
USE_WEBSOCKET = False  # Polling every 10 seconds, uses API credits
```

**For detailed comparison, see [WEBSOCKET_VS_API.md](WEBSOCKET_VS_API.md)**

### Configuring Symbols to Track

Edit `main.py` to configure the symbols you want to track:

```python
SYMBOLS: List[str] = [
    "RELIANCE",   # Reliance Industries
    "TCS",        # Tata Consultancy Services
    "HDFCBANK",   # HDFC Bank
    "INFY",       # Infosys
    "ICICIBANK",  # ICICI Bank
]
```

### Available Predefined Symbols

The following Indian NSE stocks are pre-configured in `utils/instruments.py`:

| Symbol | Company Name |
|--------|--------------|
| RELIANCE | Reliance Industries |
| TCS | Tata Consultancy Services |
| HDFCBANK | HDFC Bank |
| INFY | Infosys |
| ICICIBANK | ICICI Bank |
| HINDUNILVR | Hindustan Unilever |
| ITC | ITC Limited |
| SBIN | State Bank of India |
| BHARTIARTL | Bharti Airtel |
| KOTAKBANK | Kotak Mahindra Bank |
| LT | Larsen & Toubro |
| AXISBANK | Axis Bank |
| ASIANPAINT | Asian Paints |
| MARUTI | Maruti Suzuki |
| WIPRO | Wipro |
| TATAMOTORS | Tata Motors |
| TATASTEEL | Tata Steel |
| SUNPHARMA | Sun Pharmaceutical |
| TITAN | Titan Company |
| ULTRACEMCO | UltraTech Cement |
| BAJFINANCE | Bajaj Finance |
| TECHM | Tech Mahindra |
| POWERGRID | Power Grid Corporation |
| NESTLEIND | Nestle India |
| HCLTECH | HCL Technologies |

## Usage

### Running the Application

```bash
python main.py
```

The application will:
1. Validate your Twelve Data API key
2. Wait for market hours if market is closed
3. Connect to Twelve Data API
4. Fetch live data for configured symbols every 10 seconds
5. Automatically handle rate limiting and reconnections
6. Stop gracefully when market closes or on Ctrl+C

### Sample Output

```
============================================================
🚀 Stock Market Data Streaming Application (Twelve Data API)
============================================================
📅 Current time (IST): 2025-10-15 09:14:30
📊 Tracking 5 Indian NSE stocks: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK
🔑 Validating Twelve Data API key...
✅ API key is valid
📝 Initializing instruments...
✅ Initialized 5 instruments
✅ Connected. Starting data polling...
📊 RELIANCE: Price=2450.30, Volume=234567, Change=15.50 (0.63%)
📊 TCS: Price=3625.75, Volume=89234, Change=-12.25 (-0.34%)
📊 HDFCBANK: Price=1650.80, Volume=156789, Change=8.30 (0.50%)
...
```

## Rate Limits

Twelve Data API has the following limits based on your plan:

| Plan | Requests/Minute | Requests/Day |
|------|----------------|--------------|
| Free | 8 | 800 |
| Basic | 800 | 100,000 |
| Pro | 3,200 | Unlimited |
| Enterprise | Custom | Unlimited |

**The application automatically respects these limits** with built-in rate limiting.

### Free Plan Optimization

- **Polling Interval**: 10 seconds (6 updates/min per symbol)
- **Rate Limiter**: Ensures max 8 requests/minute
- **Conservative Approach**: Leaves buffer for API key validation

## Project Structure

```
stock-api/
├── main.py                       # Main application entry point
├── requirements.txt              # Python dependencies
├── .env                         # Environment variables (create this)
├── README.md                    # This file
├── auth/
│   └── auth.py                  # Twelve Data authentication
├── classes/
│   ├── TwelveDataManager.py     # Data fetching manager with rate limiting
│   └── GrowwWebSocketManager.py # (Legacy - can be removed)
├── config/
│   └── env.py                   # Environment variable loader
├── db/
│   └── mongoClient.py           # MongoDB client (optional)
├── log/
│   └── logging.py               # Custom logger with colors
└── utils/
    ├── instruments.py           # Instrument management
    └── marketHours.py           # Market hours utility
```

## Key Components

### 1. Authentication (`auth/auth.py`)
- Simple API key authentication
- Automatic client initialization
- API key validation

### 2. Data Manager (`classes/TwelveDataManager.py`)
- Polling-based data fetching
- Rate limiting (respects free tier limits)
- Automatic reconnection with exponential backoff
- Health monitoring

### 3. Rate Limiter
- Per-minute rate limiting
- Thread-safe implementation
- Automatic throttling

### 4. Instrument Manager (`utils/instruments.py`)
- Symbol management
- Instrument configuration
- Pre-configured popular Indian stocks

### 5. Market Hours (`utils/marketHours.py`)
- IST timezone handling
- Market open/close detection
- Automatic scheduling

## Database Integration (Optional)

To save tick data to MongoDB, uncomment the database save code in `classes/TwelveDataManager.py`:

```python
def processQuoteData(self, data: Dict) -> None:
    # ... existing code ...
    
    # Save to database
    from db.mongoClient import mongoClient
    collection = mongoClient.get_collection('market_data')
    collection.insert_one({
        'symbol': symbol,
        'price': price,
        'volume': volume,
        'change': change,
        'percent_change': percent_change,
        'timestamp': getCurrentTimeIST()
    })
```

## Troubleshooting

### Authentication Failed
- Verify `TWELVEDATA_API_KEY` in `.env` file
- Check API key is correct on [Twelve Data Dashboard](https://twelvedata.com/account/api-keys)
- Ensure you have internet connection

### No Data Received
- Verify market is open (9:15 AM - 3:30 PM IST, Mon-Fri)
- Check symbols are valid NSE stocks
- Ensure you haven't exceeded daily rate limits

### Rate Limit Errors
- The application automatically handles rate limits
- If on free plan, reduce number of tracked symbols
- Consider upgrading to Basic or Pro plan for higher limits

### Symbol Not Found
- Verify symbol exists on NSE
- Add custom symbols to `POPULAR_INSTRUMENTS` in `utils/instruments.py`
- Check spelling matches Twelve Data's symbol format

## API Documentation

For complete Twelve Data API documentation, visit:
- [Twelve Data Docs](https://twelvedata.com/docs)
- [Python Client](https://github.com/twelvedata/twelvedata-python)
- [API Reference](https://twelvedata.com/docs#getting-started)

## Upgrading Your Plan

To handle more symbols or get faster updates, consider upgrading:

1. Visit [Twelve Data Pricing](https://twelvedata.com/pricing)
2. Choose a plan (Basic, Pro, or Enterprise)
3. Update `RATE_LIMIT_PER_MINUTE` in `classes/TwelveDataManager.py`:
   ```python
   RATE_LIMIT_PER_MINUTE = 800  # For Basic plan
   # or
   RATE_LIMIT_PER_MINUTE = 3200  # For Pro plan
   ```
4. Optionally reduce `POLLING_INTERVAL` for faster updates

## Features Comparison

| Feature | Free Plan | Basic Plan | Pro Plan |
|---------|-----------|------------|----------|
| API Calls/Min | 8 | 800 | 3,200 |
| Daily Limit | 800 | 100,000 | Unlimited |
| Real-time Data | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ✅ | ✅ |
| Technical Indicators | ✅ | ✅ | ✅ |
| WebSocket | ❌ | ❌ | ✅ |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Support

For Twelve Data API issues, contact: [hello@twelvedata.com](mailto:hello@twelvedata.com)

For application issues, create an issue in this repository.

---

**⚠️ Disclaimer**: This is a development tool. Use at your own risk. Always test thoroughly before using in production. Market data and trading involve financial risk.

## Quick Start Summary

1. **Get API Key**: [twelvedata.com](https://twelvedata.com/) (free signup)
2. **Install**: `pip install -r requirements.txt`
3. **Configure**: Create `.env` with your API key
4. **Run**: `python main.py`

That's it! The application handles everything else automatically! 🚀
