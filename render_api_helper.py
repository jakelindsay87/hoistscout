#!/usr/bin/env python3
"""
Helper script to interact with Render API
"""
import os
import requests
import json
from typing import Dict, List, Optional

class RenderAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def list_services(self) -> List[Dict]:
        """List all services"""
        response = requests.get(
            f"{self.base_url}/services",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_service(self, service_id: str) -> Dict:
        """Get service details"""
        response = requests.get(
            f"{self.base_url}/services/{service_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_env_vars(self, service_id: str) -> List[Dict]:
        """Get environment variables for a service"""
        response = requests.get(
            f"{self.base_url}/services/{service_id}/env-vars",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update_env_var(self, service_id: str, key: str, value: str) -> Dict:
        """Update or create an environment variable"""
        response = requests.put(
            f"{self.base_url}/services/{service_id}/env-vars/{key}",
            headers=self.headers,
            json={"value": value}
        )
        response.raise_for_status()
        return response.json()
    
    def deploy_service(self, service_id: str) -> Dict:
        """Trigger a new deployment"""
        response = requests.post(
            f"{self.base_url}/services/{service_id}/deploys",
            headers=self.headers,
            json={"clearCache": True}
        )
        response.raise_for_status()
        return response.json()
    
    def create_service(self, service_config: Dict) -> Dict:
        """Create a new service"""
        response = requests.post(
            f"{self.base_url}/services",
            headers=self.headers,
            json=service_config
        )
        response.raise_for_status()
        return response.json()


def main():
    # Get API key from environment or prompt
    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        print("Please set RENDER_API_KEY environment variable")
        print("You can find it at: https://dashboard.render.com/account/settings")
        return
    
    api = RenderAPI(api_key)
    
    print("🔍 Fetching Render services...")
    print("-" * 50)
    
    try:
        services = api.list_services()
        
        # Find HoistScout services
        hoistscout_services = {}
        for service in services:
            if "hoistscout" in service.get("name", "").lower():
                name = service["name"]
                hoistscout_services[name] = service
                print(f"✅ Found: {name}")
                print(f"   ID: {service['id']}")
                print(f"   Type: {service['type']}")
                print(f"   Status: {service.get('suspended', False) and 'Suspended' or 'Active'}")
        
        if not hoistscout_services:
            print("❌ No HoistScout services found")
            return
        
        # Check for worker service
        worker_service = None
        for name, service in hoistscout_services.items():
            if "worker" in name.lower():
                worker_service = service
                print(f"\n📦 Worker Service: {name}")
                
                # Get current env vars
                env_vars = api.get_env_vars(service['id'])
                ollama_configured = False
                
                for env in env_vars:
                    if env['key'] == 'OLLAMA_BASE_URL':
                        print(f"   Current OLLAMA_BASE_URL: {env['value']}")
                        ollama_configured = True
                
                if not ollama_configured:
                    print("   ⚠️  OLLAMA_BASE_URL not configured")
        
        # Check if Ollama service exists
        ollama_service = None
        for name, service in hoistscout_services.items():
            if "ollama" in name.lower():
                ollama_service = service
                print(f"\n🤖 Ollama Service: {name}")
                print(f"   URL: {service.get('serviceDetails', {}).get('url', 'N/A')}")
        
        if not ollama_service:
            print("\n⚠️  No Ollama service found on Render")
            print("\nTo deploy Ollama on Render:")
            print("1. Create a new Web Service")
            print("2. Use Docker image: ollama/ollama:latest")
            print("3. Set PORT environment variable to 11434")
            print("4. Add startup command: ollama serve")
        
        return hoistscout_services
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    main()