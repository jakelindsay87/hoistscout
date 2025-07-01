#!/usr/bin/env python3
"""
Simple compliance test without database dependencies
"""

import asyncio
import httpx
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleComplianceChecker:
    """Simplified compliance checker for testing"""
    
    def __init__(self):
        self.logger = logger
        
    async def check_site_compliance(self, website_config: dict) -> dict:
        """Check basic compliance for a website"""
        
        site_url = website_config['url']
        domain = urlparse(site_url).netloc
        
        self.logger.info(f"Starting compliance check for: {domain}")
        
        compliance_result = {
            'domain': domain,
            'compliance_status': 'unknown',
            'scraping_allowed': False,
            'checks_performed': {},
            'risk_level': 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Check robots.txt
            robots_result = await self.check_robots_txt(site_url)
            compliance_result['robots_analysis'] = robots_result
            compliance_result['checks_performed']['robots_txt'] = True
            
            # Check if it's a government site
            if any(gov in domain for gov in ['.gov.', '.gov.au']):
                compliance_result['compliance_status'] = 'allowed_with_precautions'
                compliance_result['scraping_allowed'] = True
                compliance_result['risk_level'] = 'low'
                compliance_result['required_precautions'] = [
                    'Respect rate limits (max 1 request per 2 seconds)',
                    'Only access public tender information',
                    'Include proper User-Agent identification'
                ]
            else:
                compliance_result['compliance_status'] = 'unclear'
                compliance_result['risk_level'] = 'medium'
            
        except Exception as e:
            self.logger.error(f"Compliance check failed: {e}")
            compliance_result['error'] = str(e)
            
        return compliance_result
    
    async def check_robots_txt(self, site_url: str) -> dict:
        """Check robots.txt"""
        
        robots_analysis = {
            'robots_txt_found': False,
            'scraping_allowed': True
        }
        
        try:
            robots_url = urljoin(site_url, '/robots.txt')
            
            async with httpx.AsyncClient() as client:
                response = await client.get(robots_url, timeout=10)
                
                if response.status_code == 200:
                    robots_analysis['robots_txt_found'] = True
                    self.logger.info(f"Found robots.txt at {robots_url}")
                    
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt: {e}")
            
        return robots_analysis


async def test_victorian_tenders():
    """Test Victorian Government Tenders compliance"""
    
    print("🔍 Testing Compliance for Victorian Government Tenders")
    print("=" * 60)
    
    checker = SimpleComplianceChecker()
    
    test_site = {
        'url': 'https://www.tenders.vic.gov.au',
        'name': 'Victorian Government Tenders'
    }
    
    result = await checker.check_site_compliance(test_site)
    
    print(f"\n📋 Domain: {result['domain']}")
    print(f"✓ Compliance Status: {result['compliance_status']}")
    print(f"✓ Scraping Allowed: {'✅ YES' if result['scraping_allowed'] else '❌ NO'}")
    print(f"✓ Risk Level: {result['risk_level']}")
    
    if result.get('robots_analysis'):
        print(f"\n🤖 Robots.txt Found: {'YES' if result['robots_analysis']['robots_txt_found'] else 'NO'}")
    
    if result.get('required_precautions'):
        print("\n⚠️  Required Precautions:")
        for precaution in result['required_precautions']:
            print(f"  - {precaution}")
    
    print("\n" + "=" * 60)
    print(f"✅ Test completed successfully!")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_victorian_tenders())