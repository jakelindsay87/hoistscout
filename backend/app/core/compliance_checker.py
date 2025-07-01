"""
Terms & Conditions Compliance System for Legal Web Scraping
Ensures all scraping activities comply with website terms, robots.txt, and legal requirements
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import Column, String, Boolean, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base

from ..database import Base
from ..core.simple_logging import ProductionLogger
from ..config import get_settings

settings = get_settings()
production_logger = ProductionLogger()


class ComplianceCache(Base):
    """Database model for caching compliance results"""
    __tablename__ = "compliance_cache"
    
    domain = Column(String, primary_key=True, index=True)
    compliance_data = Column(JSON)
    checked_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class TermsComplianceChecker:
    """Automated Terms & Conditions and legal compliance validation."""
    
    def __init__(self):
        self.logger = production_logger.get_logger("compliance_checker")
        self.compliance_cache = {}
        self.llm_analyzer = None  # Will be initialized when needed
        
    async def check_site_compliance(self, website_config: dict) -> dict:
        """Complete compliance check before scraping any website."""
        
        site_url = website_config['url']
        domain = urlparse(site_url).netloc
        
        self.logger.info(f"Starting compliance check for: {domain}")
        
        compliance_result = {
            'domain': domain,
            'compliance_status': 'unknown',
            'scraping_allowed': False,
            'restrictions': [],
            'recommendations': [],
            'checks_performed': {
                'robots_txt': False,
                'terms_conditions': False,
                'privacy_policy': False,
                'copyright_notice': False,
                'api_available': False,
                'rate_limits': False
            },
            'legal_analysis': {},
            'risk_assessment': 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # 1. Check robots.txt
            robots_result = await self.check_robots_txt(site_url)
            compliance_result['checks_performed']['robots_txt'] = True
            compliance_result['robots_analysis'] = robots_result
            
            # 2. Find and analyze Terms & Conditions
            terms_result = await self.analyze_terms_and_conditions(site_url)
            compliance_result['checks_performed']['terms_conditions'] = True
            compliance_result['terms_analysis'] = terms_result
            
            # 3. Check for API availability
            api_result = await self.check_api_availability(site_url)
            compliance_result['checks_performed']['api_available'] = True
            compliance_result['api_analysis'] = api_result
            
            # 4. Analyze privacy policy
            privacy_result = await self.analyze_privacy_policy(site_url)
            compliance_result['checks_performed']['privacy_policy'] = True
            compliance_result['privacy_analysis'] = privacy_result
            
            # 5. Check copyright notices
            copyright_result = await self.check_copyright_notices(site_url)
            compliance_result['checks_performed']['copyright_notice'] = True
            compliance_result['copyright_analysis'] = copyright_result
            
            # 6. Assess rate limiting requirements
            rate_limit_result = await self.assess_rate_limiting(site_url)
            compliance_result['checks_performed']['rate_limits'] = True
            compliance_result['rate_limit_analysis'] = rate_limit_result
            
            # 7. Generate overall compliance assessment
            overall_assessment = await self.generate_compliance_assessment(compliance_result)
            compliance_result.update(overall_assessment)
            
            # 8. Cache results for future use
            self.compliance_cache[domain] = compliance_result
            
            # 9. Log compliance summary
            self.logger.info(f"Compliance check complete for {domain}: "
                           f"Status={compliance_result['compliance_status']}, "
                           f"Allowed={compliance_result['scraping_allowed']}, "
                           f"Risk={compliance_result['risk_level']}")
            
            return compliance_result
            
        except Exception as e:
            self.logger.error(f"Compliance check failed for {domain}: {e}")
            compliance_result['error'] = str(e)
            compliance_result['compliance_status'] = 'error'
            return compliance_result
    
    async def check_robots_txt(self, site_url: str) -> dict:
        """Check robots.txt for scraping permissions."""
        
        robots_analysis = {
            'robots_txt_found': False,
            'user_agent_restrictions': [],
            'disallowed_paths': [],
            'crawl_delay': None,
            'sitemap_urls': [],
            'scraping_allowed': True,
            'specific_restrictions': []
        }
        
        try:
            robots_url = urljoin(site_url, '/robots.txt')
            
            async with httpx.AsyncClient() as client:
                response = await client.get(robots_url, timeout=10)
                
                if response.status_code == 200:
                    robots_analysis['robots_txt_found'] = True
                    robots_content = response.text
                    
                    # Parse robots.txt using built-in parser
                    rp = RobotFileParser()
                    rp.set_url(robots_url)
                    rp.parse(robots_content.splitlines())
                    
                    # Check if scraping is allowed for our user agent
                    test_paths = ['/tender/', '/search/', '/api/', '/documents/', '/opportunities/']
                    
                    for path in test_paths:
                        test_url = urljoin(site_url, path)
                        if not rp.can_fetch('*', test_url):
                            robots_analysis['disallowed_paths'].append(path)
                            robots_analysis['scraping_allowed'] = False
                    
                    # Extract additional information
                    lines = robots_content.split('\n')
                    current_user_agent = None
                    
                    for line in lines:
                        line = line.strip()
                        
                        if line.lower().startswith('user-agent:'):
                            current_user_agent = line.split(':', 1)[1].strip()
                        elif line.lower().startswith('crawl-delay:') and current_user_agent in ['*', 'HoistScout']:
                            try:
                                robots_analysis['crawl_delay'] = int(line.split(':', 1)[1].strip())
                            except:
                                pass
                        elif line.lower().startswith('sitemap:'):
                            robots_analysis['sitemap_urls'].append(line.split(':', 1)[1].strip())
                    
                    self.logger.info(f"Robots.txt analysis for {site_url}: "
                                   f"Found={robots_analysis['robots_txt_found']}, "
                                   f"Allowed={robots_analysis['scraping_allowed']}, "
                                   f"Disallowed paths={len(robots_analysis['disallowed_paths'])}")
                    
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt: {e}")
            robots_analysis['error'] = str(e)
        
        return robots_analysis
    
    async def analyze_terms_and_conditions(self, site_url: str) -> dict:
        """Find and analyze Terms & Conditions with LLM."""
        
        terms_analysis = {
            'terms_found': False,
            'terms_url': None,
            'scraping_explicitly_prohibited': False,
            'data_use_restrictions': [],
            'commercial_use_allowed': 'unknown',
            'attribution_required': False,
            'legal_notices': [],
            'risk_level': 'unknown'
        }
        
        try:
            # 1. Find Terms & Conditions page
            terms_url = await self.find_terms_page(site_url)
            
            if terms_url:
                terms_analysis['terms_found'] = True
                terms_analysis['terms_url'] = terms_url
                
                # 2. Extract terms content
                terms_content = await self.extract_page_content(terms_url)
                
                # 3. Analyze with LLM
                terms_llm_analysis = await self.analyze_legal_text_with_llm(
                    terms_content, 'terms_and_conditions'
                )
                
                terms_analysis.update(terms_llm_analysis)
                
                self.logger.info(f"Terms analysis completed for: {terms_url}")
                
        except Exception as e:
            self.logger.error(f"Terms analysis failed: {e}")
            terms_analysis['error'] = str(e)
        
        return terms_analysis
    
    async def find_terms_page(self, site_url: str) -> Optional[str]:
        """Find Terms & Conditions page URL."""
        
        # Common terms page patterns
        terms_patterns = [
            '/terms',
            '/terms-and-conditions',
            '/terms-of-use',
            '/terms-of-service',
            '/legal',
            '/legal-notices',
            '/conditions-of-use',
            '/website-terms',
            '/site-terms',
            '/policies'
        ]
        
        async with httpx.AsyncClient() as client:
            # Try direct URL patterns first
            for pattern in terms_patterns:
                test_url = urljoin(site_url, pattern)
                try:
                    response = await client.get(test_url, timeout=5, follow_redirects=True)
                    if response.status_code == 200 and 'terms' in response.text.lower():
                        self.logger.info(f"Found terms page at: {test_url}")
                        return test_url
                except:
                    continue
            
            # Search homepage for terms links
            try:
                response = await client.get(site_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for terms links
                    terms_keywords = ['terms', 'conditions', 'legal', 'policy']
                    
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '').lower()
                        text = link.get_text().lower()
                        
                        if any(keyword in href or keyword in text for keyword in terms_keywords):
                            if 'terms' in href or 'terms' in text:
                                full_url = urljoin(site_url, link['href'])
                                self.logger.info(f"Found terms link: {full_url}")
                                return full_url
            except Exception as e:
                self.logger.error(f"Error searching for terms page: {e}")
        
        return None
    
    async def extract_page_content(self, url: str) -> str:
        """Extract text content from a webpage."""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # Get text
                    text = soup.get_text()
                    
                    # Break into lines and remove leading/trailing space
                    lines = (line.strip() for line in text.splitlines())
                    # Break multi-headlines into a line each
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    # Drop blank lines
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    return text[:10000]  # Limit to 10k characters for analysis
        except Exception as e:
            self.logger.error(f"Failed to extract content from {url}: {e}")
            return ""
    
    async def analyze_legal_text_with_llm(self, legal_text: str, document_type: str) -> dict:
        """Use LLM to analyze legal documents for scraping compliance."""
        
        # For now, we'll use pattern matching as a fallback
        # In production, this would call Ollama or another LLM
        
        analysis = {
            'scraping_explicitly_prohibited': False,
            'automated_access_prohibited': False,
            'data_use_restrictions': [],
            'commercial_use_allowed': 'unclear',
            'attribution_required': False,
            'rate_limiting_required': False,
            'prohibited_activities': [],
            'risk_assessment': 'medium',
            'recommendation': 'proceed_with_caution'
        }
        
        # Pattern matching for common legal terms
        legal_text_lower = legal_text.lower()
        
        # Check for explicit scraping prohibition
        scraping_prohibited_patterns = [
            'no automated access',
            'no scraping',
            'no data mining',
            'no robots',
            'no crawling',
            'no harvesting',
            'automated access is prohibited',
            'do not use automated'
        ]
        
        for pattern in scraping_prohibited_patterns:
            if pattern in legal_text_lower:
                analysis['scraping_explicitly_prohibited'] = True
                analysis['automated_access_prohibited'] = True
                analysis['risk_assessment'] = 'high'
                analysis['recommendation'] = 'do_not_proceed'
                break
        
        # Check for government/public data provisions
        if any(term in legal_text_lower for term in ['.gov.', 'government', 'public information', 'public data']):
            if 'public' in legal_text_lower and 'information' in legal_text_lower:
                analysis['risk_assessment'] = 'low'
                analysis['recommendation'] = 'proceed_with_caution'
                analysis['data_use_restrictions'].append('Use only for public information purposes')
        
        # Check for rate limiting requirements
        if any(term in legal_text_lower for term in ['rate limit', 'excessive requests', 'server load']):
            analysis['rate_limiting_required'] = True
            analysis['data_use_restrictions'].append('Implement rate limiting')
        
        # Check for attribution requirements
        if any(term in legal_text_lower for term in ['attribution', 'acknowledge', 'credit']):
            analysis['attribution_required'] = True
            analysis['data_use_restrictions'].append('Attribution required')
        
        return analysis
    
    async def analyze_privacy_policy(self, site_url: str) -> dict:
        """Analyze privacy policy for data collection restrictions."""
        
        privacy_analysis = {
            'privacy_policy_found': False,
            'personal_data_restrictions': [],
            'data_collection_allowed': True
        }
        
        # Similar pattern to finding terms page
        privacy_patterns = ['/privacy', '/privacy-policy', '/privacy-statement']
        
        async with httpx.AsyncClient() as client:
            for pattern in privacy_patterns:
                test_url = urljoin(site_url, pattern)
                try:
                    response = await client.get(test_url, timeout=5, follow_redirects=True)
                    if response.status_code == 200 and 'privacy' in response.text.lower():
                        privacy_analysis['privacy_policy_found'] = True
                        break
                except:
                    continue
        
        return privacy_analysis
    
    async def check_copyright_notices(self, site_url: str) -> dict:
        """Check for copyright notices and restrictions."""
        
        copyright_analysis = {
            'copyright_notice_found': False,
            'copyright_restrictions': []
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(site_url, timeout=10)
                if response.status_code == 200:
                    text_lower = response.text.lower()
                    if '©' in response.text or 'copyright' in text_lower:
                        copyright_analysis['copyright_notice_found'] = True
                        
                        # Check for specific copyright restrictions
                        if 'all rights reserved' in text_lower:
                            copyright_analysis['copyright_restrictions'].append('All rights reserved')
        except:
            pass
        
        return copyright_analysis
    
    async def check_api_availability(self, site_url: str) -> dict:
        """Check if the site offers an official API."""
        
        api_analysis = {
            'api_found': False,
            'api_endpoints': [],
            'api_documentation_url': None,
            'authentication_required': False,
            'rate_limits': None,
            'recommendation': 'use_scraping'
        }
        
        # Common API patterns
        api_patterns = [
            '/api',
            '/api/v1',
            '/api/v2',
            '/api/docs',
            '/swagger',
            '/openapi',
            '/graphql',
            '/rest',
            '/developers',
            '/api-docs',
            '/developer'
        ]
        
        async with httpx.AsyncClient() as client:
            for pattern in api_patterns:
                try:
                    api_url = urljoin(site_url, pattern)
                    response = await client.get(api_url, timeout=5, follow_redirects=True)
                    
                    if response.status_code == 200:
                        content = response.text.lower()
                        if any(term in content for term in ['api', 'endpoint', 'swagger', 'openapi', 'graphql']):
                            api_analysis['api_found'] = True
                            api_analysis['api_endpoints'].append(api_url)
                            
                            if 'documentation' in content or 'docs' in content:
                                api_analysis['api_documentation_url'] = api_url
                                api_analysis['recommendation'] = 'use_api_instead'
                            
                            self.logger.info(f"Found API at: {api_url}")
                            break
                except:
                    continue
        
        return api_analysis
    
    async def assess_rate_limiting(self, site_url: str) -> dict:
        """Assess appropriate rate limiting for the site."""
        
        rate_limit_analysis = {
            'suggested_delay_ms': 2000,  # Default 2 seconds
            'max_concurrent_requests': 1,
            'respect_business_hours': False,
            'notes': []
        }
        
        domain = urlparse(site_url).netloc
        
        # Government sites require more respectful rate limiting
        if any(gov in domain for gov in ['.gov.', '.gov.au', '.edu.', '.edu.au']):
            rate_limit_analysis['suggested_delay_ms'] = 3000
            rate_limit_analysis['respect_business_hours'] = True
            rate_limit_analysis['notes'].append('Government site - use conservative rate limiting')
        
        # Check if robots.txt specified crawl delay
        if hasattr(self, 'robots_crawl_delay') and self.robots_crawl_delay:
            rate_limit_analysis['suggested_delay_ms'] = max(
                self.robots_crawl_delay * 1000,
                rate_limit_analysis['suggested_delay_ms']
            )
            rate_limit_analysis['notes'].append(f'Robots.txt specifies crawl-delay: {self.robots_crawl_delay}s')
        
        return rate_limit_analysis
    
    async def generate_compliance_assessment(self, compliance_data: dict) -> dict:
        """Generate overall compliance assessment and recommendations."""
        
        assessment = {
            'compliance_status': 'unknown',
            'scraping_allowed': False,
            'risk_level': 'unknown',
            'required_precautions': [],
            'recommended_approach': 'do_not_proceed'
        }
        
        # Analyze all collected data
        robots_allowed = compliance_data.get('robots_analysis', {}).get('scraping_allowed', True)
        terms_prohibited = compliance_data.get('terms_analysis', {}).get('scraping_explicitly_prohibited', False)
        api_available = compliance_data.get('api_analysis', {}).get('api_found', False)
        
        # Decision logic
        if terms_prohibited:
            assessment['compliance_status'] = 'prohibited'
            assessment['scraping_allowed'] = False
            assessment['risk_level'] = 'high'
            assessment['recommended_approach'] = 'do_not_proceed'
            assessment['required_precautions'].append('Scraping explicitly prohibited in terms')
            
        elif not robots_allowed:
            assessment['compliance_status'] = 'restricted'
            assessment['scraping_allowed'] = False
            assessment['risk_level'] = 'medium'
            assessment['recommended_approach'] = 'do_not_proceed'
            assessment['required_precautions'].append('Restricted by robots.txt')
            
        elif api_available:
            assessment['compliance_status'] = 'api_preferred'
            assessment['scraping_allowed'] = True
            assessment['risk_level'] = 'low'
            assessment['recommended_approach'] = 'use_api_instead'
            assessment['required_precautions'].append('Use official API instead of scraping')
            
        else:
            # Check if it's a government domain
            domain = compliance_data['domain']
            if any(gov_domain in domain for gov_domain in ['.gov.', '.gov.au', '.qld.gov.au', '.nsw.gov.au', '.vic.gov.au']):
                assessment['compliance_status'] = 'allowed_with_precautions'
                assessment['scraping_allowed'] = True
                assessment['risk_level'] = 'low'
                assessment['recommended_approach'] = 'proceed_with_caution'
                assessment['required_precautions'] = [
                    'Respect rate limits (max 1 request per 2-3 seconds)',
                    'Only access public tender information',
                    'Do not overload servers',
                    'Include proper User-Agent identification',
                    'Consider business hours for heavy scraping',
                    'Monitor for any access restrictions or blocks',
                    'Comply with any specific terms for government data'
                ]
            else:
                assessment['compliance_status'] = 'unclear'
                assessment['scraping_allowed'] = False
                assessment['risk_level'] = 'medium'
                assessment['recommended_approach'] = 'seek_permission'
                assessment['required_precautions'].append('Terms unclear - recommend seeking explicit permission')
        
        return assessment


class ComplianceMonitor:
    """Monitor ongoing compliance during scraping operations."""
    
    def __init__(self):
        self.logger = production_logger.get_logger("compliance_monitor")
        self.violation_count = {}
        self.last_request_time = {}
        
    async def check_rate_limit_compliance(self, domain: str, required_delay_ms: int) -> bool:
        """Ensure rate limiting compliance."""
        
        current_time = asyncio.get_event_loop().time()
        last_time = self.last_request_time.get(domain, 0)
        
        time_since_last = (current_time - last_time) * 1000  # Convert to ms
        
        if time_since_last < required_delay_ms:
            self.logger.warning(f"Rate limit violation for {domain}: "
                              f"Only {time_since_last:.0f}ms since last request, "
                              f"required {required_delay_ms}ms")
            self.violation_count[domain] = self.violation_count.get(domain, 0) + 1
            
            # Stop after multiple violations
            if self.violation_count[domain] > 3:
                raise Exception(f"Multiple rate limit violations for {domain}. Stopping to ensure compliance.")
            
            # Wait for remaining time
            wait_time = (required_delay_ms - time_since_last) / 1000
            await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = asyncio.get_event_loop().time()
        return True
    
    async def log_compliance_action(self, action: str, domain: str, details: dict):
        """Log all compliance-related actions for audit trail."""
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'domain': domain,
            'details': details
        }
        
        self.logger.info(f"Compliance action: {action} for {domain}", extra=log_entry)
        
        # In production, this would also save to database for audit trail