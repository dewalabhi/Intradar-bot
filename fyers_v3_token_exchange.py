#!/usr/bin/env python3
"""
Fyers v3 Token Exchange Script
Exchange auth code for access token using the v3 API
"""
import requests
import json
import yaml
from datetime import datetime

def exchange_token_v3():
    """Exchange auth code for access token using Fyers v3 API"""
    print("🔑 FYERS V3 TOKEN EXCHANGE")
    print("=" * 40)
    
    # Load configuration
    with open('/workspaces/Intradar-bot/config/fyers_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        fyers_config = config.get('fyers', {})
    
    app_id = fyers_config.get('app_id')  # RQDJ4HBQEN-100
    secret_key = fyers_config.get('secret_key')  # 1UHBSCQQRR
    redirect_uri = "http://127.0.0.1:8000"
    
    print(f"📋 App ID: {app_id}")
    print(f"📋 Secret Key: {secret_key[:8]}...")
    
    # Your fresh auth code
    auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiJSUURKNEhCUUVOIiwidXVpZCI6ImQ5ODJhYWUxMGM5YTQ5MTJhYzIxOTI4ODc4MTc3MGZlIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IllBMTE0MTQiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJiNThmYjJhN2FmYTRkZGM5ZWI1YjljNGNlMTAwZmJlNjZlMWE5ZGY3YTg3YThkMzk2NWYwMTAxNyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzUzNDM5OTMyLCJpYXQiOjE3NTM0MDk5MzIsImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc1MzQwOTkzMiwic3ViIjoiYXV0aF9jb2RlIn0.77Okhe9Ra0fEwwv2Q1b8SO7C9N2nx5i1QheET5_csdQ"
    
    print(f"✅ Using auth code (length: {len(auth_code)})")
    
    # Fyers v3 API token exchange payload
    payload = {
        "grant_type": "authorization_code",
        "app_id": app_id,
        "secret_key": secret_key,
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"\n🔄 Token Exchange using Fyers v3 API...")
    print(f"📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    # Try v3 API endpoint
    endpoint = "https://api.fyers.in/api/v3/token"
    
    try:
        print(f"\n📤 Making request to: {endpoint}")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📋 Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📊 Response JSON:")
                print(json.dumps(data, indent=2))
                
                if data.get("s") == "ok" and "access_token" in data:
                    access_token = data["access_token"]
                    print(f"\n🎉 SUCCESS! Access token received!")
                    print(f"🔑 Access Token: {access_token[:30]}...{access_token[-10:]}")
                    
                    # Save token to config
                    token_data = {
                        "access_token": access_token,
                        "client_id": f"{app_id}:{access_token}",
                        "created_at": datetime.now().isoformat(),
                        "app_id": app_id,
                        "expires_in": data.get("expires_in", 86400),
                        "api_version": "v3"
                    }
                    
                    import os
                    os.makedirs('config', exist_ok=True)
                    
                    with open('config/fyers_token.json', 'w') as f:
                        json.dump(token_data, f, indent=2)
                    
                    print(f"💾 Token saved to config/fyers_token.json")
                    
                    # Test the token with profile API
                    print(f"\n🧪 Testing token with profile API...")
                    test_profile(app_id, access_token)
                    
                    return access_token
                    
                else:
                    print(f"❌ Token exchange failed: {data.get('message', 'Unknown error')}")
                    print(f"📋 Full response: {data}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"📋 Raw response: {response.text}")
                
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def test_profile(app_id, access_token):
    """Test the access token with profile API"""
    try:
        profile_url = "https://api.fyers.in/api/v3/profile"
        headers = {
            "Authorization": f"{app_id}:{access_token}"
        }
        
        print(f"👤 Profile URL: {profile_url}")
        print(f"🔑 Authorization: {app_id}:{access_token[:20]}...")
        
        response = requests.get(profile_url, headers=headers, timeout=10)
        
        print(f"📥 Profile Status: {response.status_code}")
        print(f"📋 Profile Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("s") == "ok":
                user_data = data.get("data", {})
                print(f"✅ Profile working! User: {user_data.get('fy_id', 'N/A')}")
                return True
            else:
                print(f"⚠️ Profile error: {data.get('message')}")
        else:
            print(f"⚠️ Profile request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Profile test error: {e}")
    
    return False

if __name__ == "__main__":
    try:
        token = exchange_token_v3()
        if token:
            print(f"\n🎉 SUCCESS! Fyers v3 integration complete! 🚀")
            print(f"✅ Token: {token[:30]}...{token[-10:]}")
        else:
            print(f"\n❌ Token exchange failed")
    except Exception as e:
        print(f"\n❌ Script error: {e}")
        import traceback
        traceback.print_exc()
