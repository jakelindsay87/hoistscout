#!/usr/bin/env python3
"""
End-to-end test for HoistScout scraping functionality.
Tests: Login → Add Website → Trigger Scrape → Monitor Job → View Opportunities
"""
import requests
import time
import json
from datetime import datetime

# Configuration
import os
API_BASE = os.environ.get("API_BASE", "https://hoistscout-api.onrender.com")
DEMO_USERNAME = os.environ.get("DEMO_USERNAME", "demo")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "demo123")

class HoistScoutTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        
    def login(self):
        """Login with demo credentials."""
        print("🔐 Logging in with demo account...")
        
        # OAuth2 compatible login
        login_data = {
            "username": DEMO_USERNAME,
            "password": DEMO_PASSWORD,
            "grant_type": "password"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/api/auth/login",
                data=login_data,  # Form data, not JSON
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                print(f"✅ Login successful!")
                print(f"   Token: {self.access_token[:20]}..." if self.access_token else "   Warning: No token received")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_websites(self):
        """Get list of websites."""
        print("\n📋 Fetching websites...")
        print(f"   Headers: {dict(self.session.headers)}")
        try:
            response = self.session.get(f"{API_BASE}/api/websites", timeout=10)
            if response.status_code == 200:
                websites = response.json()
                print(f"✅ Found {len(websites)} websites")
                for site in websites[:5]:  # Show first 5
                    print(f"   - {site['name'] or site['url']} (ID: {site['id']})")
                return websites
            else:
                print(f"❌ Failed to get websites: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error fetching websites: {e}")
            return []
    
    def add_website(self, name, url):
        """Add a new website."""
        print(f"\n➕ Adding website: {name}")
        website_data = {
            "name": name,
            "url": url,
            "is_active": True,
            "category": "grants"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/api/websites",
                json=website_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                website = response.json()
                print(f"✅ Created website: {website['name']} (ID: {website['id']})")
                return website
            else:
                print(f"❌ Failed to create website: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating website: {e}")
            return None
    
    def trigger_scrape(self, website_id):
        """Trigger a scraping job for a website."""
        print(f"\n🔄 Triggering scrape for website ID {website_id}...")
        
        job_data = {
            "website_id": website_id,
            "job_type": "full",
            "priority": 5
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/api/scraping/jobs",
                json=job_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                job = response.json()
                print(f"✅ Created scrape job ID: {job['id']} with status: {job['status']}")
                return job
            else:
                print(f"❌ Failed to create job: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating job: {e}")
            return None
    
    def check_job_status(self, job_id):
        """Check the status of a scraping job."""
        try:
            response = self.session.get(
                f"{API_BASE}/api/scraping/jobs/{job_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get job status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error checking job: {e}")
            return None
    
    def monitor_job(self, job_id, max_wait=120):
        """Monitor a job until completion."""
        print(f"\n⏳ Monitoring job {job_id}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = self.check_job_status(job_id)
            if not job:
                break
                
            status = job.get('status', 'unknown')
            print(f"   Job status: {status}", end="\r")
            
            if status in ['completed', 'failed', 'cancelled']:
                print(f"\n   Final status: {status}")
                if status == 'completed':
                    print("✅ Job completed successfully!")
                elif status == 'failed':
                    error = job.get('error_message', 'Unknown error')
                    print(f"❌ Job failed: {error}")
                return job
                
            time.sleep(3)
        
        print(f"\n⏱️  Job did not complete within {max_wait} seconds")
        return None
    
    def get_opportunities(self, website_id=None):
        """Get opportunities, optionally filtered by website."""
        print(f"\n🎯 Fetching opportunities...")
        
        url = f"{API_BASE}/api/opportunities"
        if website_id:
            url += f"?website_id={website_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                opportunities = response.json()
                print(f"✅ Found {len(opportunities)} opportunities")
                
                # Show first few opportunities
                for opp in opportunities[:3]:
                    print(f"\n   📌 {opp.get('title', 'Untitled')}")
                    print(f"      Deadline: {opp.get('deadline', 'No deadline')}")
                    print(f"      Value: {opp.get('currency', '$')}{opp.get('value', 'N/A')}")
                    print(f"      URL: {opp.get('source_url', 'No URL')}")
                
                return opportunities
            else:
                print(f"❌ Failed to get opportunities: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching opportunities: {e}")
            return []
    
    def run_full_test(self):
        """Run the complete end-to-end test."""
        print("=" * 60)
        print("🚀 HoistScout End-to-End Scraping Test")
        print(f"📅 {datetime.now()}")
        print(f"🌐 API: {API_BASE}")
        print("=" * 60)
        
        # Step 1: Login
        if not self.login():
            print("\n❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Get existing websites
        websites = self.get_websites()
        
        # Step 3: Add a test website or use existing
        test_website = None
        if not websites:
            test_website = self.add_website(
                "Test Grants Portal",
                "https://www.grants.gov"
            )
            if not test_website:
                print("\n❌ Cannot proceed without a website")
                return False
        else:
            # Use the first active website
            test_website = websites[0]
            print(f"\n📍 Using existing website: {test_website['name']} (ID: {test_website['id']})")
        
        # Step 4: Trigger scraping
        job = self.trigger_scrape(test_website['id'])
        if not job:
            print("\n❌ Cannot proceed without a scraping job")
            return False
        
        # Step 5: Monitor the job
        final_job = self.monitor_job(job['id'])
        
        # Step 6: Check for opportunities
        if final_job and final_job.get('status') == 'completed':
            time.sleep(2)  # Give DB time to commit
            opportunities = self.get_opportunities(test_website['id'])
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        if final_job and final_job.get('status') == 'completed':
            print("✅ SUCCESS: Complete scraping pipeline is working!")
            print(f"   - Website: {test_website['name']}")
            print(f"   - Job ID: {final_job['id']}")
            print(f"   - Status: {final_job['status']}")
            print(f"   - Opportunities found: {len(opportunities) if 'opportunities' in locals() else 0}")
            return True
        else:
            print("❌ FAILED: Scraping pipeline has issues")
            if final_job:
                print(f"   - Final job status: {final_job.get('status', 'unknown')}")
                print(f"   - Error: {final_job.get('error_message', 'None')}")
            else:
                print("   - Job did not complete in time or could not be monitored")
            return False


if __name__ == "__main__":
    tester = HoistScoutTester()
    success = tester.run_full_test()
    exit(0 if success else 1)