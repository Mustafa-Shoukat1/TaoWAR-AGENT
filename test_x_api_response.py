#!/usr/bin/env python3
"""
Test script to understand X API response structure and fix the Response object errors
Run this script and provide the actual X API response to understand the structure
"""

import json
from typing import Any, Dict, Union

def analyze_x_api_response(response_object: Any) -> Dict[str, Any]:
    """
    Analyze the structure of an X API response object
    
    Args:
        response_object: The actual response object returned by tweepy
        
    Returns:
        dict: Analysis of the response structure
    """
    analysis = {
        "object_type": type(response_object).__name__,
        "has_get_method": hasattr(response_object, 'get'),
        "has_data_attr": hasattr(response_object, 'data'),
        "has_id_attr": hasattr(response_object, 'id'),
        "attributes": [],
        "methods": [],
        "data_structure": None,
        "recommended_access_pattern": None
    }
    
    # Get all attributes and methods
    for attr in dir(response_object):
        if not attr.startswith('_'):
            if callable(getattr(response_object, attr)):
                analysis["methods"].append(attr)
            else:
                analysis["attributes"].append(attr)
    
    # Analyze data structure if it exists
    if hasattr(response_object, 'data'):
        data = response_object.data
        analysis["data_structure"] = {
            "data_type": type(data).__name__,
            "data_attributes": [attr for attr in dir(data) if not attr.startswith('_') and not callable(getattr(data, attr))],
            "has_id": hasattr(data, 'id') if data else False
        }
    
    # Check if it's a dict-like object
    if hasattr(response_object, 'keys'):
        analysis["is_dict_like"] = True
        try:
            analysis["keys"] = list(response_object.keys())
        except:
            analysis["keys"] = "Unable to get keys"
    
    # Determine recommended access pattern
    if hasattr(response_object, 'data') and hasattr(response_object.data, 'id'):
        analysis["recommended_access_pattern"] = "response.data.id"
    elif hasattr(response_object, 'id'):
        analysis["recommended_access_pattern"] = "response.id"
    elif hasattr(response_object, 'get') and isinstance(response_object, dict):
        analysis["recommended_access_pattern"] = "response.get('id')"
    elif hasattr(response_object, 'keys'):
        analysis["recommended_access_pattern"] = "response['id'] (if 'id' in keys)"
    else:
        analysis["recommended_access_pattern"] = "Unknown - needs investigation"
    
    return analysis

def safe_extract_tweet_id(response_object: Any) -> Union[str, None]:
    """
    Safely extract tweet ID from X API response using multiple fallback methods
    
    Args:
        response_object: The response object from X API
        
    Returns:
        str or None: The tweet ID if found, None otherwise
    """
    if not response_object:
        return None
    
    # Method 1: Try response.data.id (most common for tweepy v2)
    try:
        if hasattr(response_object, 'data') and hasattr(response_object.data, 'id'):
            return str(response_object.data.id)
    except:
        pass
    
    # Method 2: Try direct response.id
    try:
        if hasattr(response_object, 'id'):
            return str(response_object.id)
    except:
        pass
    
    # Method 3: Try dict-like access with get() method
    try:
        if hasattr(response_object, 'get'):
            return str(response_object.get('id'))
    except:
        pass
    
    # Method 4: Try direct dict access
    try:
        if isinstance(response_object, dict) and 'id' in response_object:
            return str(response_object['id'])
    except:
        pass
    
    # Method 5: Check for data dict within response
    try:
        if hasattr(response_object, 'data') and isinstance(response_object.data, dict):
            return str(response_object.data.get('id'))
    except:
        pass
    
    # Method 6: Try accessing as nested dict
    try:
        if isinstance(response_object, dict) and 'data' in response_object:
            data = response_object['data']
            if isinstance(data, dict) and 'id' in data:
                return str(data['id'])
    except:
        pass
    
    print(f"⚠️ Could not extract ID from response: {type(response_object)}")
    return None

