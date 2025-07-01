#!/usr/bin/env python3
"""
Quick compliance check for Victorian Government Tenders
This tests only the compliance checking system without performing any scraping
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.compliance_checker import TermsComplianceChecker
from app.core.logging import ProductionLogger

logger = ProductionLogger().get_logger("compliance_test")


async def test_compliance_checker():
    """Test the compliance checking system on Victorian Government Tenders."""
    
    print("🔍 Testing Compliance Checker for Victorian Government Tenders")
    print("=" * 60)
    
    checker = TermsComplianceChecker()
    
    # Test configuration
    test_site = {
        'url': 'https://www.tenders.vic.gov.au',
        'name': 'Victorian Government Tenders'
    }
    
    print(f"\nChecking: {test_site['name']}")
    print(f"URL: {test_site['url']}")
    print("-" * 60)
    
    # Run compliance check
    result = await checker.check_site_compliance(test_site)
    
    # Display results
    print("\n📋 COMPLIANCE CHECK RESULTS:")
    print(f"  ✓ Domain: {result['domain']}")
    print(f"  ✓ Compliance Status: {result['compliance_status']}")
    print(f"  ✓ Scraping Allowed: {'✅ YES' if result['scraping_allowed'] else '❌ NO'}")
    print(f"  ✓ Risk Level: {result['risk_level']}")
    
    print("\n📊 CHECKS PERFORMED:")
    for check, performed in result['checks_performed'].items():
        status = "✅" if performed else "❌"
        print(f"  {status} {check.replace('_', ' ').title()}")
    
    # Robots.txt analysis
    if 'robots_analysis' in result:
        print("\n🤖 ROBOTS.TXT ANALYSIS:")
        robots = result['robots_analysis']
        print(f"  ✓ Found: {'YES' if robots.get('robots_txt_found') else 'NO'}")
        if robots.get('crawl_delay'):
            print(f"  ✓ Crawl Delay: {robots['crawl_delay']} seconds")
        if robots.get('disallowed_paths'):
            print(f"  ✓ Disallowed Paths: {', '.join(robots['disallowed_paths'])}")
    
    # Terms analysis
    if 'terms_analysis' in result:
        print("\n📜 TERMS & CONDITIONS ANALYSIS:")
        terms = result['terms_analysis']
        print(f"  ✓ Found: {'YES' if terms.get('terms_found') else 'NO'}")
        if terms.get('terms_url'):
            print(f"  ✓ URL: {terms['terms_url']}")
        print(f"  ✓ Scraping Prohibited: {'YES' if terms.get('scraping_explicitly_prohibited') else 'NO'}")
    
    # API analysis
    if 'api_analysis' in result:
        print("\n🔌 API AVAILABILITY:")
        api = result['api_analysis']
        print(f"  ✓ API Found: {'YES' if api.get('api_found') else 'NO'}")
        if api.get('api_documentation_url'):
            print(f"  ✓ Documentation: {api['api_documentation_url']}")
    
    # Required precautions
    if result.get('required_precautions'):
        print("\n⚠️  REQUIRED PRECAUTIONS:")
        for i, precaution in enumerate(result['required_precautions'], 1):
            print(f"  {i}. {precaution}")
    
    # Recommendations
    if result.get('recommendations'):
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "=" * 60)
    print(f"🏁 FINAL VERDICT: ", end="")
    if result['scraping_allowed']:
        print("✅ SCRAPING IS ALLOWED WITH PRECAUTIONS")
    else:
        print("❌ SCRAPING IS NOT ALLOWED")
    
    print(f"   Recommended Approach: {result.get('recommended_approach', 'Unknown')}")
    print("=" * 60)
    
    return result


async def test_multiple_sites():
    """Test compliance on multiple government sites for comparison."""
    
    print("\n\n🔍 Testing Multiple Government Sites for Comparison")
    print("=" * 60)
    
    test_sites = [
        {
            'url': 'https://www.tenders.vic.gov.au',
            'name': 'Victorian Government Tenders'
        },
        {
            'url': 'https://www.tenders.gov.au',
            'name': 'Australian Government Tenders'
        },
        {
            'url': 'https://qtenders.epw.qld.gov.au',
            'name': 'Queensland Government Tenders'
        }
    ]
    
    checker = TermsComplianceChecker()
    results = []
    
    for site in test_sites:
        print(f"\nChecking: {site['name']}...")
        try:
            result = await checker.check_site_compliance(site)
            results.append({
                'name': site['name'],
                'url': site['url'],
                'allowed': result['scraping_allowed'],
                'status': result['compliance_status'],
                'risk': result['risk_level']
            })
        except Exception as e:
            print(f"  ❌ Error checking {site['name']}: {e}")
            results.append({
                'name': site['name'],
                'url': site['url'],
                'allowed': False,
                'status': 'error',
                'risk': 'unknown'
            })
    
    # Summary table
    print("\n📊 COMPLIANCE SUMMARY:")
    print("-" * 80)
    print(f"{'Site Name':<35} {'Allowed':<10} {'Status':<25} {'Risk':<10}")
    print("-" * 80)
    
    for r in results:
        allowed = "✅ YES" if r['allowed'] else "❌ NO"
        print(f"{r['name']:<35} {allowed:<10} {r['status']:<25} {r['risk']:<10}")
    
    print("-" * 80)


if __name__ == "__main__":
    # Run the compliance test
    asyncio.run(test_compliance_checker())
    
    # Optionally test multiple sites
    if "--compare" in sys.argv:
        asyncio.run(test_multiple_sites())