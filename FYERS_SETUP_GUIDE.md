# 🏦 FYERS SETUP GUIDE
# ============================================================
# Complete guide to configure Fyers broker integration

## Step 1: Get Fyers API Credentials

### 1.1 Create Fyers Developer Account
1. Visit: https://myapi.fyers.in/
2. Sign up with your Fyers trading account
3. Complete KYC verification if required

### 1.2 Create API App
1. Go to "My Apps" section
2. Click "Create App"
3. Fill in app details:
   - **App Name**: "Intradar Trading Bot"
   - **App Type**: "Web App"
   - **Redirect URI**: `https://127.0.0.1:8080/callback`
   - **Description**: "Automated trading bot for NSE stocks"

### 1.3 Get Credentials
After creating the app, you'll get:
- **App ID**: Format like `ABC123-100`
- **Secret Key**: 40-character alphanumeric string
- **Redirect URI**: Must match exactly what you registered

## Step 2: Configuration Setup

### 2.1 Environment Variables (Recommended)
```bash
# Linux/Mac - Add to ~/.bashrc or ~/.zshrc
export FYERS_APP_ID="your_app_id_here"
export FYERS_SECRET_KEY="your_secret_key_here"
export FYERS_REDIRECT_URI="https://127.0.0.1:8080/callback"

# Windows - Add to system environment variables
set FYERS_APP_ID=your_app_id_here
set FYERS_SECRET_KEY=your_secret_key_here
set FYERS_REDIRECT_URI=https://127.0.0.1:8080/callback
```

### 2.2 Configuration File Method
1. Copy the template:
   ```bash
   cp config/fyers_credentials_template.yaml config/fyers_credentials.yaml
   ```

2. Edit `config/fyers_credentials.yaml` with your credentials:
   ```yaml
   fyers_credentials:
     app_id: "YOUR_ACTUAL_APP_ID"
     secret_key: "YOUR_ACTUAL_SECRET_KEY"
     redirect_uri: "https://127.0.0.1:8080/callback"
   ```

3. Add to `.gitignore`:
   ```bash
   echo "config/fyers_credentials.yaml" >> .gitignore
   ```

### 2.3 Update Paper Trading Config
In `config/paper_trading_config.yaml`, update the fyers section:
```yaml
fyers:
  app_id: "${FYERS_APP_ID}"  # Will read from environment variable
  secret_key: "${FYERS_SECRET_KEY}"
  paper_trading: true  # Keep true for testing
```

## Step 3: Authentication Flow

### 3.1 First-Time Setup
When you first run the bot with Fyers:

1. **Generate Auth URL**: Bot creates authorization URL
2. **Manual Authorization**: You visit URL in browser and login
3. **Get Auth Code**: Fyers redirects with authorization code
4. **Token Exchange**: Bot exchanges code for access token
5. **Store Token**: Token saved for future use

### 3.2 Authentication Code Example
```python
from src.brokers.fyers_broker import FyersBroker

# Initialize broker
broker = FyersBroker(
    app_id="YOUR_APP_ID",
    secret_key="YOUR_SECRET_KEY", 
    redirect_uri="https://127.0.0.1:8080/callback",
    paper_trading=True
)

# Step 1: Get auth URL
auth_url = broker.generate_auth_url()
print(f"Visit this URL: {auth_url}")

# Step 2: After visiting URL and getting code
auth_code = input("Enter the authorization code: ")

# Step 3: Authenticate
success = broker.authenticate(auth_code)
if success:
    print("✅ Authentication successful!")
```

## Step 4: Paper Trading vs Live Trading

### 4.1 Paper Trading Configuration
```yaml
fyers:
  paper_trading: true
  api:
    base_url: "https://api-t1.fyers.in/api/v3"  # Sandbox URL
```

### 4.2 Live Trading Configuration
```yaml
fyers:
  paper_trading: false
  api:
    base_url: "https://api.fyers.in/api/v3"  # Production URL
```

## Step 5: Symbol Format

