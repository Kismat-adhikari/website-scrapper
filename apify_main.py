"""
Apify Actor Entry Point - Website & Email Scraper
Production-ready scraper optimized for Apify deployment

This wraps your existing ultimate_scraper_optimized.py for Apify compatibility
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

# Try to import Apify SDK
try:
    from apify import Actor
    APIFY_MODE = True
except ImportError:
    APIFY_MODE = False
    print("⚠️  Running in LOCAL mode (Apify SDK not installed)")
    print("   Install with: pip install apify")

# Import async scraper for Apify
from apify_scraper_async import AsyncWebsiteScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApifyWebsiteScraper:
    """
    Apify-compatible wrapper for your existing scraper.
    Handles input/output, progress tracking, and Apify integration.
    """
    
    def __init__(self, config: Dict):
        """Initialize with Apify input configuration"""
        self.config = config
        self.results = []
        self.failed_urls = []
        self.processed_count = 0
        self.total_count = 0
        self.start_time = datetime.now()
        
    async def scrape_single_url(self, url: str, scraper: AsyncWebsiteScraper) -> Optional[Dict]:
        """
        Scrape a single URL using async scraper.
        
        Args:
            url: URL to scrape
            scraper: Async scraper instance
            
        Returns:
            Dict with scraped data or None if failed
        """
        logger.info(f"[{self.processed_count + 1}/{self.total_count}] Scraping: {url}")
        
        try:
            result = await scraper.scrape_url(url)
            
            self.processed_count += 1
            
            # Log progress
            progress = (self.processed_count / self.total_count) * 100
            logger.info(f"✓ Success | Progress: {progress:.1f}% | Emails: {result['email_count']} | Phones: {result['phone_count']}")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Failed: {url} - {str(e)}")
            self.failed_urls.append({
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self.processed_count += 1
            return None
    
    def calculate_confidence(self, email_count: int, phone_count: int, 
                           social_count: int, has_form: bool) -> float:
        """Calculate confidence score based on data found"""
        score = 0.0
        
        # Email found (most important)
        if email_count > 0:
            score += 0.5
        
        # Phone found
        if phone_count > 0:
            score += 0.2
        
        # Social links found
        if social_count > 0:
            score += 0.15
        
        # Contact form found
        if has_form:
            score += 0.15
        
        return min(score, 1.0)
    
    async def scrape_bulk_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs with progress tracking.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraped data dictionaries
        """
        self.total_count = len(urls)
        logger.info(f"🚀 Starting bulk scrape: {self.total_count} URLs")
        logger.info(f"⚙️  Max Concurrency: {self.config.get('maxConcurrency', 10)}")
        
        # Only use proxy if explicitly requested (auto-enable disabled for now)
        use_proxy = self.config.get('useProxy', False)
        
        # Configure Apify proxy if enabled
        proxy_config = None
        if use_proxy and APIFY_MODE:
            # Use Apify's proxy (requires Apify proxy subscription)
            # Note: This requires valid Apify proxy credentials
            logger.warning("⚠️  Proxy requested but not configured. Set up Apify proxy in your account.")
            logger.info("ℹ️  Running without proxy for now...")
            use_proxy = False  # Disable until properly configured
        
        # Initialize async scraper
        scraper = AsyncWebsiteScraper(use_proxy=use_proxy, proxy_config=proxy_config)
        await scraper.start()
        
        try:
            # Process URLs sequentially
            for url in urls:
                result = await self.scrape_single_url(url, scraper)
                
                if result:
                    # Check confidence threshold
                    min_confidence = self.config.get('minConfidenceScore', 0.0)
                    if result['confidence_score'] >= min_confidence:
                        self.results.append(result)
                        
                        # Save to Apify dataset incrementally
                        if APIFY_MODE:
                            await Actor.push_data(result)
                
                # Save progress every 10 URLs
                if self.processed_count % 10 == 0:
                    await self.save_progress()
            
        finally:
            # Cleanup
            await scraper.close()
        
        return self.results
    
    async def save_progress(self):
        """Save progress for resume capability"""
        if not APIFY_MODE:
            return
        
        progress_data = {
            'processed_count': self.processed_count,
            'total_count': self.total_count,
            'percentage': (self.processed_count / self.total_count * 100) if self.total_count > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        await Actor.set_value('PROGRESS', progress_data)
    
    async def save_failed_urls(self):
        """Save failed URLs log"""
        if not self.failed_urls:
            return
        
        if APIFY_MODE:
            await Actor.set_value('FAILED_URLS', self.failed_urls)
        else:
            with open('failed_urls.json', 'w') as f:
                json.dump(self.failed_urls, f, indent=2)
    
    async def generate_final_report(self) -> Dict:
        """Generate comprehensive final report"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        report = {
            'summary': {
                'total_urls': self.total_count,
                'successful': len(self.results),
                'failed': len(self.failed_urls),
                'success_rate': (len(self.results) / self.total_count * 100) if self.total_count > 0 else 0,
                'duration_seconds': elapsed
            },
            'data_found': {
                'total_emails': sum(r.get('email_count', 0) for r in self.results),
                'total_phones': sum(r.get('phone_count', 0) for r in self.results),
                'total_socials': sum(r.get('social_count', 0) for r in self.results),
                'avg_confidence': sum(r.get('confidence_score', 0) for r in self.results) / len(self.results) if self.results else 0
            },
            'failed_urls': self.failed_urls,
            'timestamp': datetime.now().isoformat()
        }
        
        if APIFY_MODE:
            await Actor.set_value('FINAL_REPORT', report)
        else:
            with open('final_report.json', 'w') as f:
                json.dump(report, f, indent=2)
        
        return report


async def main():
    """
    Main entry point for Apify Actor.
    Handles both Apify and local execution.
    """
    
    if APIFY_MODE:
        # ============================================================
        # APIFY MODE
        # ============================================================
        async with Actor:
            logger.info("🚀 Starting Apify Actor: Website & Email Scraper")
            
            # Get input from Apify
            actor_input = await Actor.get_input() or {}
            logger.info(f"📥 Input received: {len(actor_input.get('urls', []))} URLs")
            
            # Parse URLs
            urls = actor_input.get('urls', [])
            if isinstance(urls, str):
                urls = [urls]
            elif isinstance(urls, list):
                # Handle Apify's requestListSources format
                parsed_urls = []
                for item in urls:
                    if isinstance(item, dict):
                        parsed_urls.append(item.get('url', ''))
                    else:
                        parsed_urls.append(str(item))
                urls = [u for u in parsed_urls if u]
            
            if not urls:
                logger.error("❌ No URLs provided in input!")
                return
            
            # Create configuration
            config = {
                'maxConcurrency': actor_input.get('maxConcurrency', 10),
                'depth': actor_input.get('depth', 2),
                'timeout': actor_input.get('timeout', 30),
                'retryAttempts': actor_input.get('retryAttempts', 3),
                'useProxy': actor_input.get('useProxy', False),
                'minConfidenceScore': actor_input.get('minConfidenceScore', 0.0)
            }
            
            # Initialize scraper
            scraper = ApifyWebsiteScraper(config)
            
            # Scrape URLs
            await scraper.scrape_bulk_urls(urls)
            
            # Save failed URLs
            await scraper.save_failed_urls()
            
            # Generate final report
            report = await scraper.generate_final_report()
            
            # Log summary
            logger.info("=" * 60)
            logger.info("✅ SCRAPING COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Total URLs: {report['summary']['total_urls']}")
            logger.info(f"Successful: {report['summary']['successful']}")
            logger.info(f"Failed: {report['summary']['failed']}")
            logger.info(f"Success Rate: {report['summary']['success_rate']:.1f}%")
            logger.info(f"Emails Found: {report['data_found']['total_emails']}")
            logger.info(f"Phones Found: {report['data_found']['total_phones']}")
            logger.info(f"Duration: {report['summary']['duration_seconds']:.1f}s")
            logger.info("=" * 60)
            
    else:
        # ============================================================
        # LOCAL MODE
        # ============================================================
        logger.info("🖥️  Running in LOCAL mode")
        logger.info("   (For Apify deployment, install: pip install apify)")
        
        # Load input from file or use default
        try:
            with open('apify_input.json', 'r') as f:
                local_input = json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️  apify_input.json not found, using default input")
            local_input = {
                'urls': ['https://example.com'],
                'maxConcurrency': 5,
                'depth': 2
            }
        
        urls = local_input.get('urls', [])
        if isinstance(urls, str):
            urls = [urls]
        
        # Create configuration
        config = {
            'maxConcurrency': local_input.get('maxConcurrency', 5),
            'depth': local_input.get('depth', 2),
            'timeout': local_input.get('timeout', 30),
            'retryAttempts': local_input.get('retryAttempts', 3),
            'useProxy': local_input.get('useProxy', False),
            'minConfidenceScore': local_input.get('minConfidenceScore', 0.0)
        }
        
        # Initialize scraper
        scraper = ApifyWebsiteScraper(config)
        
        # Scrape URLs
        await scraper.scrape_bulk_urls(urls)
        
        # Save results locally
        with open('apify_results.json', 'w') as f:
            json.dump(scraper.results, f, indent=2)
        
        # Save failed URLs
        await scraper.save_failed_urls()
        
        # Generate final report
        report = await scraper.generate_final_report()
        
        # Log summary
        logger.info("=" * 60)
        logger.info("✅ SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total URLs: {report['summary']['total_urls']}")
        logger.info(f"Successful: {report['summary']['successful']}")
        logger.info(f"Failed: {report['summary']['failed']}")
        logger.info(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        logger.info(f"Emails Found: {report['data_found']['total_emails']}")
        logger.info(f"Phones Found: {report['data_found']['total_phones']}")
        logger.info(f"Duration: {report['summary']['duration_seconds']:.1f}s")
        logger.info("=" * 60)
        logger.info("📁 Results saved to: apify_results.json")
        logger.info("📁 Report saved to: final_report.json")


if __name__ == '__main__':
    asyncio.run(main())
