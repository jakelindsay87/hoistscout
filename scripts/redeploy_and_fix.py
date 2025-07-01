#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

HOISTSCOUT_SERVICES = {
    "hoistscout-api": "srv-d1hltovfte5s73ad16tg",
    "hoistscout-frontend": "srv-d1hlum6r433s73avdn6g", 
    "hoistscout-worker": "srv-d1hlvanfte5s73ad476g"
}

def trigger_deployment(service_id, service_name):
    """Trigger a new deployment with clear cache"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys"
    
    print(f"\n🚀 Triggering deployment for {service_name}...")
    
    # Clear cache to ensure fresh build
    deploy_data = {
        "clearCache": "clear"
    }
    
    response = requests.post(url, headers=headers, json=deploy_data)
    
    if response.status_code in [200, 201]:
        deploy = response.json()
        deploy_id = deploy.get('id', 'Unknown')
        print(f"✅ Deployment triggered successfully")
        print(f"   Deploy ID: {deploy_id}")
        return deploy_id
    else:
        print(f"❌ Failed to trigger deployment: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def get_deploy_status(service_id, deploy_id):
    """Get current deployment status"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        deploy = response.json()
        return {
            'status': deploy.get('status', 'unknown'),
            'createdAt': deploy.get('createdAt', 'N/A'),
            'finishedAt': deploy.get('finishedAt', 'N/A')
        }
    return None

