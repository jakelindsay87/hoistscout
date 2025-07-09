import requests
import time
import sys

# Login
print('1. Logging in...')
r = requests.post('https://hoistscout-api.onrender.com/api/auth/login', 
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={'username': 'demo', 'password': 'demo123'})
if r.status_code \!= 200:
    print(f'Login failed: {r.status_code}')
    sys.exit(1)
token = r.json()['access_token']
print('✓ Login successful')

# Create job
print('\n2. Creating job...')
headers = {'Authorization': f'Bearer {token}'}
r = requests.post('https://hoistscout-api.onrender.com/api/scraping/jobs/',
    headers=headers,
    json={'website_id': 1, 'job_type': 'test', 'priority': 10})
if r.status_code not in [200, 201]:
    print(f'Job creation failed: {r.status_code} - {r.text}')
    sys.exit(1)
job = r.json()
print(f'✓ Job created: ID={job["id"]}, Status={job["status"]}')

# Monitor status
print('\n3. Monitoring job...')
job_id = job['id']
for i in range(12):  # Check for 60 seconds
    time.sleep(5)
    r = requests.get(f'https://hoistscout-api.onrender.com/api/scraping/jobs/{job_id}', headers=headers)
    if r.status_code == 200:
        job = r.json()
        print(f'  [{i*5}s] Status: {job["status"]}', end='')
        if job.get('started_at'):
            print(' - STARTED\!', end='')
        if job.get('error_message'):
            print(f' - ERROR: {job["error_message"]}', end='')
        print()
        
        if job['status'] in ['completed', 'failed', 'processing']:
            if job['status'] == 'completed':
                print('\n✅ SUCCESS\! Job completed\!')
            elif job['status'] == 'processing':
                print('\n🔄 Job is being processed\!')
            else:
                print(f'\n❌ Job failed: {job.get("error_message", "Unknown error")}')
            sys.exit(0)

print('\n❌ Job still pending after 60 seconds - worker not processing')
