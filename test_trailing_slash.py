#!/usr/bin/env python3
import requests

# Login
resp = requests.post('https://hoistscout-api.onrender.com/api/auth/login', 
    data={'username': 'demo', 'password': 'demo123', 'grant_type': 'password'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
token = resp.json()['access_token']

# Test with trailing slash
headers = {'Authorization': f'Bearer {token}'}
resp = requests.get('https://hoistscout-api.onrender.com/api/websites/', headers=headers)
print(f'With trailing slash: {resp.status_code}')
if resp.status_code == 200:
    print('Success! Authentication works with trailing slash')
    print(f'Got {len(resp.json())} websites')
else:
    print(f'Failed: {resp.text[:100]}')