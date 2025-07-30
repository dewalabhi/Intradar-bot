#!/usr/bin/env python3
"""
Try multiple Fyers API endpoints for v3 token exchange
"""
import requests
import json
import yaml
from datetime import datetime

def try_multiple_endpoints():
    """Try token exchange on multiple Fyers API endpoints"""
    print("🔑 FYERS V3 TOKEN EXCHANGE - MULTIPLE ENDPOINTS")
    print("=" * 50)
    
    # Load configuration
    with open('/workspaces/Intradar-bot/config/fyers_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        fyers_config = config.get('fyers', {})
    
    app_id = fyers_config.get('app_id')
    secret_key = fyers_config.get('secret_key')
    redirect_uri = "http://127.0.0.1:8000"
    
    # Your fresh auth code
    auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiJSUURKNEhCUUVOIiwidXVpZCI6ImQ5ODJhYWUxMGM5YTQ5MTJhYzIxOTI4ODc4MTc3MGZlIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IllBMTE0MTQiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJiNThmYjJhN2FmYTRkZGM5ZWI1YjljNGNlMTAwZmJlNjZlMWE5ZGY3YTg3YThkMzk2NWYwMTAxNyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzUzNDM5OTMyLCJpYXQiOjE3NTM0MDk5MzIsImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc1MzQwOTkzMiwic3ViIjoiYXV0aF9jb2RlIn0.77Okhe9Ra0fEwwv2Q1b8SO7C9N2nx5i1QheET5_csdQ"
    
    # Multiple endpoints to try
    endpoints = [
        ("Production v3", "https://api.fyers.in/api/v3/token"),
        ("Test v3", "https://api-t1.fyers.in/api/v3/token"),
        ("Production v2", "https://api.fyers.in/api/v2/token"),
        ("Test v2", "https://api-t1.fyers.in/api/v2/token")
    ]
    
    # Try v3 payload format first
    v3_payload = {
        "grant_type": "authorization_code",
        "app_id": app_id,
        "secret_key": secret_key,
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
    
    # Also try v2 payload format as fallback
    v2_payload = {
        "grant_type": "authorization_code",
        "appIdHash": f"{app_id}:{secret_key}",
        "code": auth_code
    }
    
    headers = {"Content-Type": "application/json"}
    
    for env_name, endpoint in endpoints:
        print(f"\n{'='*50}")
        print(f"🔄 Trying {env_name}: {endpoint}")
        
        # Use appropriate payload based on API version
        payload = v3_payload if "v3" in endpoint else v2_payload
        
        print(f"📋 Payload format: {'v3' if 'v3' in endpoint else 'v2'}")
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            print(f"📥 Status: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("s") == "ok" and "access_token" in data:
                        access_token = data["access_token"]
                        print(f"\n🎉 SUCCESS with {env_name}!")
                        print(f"🔑 Token: {access_token[:30]}...{access_token[-10:]}")
                        
                        # Save successful token
                        token_data = {
                            "access_token": access_token,
                            "client_id": f"{app_id}:{access_token}",
                            "created_at": datetime.now().isoformat(),
                            "app_id": app_id,
                            "endpoint": endpoint,
                            "environment": env_name
                        }
                        
                        import os
                        os.makedirs('config', exist_ok=True)
                        
                        with open('config/fyers_token.json', 'w') as f:
                            json.dump(token_data, f, indent=2)
                        
                        print(f"💾 Token saved!")
                        return access_token
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON from {env_name}")
                    
            elif response.status_code == 503:
                print(f"⚠️ {env_name} server unavailable (503)")
            else:
                print(f"❌ {env_name} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {env_name} error: {e}")
    
    print(f"\n❌ All endpoints failed - Fyers API appears to be down")
    return None

if __name__ == "__main__":
    token = try_multiple_endpoints()
    if token:
        print(f"\n🚀 Ready for trading with Fyers!")
    else:
        print(f"\n⏳ Try again later when Fyers API is back online")