def get_deploy_logs(service_id, deploy_id):
    """Get deployment logs to identify issues"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}/logs"
    
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code == 200:
        logs = []
        errors = []
        
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                logs.append(decoded)
                
                # Capture errors
                lower_line = decoded.lower()
                if any(keyword in lower_line for keyword in ['error', 'failed', 'fatal', 'cannot', 'unable']):
                    errors.append(decoded)
        
        return logs, errors
    return [], []

def analyze_deployment_errors(errors):
    """Analyze errors and suggest fixes"""
    fixes = []
    
    for error in errors:
        error_lower = error.lower()
        
        # Repository issues
        if 'repository not found' in error_lower or 'could not read from remote' in error_lower:
            fixes.append({
                'issue': 'Repository not accessible',
                'fix': 'Update repository URL in Render dashboard to correct GitHub repo',
                'severity': 'critical'
            })
        
        # Docker build issues
        elif 'dockerfile' in error_lower and 'not found' in error_lower:
            fixes.append({
                'issue': 'Dockerfile not found',
                'fix': 'Ensure Dockerfile exists at specified path in render.yaml',
                'severity': 'critical'
            })
        
        # Python module issues
        elif 'modulenotfounderror' in error_lower or 'importerror' in error_lower:
            fixes.append({
                'issue': 'Python module import error',
                'fix': 'Check requirements.txt and ensure all dependencies are listed',
                'severity': 'high'
            })
        
        # Environment variable issues
        elif 'environment' in error_lower or 'env var' in error_lower:
            fixes.append({
                'issue': 'Missing environment variables',
                'fix': 'Configure required environment variables in Render dashboard',
                'severity': 'high'
            })
        
        # Build command issues
        elif 'command failed' in error_lower or 'exit code' in error_lower:
            fixes.append({
                'issue': 'Build command failed',
                'fix': 'Check build commands in Dockerfile and ensure they work locally',
                'severity': 'high'
            })
    
    return fixes

def check_service_configuration(service_id, service_name):
    """Check service configuration for common issues"""
    url = f"{RENDER_API_BASE}/services/{service_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        service = response.json()
        issues = []
        
        # Check repository
        repo = service.get('repo', '')
        if 'hoistscraper' in repo:
            issues.append({
                'issue': f'{service_name} still using old repository',
                'fix': 'Update to https://github.com/jakelindsay87/hoistscout',
                'severity': 'critical'
            })
        
        # Check environment variables
        if 'serviceDetails' in service:
            env_vars = service['serviceDetails'].get('envVars', [])
            if not env_vars:
                issues.append({
                    'issue': f'{service_name} has no environment variables configured',
                    'fix': 'Add required environment variables as per render.yaml',
                    'severity': 'high'
                })
        
        return issues
    return []

def main():
    print(f"Render Deployment Fix Script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # First check service configurations
    print("\n📋 Checking Service Configurations...")
    print("-" * 60)
    
    all_issues = []
    
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        issues = check_service_configuration(service_id, service_name)
        if issues:
            all_issues.extend(issues)
            for issue in issues:
                print(f"\n⚠️  {service_name}: {issue['issue']}")
                print(f"   Fix: {issue['fix']}")
    
    if any(issue['severity'] == 'critical' for issue in all_issues):
        print("\n\n🚨 CRITICAL ISSUES FOUND!")
        print("=" * 80)
        print("\nCannot proceed with deployment due to critical configuration issues.")
        print("\nRequired Manual Actions:")
        
        for issue in all_issues:
            if issue['severity'] == 'critical':
                print(f"\n❌ {issue['issue']}")
                print(f"   👉 {issue['fix']}")
        
        print("\n\nDirect links to fix issues:")
        for service_name, service_id in HOISTSCOUT_SERVICES.items():
            print(f"- {service_name}: https://dashboard.render.com/web/{service_id}/settings")
        
        return
    
    # Trigger deployments
    print("\n\n🚀 Triggering Deployments...")
    print("=" * 80)
    
    deployments = {}
    
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        deploy_id = trigger_deployment(service_id, service_name)
        if deploy_id:
            deployments[service_name] = {
                'service_id': service_id,
                'deploy_id': deploy_id,
                'status': 'triggered'
            }
        time.sleep(2)  # Rate limiting
    
    # Monitor deployments
    print("\n\n📊 Monitoring Deployments...")
    print("=" * 80)
    
    max_checks = 30
    check_count = 0
    
    while check_count < max_checks:
        check_count += 1
        print(f"\n🔍 Check #{check_count} at {datetime.now().strftime('%H:%M:%S')}")
        
        all_complete = True
        
        for service_name, deploy_info in deployments.items():
            if deploy_info['status'] in ['live', 'build_failed', 'update_failed', 'canceled']:
                continue
            
            status = get_deploy_status(deploy_info['service_id'], deploy_info['deploy_id'])
            if status:
                deploy_info['status'] = status['status']
                
                status_symbol = {
                    'live': '✅',
                    'build_in_progress': '🔨',
                    'update_in_progress': '🔄',
                    'build_failed': '❌',
                    'update_failed': '❌',
                    'canceled': '🚫'
                }.get(status['status'], '❓')
                
                print(f"  {service_name}: {status_symbol} {status['status']}")
                
                if status['status'] not in ['live', 'build_failed', 'update_failed', 'canceled']:
                    all_complete = False
        
        if all_complete:
            break
        
        if check_count < max_checks:
            time.sleep(10)
    
    # Analyze results and errors
    print("\n\n📋 Deployment Results & Analysis")
    print("=" * 80)
    
    for service_name, deploy_info in deployments.items():
        print(f"\n{service_name}:")
        print("-" * 40)
        
        if deploy_info['status'] == 'live':
            print("✅ Deployed successfully!")
        else:
            print(f"❌ Deployment failed: {deploy_info['status']}")
            
            # Get and analyze logs
            logs, errors = get_deploy_logs(deploy_info['service_id'], deploy_info['deploy_id'])
            
            if errors:
                print("\n🔍 Errors found:")
                for error in errors[-10:]:  # Last 10 errors
                    print(f"   {error}")
                
                # Analyze and suggest fixes
                fixes = analyze_deployment_errors(errors)
                if fixes:
                    print("\n💡 Suggested fixes:")
                    for fix in fixes:
                        print(f"   - {fix['fix']}")
    
    # Final recommendations
    print("\n\n📌 Next Steps:")
    print("=" * 80)
    print("\n1. If repository errors: Update GitHub repository in Render dashboard")
    print("2. If build errors: Check Dockerfile paths match render.yaml")
    print("3. If module errors: Ensure requirements.txt is complete")
    print("4. If env var errors: Configure environment variables in Render")
    print("\nUse the monitoring script to check status after fixes:")
    print("  python3 scripts/monitor_deployments.py")

if __name__ == "__main__":
    main()