def test_with_mock_responses():
    """Test the safe extraction with various mock response types"""
    
    print("🧪 Testing with various mock response types...\n")
    
    # Mock Response Type 1: Tweepy Response object
    class MockTweepyResponse:
        def __init__(self):
            self.data = MockData()
        
    class MockData:
        def __init__(self):
            self.id = "1234567890123456789"
    
    # Mock Response Type 2: Dict with get method
    class MockDictResponse(dict):
        def __init__(self):
            super().__init__()
            self['id'] = "9876543210987654321"
    
    # Mock Response Type 3: Simple dict
    mock_dict_response = {
        'data': {
            'id': '5555555555555555555',
            'text': 'Test tweet'
        }
    }
    
    # Mock Response Type 4: Direct object with id
    class MockDirectResponse:
        def __init__(self):
            self.id = "7777777777777777777"
    
    test_cases = [
        ("Tweepy Response with data.id", MockTweepyResponse()),
        ("Dict-like with get() method", MockDictResponse()),
        ("Nested dict response", mock_dict_response),
        ("Direct object with id", MockDirectResponse()),
        ("None response", None),
        ("Empty dict", {}),
    ]
    
    for description, mock_response in test_cases:
        print(f"Testing: {description}")
        analysis = analyze_x_api_response(mock_response) if mock_response is not None else {"object_type": "NoneType"}
        tweet_id = safe_extract_tweet_id(mock_response)
        
        print(f"  Object type: {analysis['object_type']}")
        print(f"  Extracted ID: {tweet_id}")
        print(f"  Recommended pattern: {analysis.get('recommended_access_pattern', 'N/A')}")
        print()

def generate_fixed_code():
    """Generate the fixed code for handling X API responses"""
    
    fixed_code = '''
def post_reply_with_safe_response_handling(tweet_id, reply_text):
    """
    Enhanced post_reply function with safe response handling
    """
    try:
        # Your existing post_reply code here...
        response = client.create_tweet(
            in_reply_to_tweet_id=tweet_id,
            text=reply_text
        )
        
        if response:
            # ✅ SAFE: Extract tweet ID using multiple fallback methods
            reply_id = safe_extract_tweet_id(response)
            
            if reply_id:
                logger.info(f"✅ Successfully posted reply with ID: {reply_id}")
                return {"id": reply_id, "response": response}
            else:
                logger.warning("⚠️ Posted successfully but could not extract tweet ID")
                return {"id": None, "response": response}
        else:
            logger.error("❌ Failed to post reply")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error posting reply: {e}")
        return None

# Usage in your posting code:
def enhanced_posting_with_safe_handling():
    try:
        reply = post_reply_with_safe_response_handling(main_tweet_id, item["summary"])
        
        if reply and reply.get("id"):
            # ✅ SAFE: Use the safely extracted ID
            mark_x_post_sent(category_name, summary_hash, reply["id"], 'daily_summary')
            logger.info(f"✅ Posted and tracked reply with ID: {reply['id']}")
        else:
            logger.error("⚠️ Failed to post reply or extract ID")
            
    except Exception as e:
        logger.error(f"Got an error in posting the tweet, Error: {e}")
'''
    
    return fixed_code

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 X API Response Structure Analysis Tool")
    print("=" * 60)
    print()
    
    print("This script helps fix the 'Response object has no attribute get' error.")
    print()
    
    # Run tests with mock data
    test_with_mock_responses()
    
    print("=" * 60)
    print("💡 HOW TO USE THIS SCRIPT:")
    print("=" * 60)
    print()
    print("1. Import this script in your X posting code:")
    print("   from test_x_api_response import safe_extract_tweet_id")
    print()
    print("2. Replace the problematic line:")
    print("   OLD: reply.get('id')")
    print("   NEW: safe_extract_tweet_id(reply)")
    print()
    print("3. To analyze your actual response object:")
    print("   analysis = analyze_x_api_response(your_actual_response)")
    print("   print(json.dumps(analysis, indent=2))")
    print()
    
    # Show the fixed code
    print("=" * 60)
    print("🛠️ FIXED CODE EXAMPLE:")
    print("=" * 60)
    print(generate_fixed_code())
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete! Use safe_extract_tweet_id() in your code.")
    print("=" * 60)
