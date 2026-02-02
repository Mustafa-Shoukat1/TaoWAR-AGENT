import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

def test_daily_endpoint():
    """Test the daily report endpoint with sample data"""
    
    print("🧪 Testing Daily Report Endpoint...")
    
    url = "https://tao-war-backend.onrender.com/daily/internal"
    headers = {
        "x-api-key": "7febb13aee3d64c20ecd7d1d312cd24c7446e144bd594c1f858d465d9a40dfa3",
        "Content-Type": "application/json"
    }
    
    # Sample payload for testing
    test_payload = {
        "title": "Test Daily Report - Crypto Market Analysis",
        "content": """<div className="card-title">Digital Asset Market Intelligence Test</div>

## Regulatory Developments
Bitcoin regulatory clarity continues to evolve across major jurisdictions. Recent policy announcements from the EU and US signal increased institutional adoption pathways.

## Technology Updates  
Layer 2 scaling solutions show significant transaction volume growth. DeFi protocols implement enhanced security measures following recent audits.

## Market Sentiment
Institutional investors display cautious optimism amid macroeconomic uncertainties. Retail participation remains steady with focus on established cryptocurrencies.
""",
        "generatedBy": "Test Script",
        "descriptionSummary": "This test report examines key regulatory developments, technology updates, and market sentiment in the digital asset space. It provides insights into institutional adoption trends, DeFi protocol enhancements, and current market dynamics shaping the cryptocurrency landscape."
    }
    
    try:
        print(f"📤 Sending request to: {url}")
        response = requests.post(url, json=test_payload, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Daily endpoint test SUCCESSFUL!")
            response_data = response.json()
            print(f"📋 Response: {json.dumps(response_data, indent=2)}")
        else:
            print("❌ Daily endpoint test FAILED!")
            print(f"📋 Error Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    print("-" * 60)

def test_weekly_endpoint():
    """Test the weekly report endpoint with sample data"""
    
    print("🧪 Testing Weekly Report Endpoint...")
    
    url = "https://tao-war-backend.onrender.com/weekly/internal"
    headers = {
        "x-api-key": "7febb13aee3d64c20ecd7d1d312cd24c7446e144bd594c1f858d465d9a40dfa3",
        "Content-Type": "application/json"
    }
    
    # Sample influencer stats for testing
    sample_influencer_stats = [
        {
            "rank": 1,
            "name": "Michael Saylor",
            "handle": "saylor",
            "followers": 3500000,
            "likes": 15000,
            "retweets": 8000,
            "replies": 2500,
            "quotes": 1200,
            "engagement_rate": 0.76
        },
        {
            "rank": 2,
            "name": "Vitalik Buterin",
            "handle": "VitalikButerin",
            "followers": 5200000,
            "likes": 22000,
            "retweets": 12000,
            "replies": 3500,
            "quotes": 1800,
            "engagement_rate": 0.75
        },
        {
            "rank": 3,
            "name": "CZ",
            "handle": "cz_binance",
            "followers": 8500000,
            "likes": 18000,
            "retweets": 9500,
            "replies": 2800,
            "quotes": 1500,
            "engagement_rate": 0.38
        }
    ]
    
    # Sample payload for testing
    test_payload = {
        "title": "Test Weekly Report - Digital Asset Market Roundup",
        "content": """<div className="card-title">Weekly Digital Asset Market Intelligence Test</div>

## Introduction 

### Total Curated Influencers: 50 
This week's analysis synthesizes insights from 50 leading voices in the digital asset ecosystem, providing comprehensive coverage of market developments, regulatory shifts, and technological innovations shaping the cryptocurrency landscape.

## DeFi Innovation and Protocol Updates
Decentralized finance protocols demonstrate remarkable resilience amid market volatility. New governance proposals focus on enhanced security measures and sustainable yield mechanisms.

## Regulatory Landscape Evolution  
Global regulatory frameworks continue to mature with clearer guidelines emerging from major jurisdictions. Institutional compliance requirements drive adoption of standardized reporting mechanisms.

## Institutional Market Movements
Corporate treasury allocations to digital assets show measured growth. Pension funds and sovereign wealth funds explore structured crypto investment products.

## What to Watch Next Week
Monitor upcoming Fed policy announcements and their potential impact on risk-on assets including cryptocurrencies. Key DeFi protocol upgrades scheduled for deployment.
""",
        "generatedBy": "Test Script",
        "influencerStats": sample_influencer_stats,
        "descriptionSummary": "This comprehensive weekly analysis examines DeFi innovation trends, evolving regulatory frameworks, and institutional market movements in the digital asset space. The report synthesizes insights from 50 leading industry voices to provide strategic intelligence on cryptocurrency market dynamics, protocol developments, and emerging investment patterns shaping the ecosystem."
    }
    
    try:
        print(f"📤 Sending request to: {url}")
        response = requests.post(url, json=test_payload, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Weekly endpoint test SUCCESSFUL!")
            response_data = response.json()
            print(f"📋 Response: {json.dumps(response_data, indent=2)}")
        else:
            print("❌ Weekly endpoint test FAILED!")
            print(f"📋 Error Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    print("-" * 60)

def main():
    """Run both endpoint tests"""
    
    print("🚀 Starting TaoWAR API Endpoint Tests")
    print(f"🕐 Test Time: {datetime.now(ZoneInfo('Europe/Paris')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 60)
    
    # Test daily endpoint
    test_daily_endpoint()
    
    # Test weekly endpoint  
    test_weekly_endpoint()
    
    print("🏁 All tests completed!")

if __name__ == "__main__":
    main()