### 5.1 Yahoo Finance Format (Current)
```
RELIANCE.NS, TCS.NS, HDFCBANK.NS
```

### 5.2 Fyers Format (Required)
```
NSE:RELIANCE-EQ, NSE:TCS-EQ, NSE:HDFCBANK-EQ
```

### 5.3 Auto-Conversion
The bot automatically converts between formats:
```python
# Mapping defined in config
symbol_mapping:
  "RELIANCE.NS": "NSE:RELIANCE-EQ"
  "TCS.NS": "NSE:TCS-EQ"
```

## Step 6: Testing Setup

### 6.1 Test Authentication
```bash
cd /workspaces/Intradar-bot
python -c "
from src.brokers.fyers_broker import FyersBroker
broker = FyersBroker('YOUR_APP_ID', 'YOUR_SECRET', 'https://127.0.0.1:8080/callback', True)
print('✅ Fyers broker initialized successfully!')
"
```

### 6.2 Test with Paper Trading Bot
```bash
# Run with Fyers paper trading
python main_runner.py --mode paper --broker fyers --config config/paper_trading_config.yaml
```

## Step 7: Security Best Practices

### 7.1 Credential Security
- ✅ **Use environment variables** for credentials
- ✅ **Never commit credentials** to version control
- ✅ **Use separate config files** with restricted permissions
- ✅ **Rotate credentials periodically**

### 7.2 File Permissions
```bash
# Secure the credentials file
chmod 600 config/fyers_credentials.yaml
```

### 7.3 Add to .gitignore
```bash
# Add to .gitignore
config/fyers_credentials.yaml
config/fyers_live_config.yaml
*.env
```

## Step 8: Trading Limits and Risk Management

### 8.1 Paper Trading Limits
```yaml
fyers:
  risk:
    max_order_value: 50000      # ₹50K per order
    max_daily_trades: 20        # 20 trades max
    position_size_limit: 100000 # ₹1L total positions
```

### 8.2 Live Trading Limits
```yaml
fyers:
  risk:
    max_daily_loss: 5000        # ₹5K daily loss limit
    max_position_size: 25000    # ₹25K per position
    auto_square_off: true       # Auto close at 3:20 PM
```

## Step 9: Troubleshooting

### 9.1 Common Issues

**Authentication Failed**
- Check app_id and secret_key are correct
- Ensure redirect_uri matches exactly
- Verify app is approved in Fyers portal

**Symbol Not Found**
- Ensure using correct Fyers format: `NSE:SYMBOL-EQ`
- Check if symbol is tradeable
- Verify market segment (EQ for equity)

**Order Rejected**
- Check available margin
- Verify order parameters
- Ensure market is open

### 9.2 Debug Mode
```bash
# Run with debug logging
FYERS_DEBUG=true python main_runner.py --mode paper --broker fyers
```

## Step 10: Going Live

### 10.1 Pre-Live Checklist
- ✅ Complete paper trading for at least 1 week
- ✅ Achieve consistent profitability in paper trading
- ✅ Test all order types and scenarios
- ✅ Verify risk management works correctly
- ✅ Have sufficient trading capital in Fyers account

### 10.2 Switch to Live Trading
1. Update configuration:
   ```yaml
   fyers:
     paper_trading: false
   ```

2. Start with small position sizes
3. Monitor closely for the first few trades
4. Gradually increase position sizes

## 🚨 Important Notes

1. **Paper Trading First**: Always test thoroughly with paper trading
2. **Small Start**: Begin live trading with small amounts
3. **Monitor Closely**: Watch the first few live trades carefully
4. **Risk Management**: Never risk more than you can afford to lose
5. **Market Hours**: NSE trading hours are 9:15 AM - 3:30 PM IST

## 📞 Support

- **Fyers API Support**: support@fyers.in
- **Fyers API Documentation**: https://myapi.fyers.in/docs/
- **Bot Issues**: Check logs in `data/logs/` directory

---

**Ready to configure Fyers?** Start with Step 1 above! 🚀
