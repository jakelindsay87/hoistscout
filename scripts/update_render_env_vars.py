#!/usr/bin/env python3
"""
Script to update Render environment variables for HoistScout services.
This script adds/updates the GEMINI_API_KEY for both hoistscout-api and hoistscout-worker services.
"""

import os
import sys
import requests
import json
from typing import Dict, List, Optional

# Render API configuration
RENDER_API_BASE = "https://api.render.com/v1"
GEMINI_API_KEY = "AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA"

def get_render_api_key() -> str:
    """Get Render API key from environment or prompt user."""
    api_key = os.environ.get('RENDER_API_KEY')
    if not api_key:
        print("RENDER_API_KEY not found in environment.")
        print("To get your Render API key:")
        print("1. Go to https://dashboard.render.com/u/settings")
        print("2. Scroll to 'API Keys' section")
        print("3. Create a new API key or copy an existing one")
        print()
        api_key = input("Enter your Render API key: ").strip()
    return api_key

def get_headers(api_key: str) -> Dict[str, str]:
    """Get headers for Render API requests."""
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def get_services(api_key: str) -> List[Dict]:
    """Get all services from Render."""
    headers = get_headers(api_key)
    response = requests.get(f"{RENDER_API_BASE}/services", headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching services: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    return response.json()

def get_service_env_vars(api_key: str, service_id: str) -> List[Dict]:
    """Get environment variables for a specific service."""
    headers = get_headers(api_key)
    response = requests.get(f"{RENDER_API_BASE}/services/{service_id}/env-vars", headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching env vars for service {service_id}: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def update_service_env_var(api_key: str, service_id: str, key: str, value: str) -> bool:
    """Update or add a single environment variable for a service."""
    headers = get_headers(api_key)
    
    # First, get existing env vars
    env_vars = get_service_env_vars(api_key, service_id)
    
    # Check if the key already exists
    existing_var = next((var for var in env_vars if var.get('key') == key), None)
    
    if existing_var:
        # Update existing variable
        url = f"{RENDER_API_BASE}/services/{service_id}/env-vars/{existing_var['id']}"
        data = {"value": value}
        response = requests.put(url, headers=headers, json=data)
    else:
        # Add new variable
        url = f"{RENDER_API_BASE}/services/{service_id}/env-vars"
        data = {"key": key, "value": value}
        response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✓ Successfully updated {key} for service {service_id}")
        return True
    else:
        print(f"✗ Error updating {key} for service {service_id}: {response.status_code}")
        print(response.text)
        return False

def trigger_deploy(api_key: str, service_id: str) -> bool:
    """Trigger a new deployment for a service."""
    headers = get_headers(api_key)
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys"
    
    response = requests.post(url, headers=headers, json={})
    
    if response.status_code in [200, 201]:
        print(f"✓ Deployment triggered for service {service_id}")
        return True
    else:
        print(f"✗ Error triggering deployment for service {service_id}: {response.status_code}")
        print(response.text)
        return False

def main():
    """Main function to update Render environment variables."""
    print("=== Render Environment Variables Updater ===")
    print()
    
    # Get API key
    api_key = get_render_api_key()
    
    # Get all services
    print("\nFetching Render services...")
    services = get_services(api_key)
    
    # Find hoistscout-api and hoistscout-worker services
    target_services = []
    for service in services:
        if service['service']['name'] in ['hoistscout-api', 'hoistscout-worker']:
            target_services.append({
                'id': service['service']['id'],
                'name': service['service']['name'],
                'status': service['service']['status']
            })
    
    if not target_services:
        print("Error: Could not find hoistscout-api or hoistscout-worker services")
        sys.exit(1)
    
    print(f"\nFound {len(target_services)} target services:")
    for service in target_services:
        print(f"  - {service['name']} (ID: {service['id']}, Status: {service['status']})")
    
    # Update environment variables for each service
    print("\nUpdating environment variables...")
    updated_services = []
    
    for service in target_services:
        print(f"\nProcessing {service['name']}...")
        
        # Update GEMINI_API_KEY
        if update_service_env_var(api_key, service['id'], 'GEMINI_API_KEY', GEMINI_API_KEY):
            # Also ensure USE_GEMINI is set to true
            update_service_env_var(api_key, service['id'], 'USE_GEMINI', 'true')
            updated_services.append(service)
    
    # Ask if user wants to trigger deployments
    if updated_services:
        print(f"\n✓ Successfully updated environment variables for {len(updated_services)} services")
        print("\nNote: Environment variable changes require a new deployment to take effect.")
        
        deploy = input("\nWould you like to trigger deployments now? (y/n): ").strip().lower()
        if deploy == 'y':
            print("\nTriggering deployments...")
            for service in updated_services:
                trigger_deploy(api_key, service['id'])
            print("\n✓ Deployments triggered. Monitor progress at https://dashboard.render.com")
        else:
            print("\nEnvironment variables updated but not deployed.")
            print("To deploy manually, visit https://dashboard.render.com and click 'Manual Deploy' for each service.")
    else:
        print("\n✗ No services were updated successfully.")
    
    # Display summary
    print("\n=== Summary ===")
    print(f"GEMINI_API_KEY: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
    print(f"USE_GEMINI: true")
    print(f"Services updated: {len(updated_services)}")
    if updated_services:
        for service in updated_services:
            print(f"  - {service['name']}")

if __name__ == "__main__":
    main()