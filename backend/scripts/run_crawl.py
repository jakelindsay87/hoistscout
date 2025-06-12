"""Main crawl runner script for HoistScraper."""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

import yaml

# Add the parent directory to the path so we can import hoistscraper modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.registry import Registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crawl.log')
    ]
)
logger = logging.getLogger(__name__)


def load_yaml(config_path: str) -> List[Dict[str, Any]]:
    """Load site configurations from YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        List of site configuration dictionaries
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            # Try relative to script directory
            script_dir = Path(__file__).parent
            config_file = script_dir / config_path
            
        if not config_file.exists():
            # Try relative to backend directory
            backend_dir = Path(__file__).parent.parent
            config_file = backend_dir / config_path
            
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if isinstance(data, list):
            return data
        else:
            return [data]
            
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
        raise


async def run_single_site(site_config: Dict[str, Any], proxy_pool: List[str]) -> Dict[str, Any]:
    """Run crawl for a single site.
    
    Args:
        site_config: Site configuration dictionary
        proxy_pool: List of proxy URLs
        
    Returns:
        Crawl results dictionary
    """
    registry = Registry(site_config, proxy_pool)
    try:
        results = await registry.crawl()
        return results
    finally:
        await registry.cleanup()


async def main(cfg: str = "sites.yml", once: bool = False, analyze_terms: bool = False):
    """Main crawl execution function.
    
    Args:
        cfg: Path to configuration file
        once: If True, run once and exit. If False, could be extended for scheduling
        analyze_terms: If True, also analyze terms and conditions
    """
    try:
        logger.info(f"Starting crawl with config: {cfg}")
        
        # Load site configurations
        sites = load_yaml(cfg)
        logger.info(f"Loaded {len(sites)} site configurations")
        
        # Get proxy pool from environment
        proxy_pool = []
        if os.getenv("PROXY_URLS"):
            proxy_pool = [url.strip() for url in os.getenv("PROXY_URLS").split(",") if url.strip()]
            logger.info(f"Using {len(proxy_pool)} proxies")
        
        # Filter sites based on status
        active_sites = [
            site for site in sites 
            if site.get("status") not in ("captcha_blocked", "legal_blocked", "disabled")
        ]
        
        if not active_sites:
            logger.warning("No active sites found to crawl")
            return
        
        logger.info(f"Crawling {len(active_sites)} active sites")
        
        # Create crawl tasks
        tasks = [
            run_single_site(site, proxy_pool) 
            for site in active_sites
        ]
        
        # Execute all crawls concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_crawls = 0
        failed_crawls = 0
        total_opportunities = 0
        
        for i, result in enumerate(results):
            site_name = active_sites[i].get("name", f"Site {i}")
            
            if isinstance(result, Exception):
                logger.error(f"Crawl failed for {site_name}: {str(result)}")
                failed_crawls += 1
            else:
                if result.get("status") == "completed":
                    successful_crawls += 1
                    opportunities = len(result.get("opportunities", []))
                    total_opportunities += opportunities
                    logger.info(f"Crawl completed for {site_name}: {opportunities} opportunities")
                else:
                    failed_crawls += 1
                    logger.error(f"Crawl failed for {site_name}: {result.get('error', 'Unknown error')}")
        
        # Terms analysis if requested
        if analyze_terms:
            logger.info("Starting terms and conditions analysis")
            terms_tasks = []
            
            for site in active_sites:
                registry = Registry(site, proxy_pool)
                terms_tasks.append(registry.analyze_terms())
            
            terms_results = await asyncio.gather(*terms_tasks, return_exceptions=True)
            
            for i, terms_result in enumerate(terms_results):
                site_name = active_sites[i].get("name", f"Site {i}")
                
                if isinstance(terms_result, Exception):
                    logger.error(f"Terms analysis failed for {site_name}: {str(terms_result)}")
                else:
                    allows_commercial = terms_result.get("allows_commercial_use", False)
                    forbids_scraping = terms_result.get("forbids_scraping", True)
                    logger.info(f"Terms analysis for {site_name}: "
                               f"Commercial use: {allows_commercial}, "
                               f"Forbids scraping: {forbids_scraping}")
        
        # Summary
        logger.info(f"Crawl summary: {successful_crawls} successful, {failed_crawls} failed, "
                   f"{total_opportunities} total opportunities found")
        
        # Save results to file
        output_file = f"crawl_results_{asyncio.get_event_loop().time()}.json"
        try:
            import json
            with open(output_file, 'w') as f:
                json.dump({
                    "summary": {
                        "successful_crawls": successful_crawls,
                        "failed_crawls": failed_crawls,
                        "total_opportunities": total_opportunities,
                        "sites_crawled": len(active_sites)
                    },
                    "results": [r for r in results if not isinstance(r, Exception)]
                }, f, indent=2, default=str)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.warning(f"Failed to save results: {str(e)}")
        
    except Exception as e:
        logger.error(f"Main crawl execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HoistScraper crawl runner")
    parser.add_argument("--config", "-c", default="sites.yml", 
                       help="Path to configuration file (default: sites.yml)")
    parser.add_argument("--once", action="store_true", 
                       help="Run once and exit (default behavior)")
    parser.add_argument("--analyze-terms", action="store_true",
                       help="Also analyze terms and conditions")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        asyncio.run(main(cfg=args.config, once=args.once, analyze_terms=args.analyze_terms))
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        sys.exit(1) 