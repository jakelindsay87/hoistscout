#!/usr/bin/env python3
"""Quick check of worker status"""
import requests
import time
import json
from datetime import datetime

API_URL = 'https://hoistscout-api.onrender.com'

print('Checking HoistScout Worker Status...')
print('=' * 60)

# Login
login_response = requests.post(
    f'{API_URL}/api/auth/login',
    data={'username': 'demo', 'password': 'demo123'}
)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Check existing jobs
    jobs_response = requests.get(f'{API_URL}/api/scraping/jobs?limit=10', headers=headers)
    if jobs_response.status_code == 200:
        jobs = jobs_response.json()
        print(f'\nFound {len(jobs)} jobs:')
        
        any_processed = False
        for job in jobs[:10]:
            status_emoji = {
                'pending': '⏳',
                'running': '🏃',
                'completed': '✅',
                'failed': '❌'
            }.get(job['status'], '❓')
            
            print(f'  Job {job["id"]}: {status_emoji} {job["status"]}')
            
            if job['status'] in ['running', 'completed']:
                any_processed = True
                print(f'\n🎉 WORKER IS PROCESSING JOBS!')
                print(f'  Job {job["id"]} is {job["status"]}!')
                if job['status'] == 'completed':
                    if job.get('stats'):
                        print(f'  Stats: {json.dumps(job["stats"], indent=4)}')
                    
                    # Check for opportunities
                    opps_response = requests.get(
                        f'{API_URL}/api/opportunities?website_id={job["website_id"]}&limit=3',
                        headers=headers
                    )
                    if opps_response.status_code == 200:
                        opps = opps_response.json()
                        if opps:
                            print(f'\n  ✅ Found {len(opps)} opportunities!')
                            for opp in opps[:2]:
                                print(f'    - {opp["title"][:60]}...')
                                print(f'      ${opp.get("value", 0):,.2f} {opp.get("currency", "AUD")}')
        
        if not any_processed:
            print('\n⚠️ No jobs have been processed yet')
            print('\nCreating a new test job...')
            
            # Get first website
            websites = requests.get(f'{API_URL}/api/websites?limit=1', headers=headers).json()
            if websites:
                job_data = {
                    'website_id': websites[0]['id'],
                    'job_type': 'test',
                    'priority': 10
                }
                
                job_response = requests.post(
                    f'{API_URL}/api/scraping/jobs',
                    json=job_data,
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                
                if job_response.status_code == 200:
                    new_job = job_response.json()
                    print(f'✅ Created job {new_job["id"]}')
                    print('\nMonitoring for 90 seconds...')
                    
                    # Monitor
                    for i in range(9):
                        time.sleep(10)
                        job = requests.get(f'{API_URL}/api/scraping/jobs/{new_job["id"]}', headers=headers).json()
                        print(f'  [{datetime.now().strftime("%H:%M:%S")}] Job {job["id"]}: {job["status"]}')
                        
                        if job['status'] != 'pending':
                            print(f'\n🎉 JOB {job["id"]} IS NOW {job["status"].upper()}!')
                            break

print('\n' + '=' * 60)
print('Worker Dashboard: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g/logs')
print('Check the logs to see:')
print('  - Environment validation results')
print('  - Redis connection status')
print('  - Database connection status')
print('  - Registered tasks list')
print('  - Any error messages')