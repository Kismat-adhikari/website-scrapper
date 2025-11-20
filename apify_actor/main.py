"""
Professional Website & Email Scraper - Apify Actor
Production-ready scraper optimized for both local use and Apify deployment

Features:
- Single and bulk URL scraping
- Email, phone, address, social media extraction
- Automatic page discovery (contact, about, support, etc.)
- Verification and completion tracking
- Resume capability
- Error handling and retry logic
- Optimized performance with parallel processing
- Apify dataset and Key-Value Store integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Try to import Apify SDK, fall back to local mode if not available
try:
    from apify import Actor
    APIFY_MODE = True
except ImportError:
    APIFY_MODE = False
    print("Running in LOCAL mode (Apify SDK not found)")

# Import our scraper modules
from scraper_core import ScraperCore
from url_processor import URLProcessor
from data_extractor import DataExtractor
from verification import VerificationManager
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebsiteEmailScraper:
    """
    Main scraper class that orchestrates the entire scraping process.
    Works both locally and on Apify platform.
    """
    
    def __init__(self, config: Config):
        """Initialize scraper with configuration"""
        self.config = config
        self.scraper_core = ScraperCore(config)
        self.url_processor = URLProcessor(config)
        self.data_extractor = DataExtractor(config)
        self.verification = VerificationManager(config)
        
        self.results = []
        self.failed_urls = []
        self.processed_count = 0
        self.total_count = 0
        
    async def scrape_single_url(self, url: str) -> Dict:
        """
        Scrape a single URL with full verification.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict with scraped data
        """
        logger.info(f"Scraping: {url}")
        
        try:
            # Start verification tracking
            tracker = self.verification.create_tracker(url)
            
            # Process URL and discover pages
            pages_to_scrape = await self.url_processor.discover_pages(url, self.config.depth)
            tracker.mark_pages_discovered(pages_to_scrape)
            
            # Scrape all discovered pages
            all_data = []
            for page_url in pages_to_scrape:
                page_data = await self.scraper_core.scrape_page(page_url)
                if page_data:
                    all_data.append(page_data)
                    tracker.mark_page_scraped(page_url, success=True)
                else:
                    tracker.mark_page_scraped(page_url, success=False)
            
            # Extract and consolidate data
            consolidated_data = self.data_extractor.consolidate_data(url, all_data)
            
            # Verify completeness
            tracker.add_emails(consolidated_data.get('emails', []))
            tracker.mark_emails_cleaned()
            
            # Add verification report
            consolidated_data['verification'] = tracker.get_summary()
            consolidated_data['confidence_score'] = tracker.calculate_confidence()
            
            self.processed_count += 1
            logger.info(f"✓ Completed: {url} ({self.processed_count}/{self.total_count})")
            
            return consolidated_data
            
        except Exception as e:
            logger.error(f"✗ Failed: {url} - {str(e)}")
            self.failed_urls.append({
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return None
    
    async def scrape_bulk_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs with parallel processing and resume capability.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraped data dictionaries
        """
        self.total_count = len(urls)
        logger.info(f"Starting bulk scrape: {self.total_count} URLs")
        
        # Check for resume data
        resume_data = await self.load_resume_data()
        if resume_data:
            processed_urls = set(resume_data.get('processed_urls', []))
            urls = [url for url in urls if url not in processed_urls]
            self.processed_count = len(processed_urls)
            logger.info(f"Resuming from {self.processed_count} processed URLs")
        
        # Process URLs with concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                result = await self.scrape_single_url(url)
                
                # Save progress for resume capability
                if self.processed_count % 10 == 0:
                    await self.save_resume_data()
                
                return result
        
        # Create tasks for all URLs
        tasks = [scrape_with_semaphore(url) for url in urls]
        
        # Execute with progress tracking
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                results.append(result)
                
                # Save to dataset incrementally (Apify or local)
                await self.save_result(result)
            
            # Log progress
            progress = (self.processed_count / self.total_count) * 100
            logger.info(f"Progress: {progress:.1f}% ({self.processed_count}/{self.total_count})")
        
        return results
    
    async def save_result(self, result: Dict):
        """Save result to Apify dataset or local file"""
        if APIFY_MODE:
            await Actor.push_data(result)
        else:
            self.results.append(result)
    
    async def save_resume_data(self):
        """Save resume data for crash recovery"""
        resume_data = {
            'processed_urls': [r['url'] for r in self.results],
            'processed_count': self.processed_count,
            'timestamp': datetime.now().isoformat()
        }
        
        if APIFY_MODE:
            await Actor.set_value('RESUME_DATA', resume_data)
        else:
            with open('resume_data.json', 'w') as f:
                json.dump(resume_data, f)
    
    async def load_resume_data(self) -> Optional[Dict]:
        """Load resume data if exists"""
        try:
            if APIFY_MODE:
                return await Actor.get_value('RESUME_DATA')
            else:
                if Path('resume_data.json').exists():
                    with open('resume_data.json', 'r') as f:
                        return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load resume data: {e}")
        return None
    
    async def save_failed_urls(self):
        """Save failed URLs log"""
        if self.failed_urls:
            if APIFY_MODE:
                await Actor.set_value('FAILED_URLS', self.failed_urls)
            else:
                with open('failed_urls.json', 'w') as f:
                    json.dump(self.failed_urls, f, indent=2)
    
    async def generate_final_report(self) -> Dict:
        """Generate comprehensive final report"""
        report = {
            'summary': {
                'total_urls': self.total_count,
                'successful': self.processed_count - len(self.failed_urls),
                'failed': len(self.failed_urls),
                'success_rate': ((self.processed_count - len(self.failed_urls)) / self.total_count * 100) if self.total_count > 0 else 0
            },
            'emails_found': sum(len(r.get('emails', [])) for r in self.results),
            'phones_found': sum(len(r.get('phones', [])) for r in self.results),
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
    Main entry point for the Actor.
    Handles both Apify and local execution.
    """
    
    if APIFY_MODE:
        async with Actor:
            # Get input from Apify
            actor_input = await Actor.get_input() or {}
            logger.info(f"Actor input: {actor_input}")
            
            # Parse input
            urls = actor_input.get('urls', [])
            if isinstance(urls, str):
                urls = [urls]
            
            # Create configuration from input
            config = Config(
                max_concurrent=actor_input.get('maxConcurrency', 10),
                depth=actor_input.get('depth', 2),
                timeout=actor_input.get('timeout', 30),
                retry_attempts=actor_input.get('retryAttempts', 3),
                use_proxy=actor_input.get('useProxy', False)
            )
            
            # Initialize scraper
            scraper = WebsiteEmailScraper(config)
            
            # Scrape URLs
            if len(urls) == 1:
                result = await scraper.scrape_single_url(urls[0])
                if result:
                    await Actor.push_data(result)
            else:
                await scraper.scrape_bulk_urls(urls)
            
            # Save failed URLs
            await scraper.save_failed_urls()
            
            # Generate final report
            report = await scraper.generate_final_report()
            logger.info(f"Scraping complete: {report['summary']}")
            
    else:
        # Local execution
        logger.info("Running in LOCAL mode")
        
        # Load input from file or use default
        try:
            with open('input.json', 'r') as f:
                local_input = json.load(f)
        except FileNotFoundError:
            local_input = {
                'urls': ['https://example.com'],
                'maxConcurrency': 5,
                'depth': 2
            }
        
        urls = local_input.get('urls', [])
        if isinstance(urls, str):
            urls = [urls]
        
        # Create configuration
        config = Config(
            max_concurrent=local_input.get('maxConcurrency', 5),
            depth=local_input.get('depth', 2),
            timeout=local_input.get('timeout', 30),
            retry_attempts=local_input.get('retryAttempts', 3),
            use_proxy=local_input.get('useProxy', False)
        )
        
        # Initialize scraper
        scraper = WebsiteEmailScraper(config)
        
        # Scrape URLs
        if len(urls) == 1:
            result = await scraper.scrape_single_url(urls[0])
            if result:
                scraper.results.append(result)
        else:
            await scraper.scrape_bulk_urls(urls)
        
        # Save results locally
        with open('results.json', 'w') as f:
            json.dump(scraper.results, f, indent=2)
        
        # Save failed URLs
        await scraper.save_failed_urls()
        
        # Generate final report
        report = await scraper.generate_final_report()
        
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total URLs: {report['summary']['total_urls']}")
        logger.info(f"Successful: {report['summary']['successful']}")
        logger.info(f"Failed: {report['summary']['failed']}")
        logger.info(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        logger.info(f"Emails Found: {report['emails_found']}")
        logger.info(f"Phones Found: {report['phones_found']}")
        logger.info("=" * 60)
        logger.info("Results saved to: results.json")
        logger.info("Report saved to: final_report.json")


if __name__ == '__main__':
    asyncio.run(main())
