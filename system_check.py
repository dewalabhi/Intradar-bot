#!/usr/bin/env python3
"""
🔧 SYSTEM CHECK - Paper Trading Setup Validator
==================================================
Checks if your system is ready for paper trading
"""

import sys
import os
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required for optimal performance")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'backtrader',
        'yfinance', 
        'pandas',
        'numpy',
        'requests',
        'pyyaml',
        'matplotlib',
        'ta'  # Technical analysis library
    ]
    
    missing_packages = []
    
    print("\n📦 Checking Dependencies:")
    print("=" * 30)
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_directory_structure():
    """Check if all required directories and files exist"""
    print("\n📁 Checking Directory Structure:")
    print("=" * 35)
    
    required_paths = [
        "src/",
        "src/strategies/",
        "src/brokers/",
        "src/data/",
        "src/paper_trading/",
        "config/",
        "data/",
        "data/logs/",
        "data/backtests/",
        "src/strategies/balanced_breakout.py",
        "src/brokers/fyers_broker.py",
        "src/brokers/paper_trading_manager.py",
        "src/paper_trading/paper_trader.py",
        "demo_paper_trading.py",
        "test_paper_trading.py",
        "main_runner.py"
    ]
    
    missing_paths = []
    
    for path in required_paths:
        full_path = Path(path)
        if full_path.exists():
            print(f"✅ {path}")
        else:
            print(f"❌ {path}")
            missing_paths.append(path)
            
            # Create missing directories
            if path.endswith('/'):
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"   ↳ Created directory: {path}")
    
    if missing_paths:
        print(f"\n⚠️  Some files/directories are missing")
        return False
    
    print("✅ All required files and directories exist")
    return True

def check_configuration():
    """Check configuration file"""
    print("\n⚙️  Checking Configuration:")
    print("=" * 28)
    
    config_path = Path("config/config.yaml")
    
    if config_path.exists():
        print("✅ config/config.yaml exists")
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check essential config sections
            required_sections = ['trading', 'symbols', 'strategy', 'data']
            for section in required_sections:
                if section in config:
                    print(f"✅ Config section: {section}")
                else:
                    print(f"❌ Missing config section: {section}")
                    
        except Exception as e:
            print(f"❌ Error reading config: {e}")
            return False
    else:
        print("❌ config/config.yaml not found")
        print("   ↳ Creating default configuration...")
        
        default_config = """# Paper Trading Configuration
trading:
  mode: "paper"
  initial_capital: 100000
  commission: 0.001

symbols:
  primary: 
    - 'RELIANCE.NS'
    - 'TCS.NS'
    - 'HDFCBANK.NS'
    - 'INFY.NS'
    - 'HINDUNILVR.NS'

strategy:
  balanced_breakout:
    lookback_period: 20
    volume_threshold: 1.5
    stop_loss_pct: 1.0
    take_profit_pct: 1.5
    risk_per_trade: 0.02

data:
  period: '5d'
  interval: '5m'
  min_bars_required: 50
"""
        
        os.makedirs("config", exist_ok=True)
        with open(config_path, 'w') as f:
            f.write(default_config)
        print("✅ Default configuration created")
    
    return True

def check_market_data_access():
    """Test market data connectivity"""
    print("\n📈 Testing Market Data Access:")
    print("=" * 32)
    
    try:
        import yfinance as yf
        # Test with a simple stock
        ticker = yf.Ticker("RELIANCE.NS")
        hist = ticker.history(period="1d")
        
        if not hist.empty:
            print("✅ Market data access working")
            print(f"   ↳ Latest RELIANCE.NS price: ₹{hist['Close'][-1]:.2f}")
            return True
        else:
            print("❌ No market data received")
            return False
            
    except Exception as e:
        print(f"❌ Market data access failed: {e}")
        print("   ↳ Check internet connection")
        return False

def run_quick_strategy_test():
    """Run a quick strategy validation"""
    print("\n🧪 Quick Strategy Test:")
    print("=" * 24)
    
    try:
        sys.path.append('/workspaces/Intradar-bot')
        from src.strategies.balanced_breakout import BalancedBreakout
        
        # Try to instantiate the strategy
        strategy = BalancedBreakout()
        print("✅ BalancedBreakout strategy loads successfully")
        
        # Check if it has required methods
        required_methods = ['next', 'notify_order', 'notify_trade']
        for method in required_methods:
            if hasattr(strategy, method):
                print(f"✅ Strategy method: {method}")
            else:
                print(f"❌ Missing strategy method: {method}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        return False

def main():
    """Main system check routine"""
    print("🔧 INTRADAR BOT - SYSTEM CHECK")
    print("=" * 50)
    print("Validating paper trading setup...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Configuration", check_configuration),
        ("Market Data Access", check_market_data_access),
        ("Strategy Validation", run_quick_strategy_test)
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_function in checks:
        try:
            if check_function():
                passed_checks += 1
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 SYSTEM CHECK RESULTS: {passed_checks}/{total_checks} PASSED")
    
    if passed_checks == total_checks:
        print("🎉 ALL CHECKS PASSED! Your system is ready for paper trading!")
        print("\n🚀 Ready to start? Run:")
        print("   ./start_paper_trading.sh")
        print("   OR")
        print("   python demo_paper_trading.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("   pip install -r requirements.txt")
        print("   Check internet connection")
        print("   Ensure you're in the correct directory")
    
    print("\n📖 For detailed help: PAPER_TRADING_STARTUP_GUIDE.md")

if __name__ == "__main__":
    main()
