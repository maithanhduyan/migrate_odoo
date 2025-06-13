#!/usr/bin/env python3
"""
Test script để kiểm tra và tạo database demo qua HTTP endpoint
"""

import requests
import json
import time
from typing import Dict, Any

def test_database_manager_endpoint(base_url: str, database_name: str) -> Dict[str, Any]:
    """Test tạo database qua web interface"""
    
    result = {
        'success': False,
        'message': '',
        'details': {}
    }
    
    try:
        # 1. Kiểm tra endpoint database manager
        manager_url = f"{base_url}/web/database/manager"
        print(f"🔍 Checking database manager at: {manager_url}")
        
        response = requests.get(manager_url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            print("✅ Database manager accessible")
        else:
            print(f"❌ Database manager not accessible: {response.status_code}")
            result['message'] = f"Database manager not accessible: {response.status_code}"
            return result
            
        # 2. Thử lấy danh sách databases hiện tại
        print(f"\n🔍 Getting current databases list...")
        list_url = f"{base_url}/web/database/list"
        
        try:
            list_response = requests.post(list_url, timeout=10)
            print(f"List databases status: {list_response.status_code}")
            
            if list_response.status_code == 200:
                try:
                    databases = list_response.json()
                    print(f"Current databases: {databases}")
                    result['details']['current_databases'] = databases
                    
                    # Kiểm tra xem database đã tồn tại chưa
                    if database_name in databases:
                        print(f"✅ Database {database_name} already exists")
                        result['success'] = True
                        result['message'] = f"Database {database_name} already exists"
                        return result
                        
                except json.JSONDecodeError:
                    print("Response is not JSON, might be HTML form")
                    
        except Exception as e:
            print(f"Warning: Could not get databases list: {e}")
            
        # 3. Thử tạo database mới
        print(f"\n🏗️ Attempting to create database: {database_name}")
        
        # Thử với endpoint /web/database/create
        create_url = f"{base_url}/web/database/create"
        
        create_data = {
            'master_pwd': 'admin',  # Master password
            'name': database_name,
            'lang': 'en_US', 
            'country_code': 'US',
            'demo': 'True',  # Enable demo data
            'login': 'admin',
            'password': 'admin',
            'phone': '',
            'confirm_password': 'admin'
        }
        
        print(f"Sending POST to: {create_url}")
        print(f"Data: {create_data}")
        
        create_response = requests.post(
            create_url, 
            data=create_data,
            timeout=300,  # 5 minutes timeout for database creation
            allow_redirects=False
        )
        
        print(f"Create response status: {create_response.status_code}")
        print(f"Create response headers: {dict(create_response.headers)}")
        
        if create_response.status_code in [200, 302]:
            # Check if there's any error in response
            response_text = create_response.text
            
            if 'error' in response_text.lower() or 'exception' in response_text.lower():
                print(f"❌ Database creation failed with error in response")
                print(f"Response preview: {response_text[:500]}...")
                result['message'] = f"Database creation failed: error in response"
                result['details']['response_preview'] = response_text[:500]
            else:
                print(f"✅ Database creation appears successful")
                result['success'] = True
                result['message'] = f"Database {database_name} created successfully"
                
                # Wait a bit and verify
                time.sleep(5)
                
                # Try to verify by listing databases again
                try:
                    verify_response = requests.post(list_url, timeout=10)
                    if verify_response.status_code == 200:
                        try:
                            updated_databases = verify_response.json()
                            if database_name in updated_databases:
                                print(f"✅ Database {database_name} confirmed in database list")
                                result['details']['verified'] = True
                            else:
                                print(f"⚠️ Database {database_name} not found in updated list")
                                result['details']['verified'] = False
                        except json.JSONDecodeError:
                            print("Could not parse database list for verification")
                            
                except Exception as e:
                    print(f"Could not verify database creation: {e}")
                    
        else:
            print(f"❌ Database creation failed: HTTP {create_response.status_code}")
            print(f"Response: {create_response.text[:500]}...")
            result['message'] = f"Database creation failed: HTTP {create_response.status_code}"
            result['details']['response_preview'] = create_response.text[:500]
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - database creation might take longer")
        result['message'] = "Request timeout during database creation"
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check if Odoo is running")
        result['message'] = "Connection error - Odoo might not be running"
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        result['message'] = f"Unexpected error: {e}"
        
    return result

def main():
    """Main test function"""
    
    print("🚀 Testing Database Creation via HTTP Endpoints")
    print("=" * 50)
    
    # Test both v15 and v16
    test_configs = [
        {
            'name': 'Odoo v15',
            'url': 'http://localhost:8069',
            'database': 'demo_v15_test'
        },
        {
            'name': 'Odoo v16', 
            'url': 'http://localhost:8016',
            'database': 'demo_v16_test'
        }
    ]
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"Testing {config['name']}")
        print(f"URL: {config['url']}")
        print(f"Database: {config['database']}")
        print('='*60)
        
        result = test_database_manager_endpoint(config['url'], config['database'])
        
        print(f"\n📊 Result for {config['name']}:")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['details']:
            print("Details:")
            for key, value in result['details'].items():
                print(f"  {key}: {value}")
        
        print("\n" + "-"*40)

if __name__ == "__main__":
    main()
