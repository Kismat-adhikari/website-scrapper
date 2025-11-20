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

# Import your existing scraper components
from scraper import (
    BrowserManager, extract_emails, extract_phones, extract_address,
    extract_social_links, extract_metadata, extract_title,
    infer_industry, detect_contact_form, calculate_word_count,
    detect_blog, detect_products_services, clean_text, normalize_data,
    apply_defaults, generate_timestamp
)

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
        
    async def scrape_single_url(self, url: str, browser_manager: BrowserManager) -> Optional[Dict]:
        """
        Scrape a single URL using your existing scraper logic.
        
        Args:
            url: URL to scrape
            browser_manager: Shared browser manager instance
            
        Returns:
            Dict with scraped data or None if failed
        """
        logger.info(f"[{self.processed_count + 1}/{self.total_count}] Scraping: {url}")
        
        try:
            # Load page
            success = browser_manager.load_page(url)
            if not success:
                raise Exception("Failed to load page")
            
            # Scroll to load dynamic content
            browser_manager.scroll_to_bottom()
            
            # Extract all data using your existing functions
            page = browser_manager.page
            
            # Basic data
            extracted_url = url
            title = extract_title(page)
            metadata = extract_metadata(page)
            
            # Contact data
            emails = extract_emails(page)
            phones = extract_phones(page)
            address_data = extract_address(page)
            social_links = extract_social_links(page)
            
            # Page features
            industry = infer_industry(page)
            contact_form = detect_contact_form(page)
            word_count = calculate_word_count(page)
            blog_present = detect_blog(page)
            products_or_services = detect_products_services(page)
            
            # Clean and normalize data
            emails = clean_text(normalize_data(emails))
            phones = clean_text(phones)
            social_links = clean_text(normalize_data(social_links))
            emails, phones = apply_defaults(emails, phones)
            
            # Format address
            address_str = address_data.get('full', '')
            if not address_str and address_data.get('country'):
                address_str = address_data.get('country', '')
            
            # Calculate metrics
            email_count = len(emails) if isinstance(emails, list) else 0
            phone_count = len(phones) if isinstance(phones, list) else 0
            social_count = len(social_links) if isinstance(social_links, list) else 0
            
            # Calculate confidence score
            confidence_score = self.calculate_confidence(
                email_count, phone_count, social_count, contact_form
            )
            
            # Build result
            result = {
                'url': extracted_url,
                'title': title,
                'emails': emails if isinstance(emails, list) else [],
                'phones': phones if isinstance(phones, list) else [],
                'address': address_str,
                'social_links': social_links if isinstance(social_links, list) else [],
                'meta_description': metadata.get('meta_description', ''),
                'og_title': metadata.get('og_title', ''),
                'og_description': metadata.get('og_description', ''),
                'contact_form': contact_form,
                'industry': industry,
                'blog_present': blog_present,
                'products_or_services': products_or_services,
                'word_count': word_count,
                'email_count': email_count,
                'phone_count': phone_count,
                'social_count': social_count,
                'confidence_score': confidence_score,
                'scrape_timestamp': generate_timestamp(),
                'scrape_method': 'browser'
            }
            
            self.processed_count += 1
            
            # Log progress
            progress = (self.processed_count / self.total_count) * 100
            logger.info(f"✓ Success | Progress: {progress:.1f}% | Emails: {email_count} | Phones: {phone_count}")
            
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
        
        # Initialize browser manager (reuse for all URLs)
        browser_manager = BrowserManager()
        browser_manager.launch_browser()
        
        try:
            # Process URLs sequentially (browser manager handles one at a time)
            # For true parallel processing, we'd need multiple browser instances
            for url in urls:
                result = await self.scrape_single_url(url, browser_manager)
                
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
            browser_manager.close_browser()
        
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
