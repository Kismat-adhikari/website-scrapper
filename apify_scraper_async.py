"""
Async Playwright Scraper for Apify
Fully async implementation to avoid threading issues
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


class AsyncWebsiteScraper:
    """Async scraper using Playwright async API"""
    
    def __init__(self, use_proxy: bool = False, proxy_config: Optional[Dict] = None):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.use_proxy = use_proxy
        self.proxy_config = proxy_config
        
    async def start(self):
        """Initialize async Playwright"""
        self.playwright = await async_playwright().start()
        
        launch_args = {
            'headless': True,
            'args': ['--no-sandbox', '--disable-setuid-sandbox']
        }
        
        # Add proxy if configured
        if self.use_proxy and self.proxy_config:
            launch_args['proxy'] = self.proxy_config
            logger.info(f"🔒 Using proxy: {self.proxy_config.get('server', 'configured')}")
        
        self.browser = await self.playwright.chromium.launch(**launch_args)
        
    async def close(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_url(self, url: str) -> Dict:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict with scraped data
        """
        page = await self.browser.new_page()
        
        try:
            # Load page
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for dynamic content
            
            # Extract data
            title = await page.title()
            content = await page.content()
            
            # Extract emails
            emails = self._extract_emails(content)
            
            # Extract phones
            phones = self._extract_phones(content)
            
            # Extract social links
            social_links = await self._extract_social_links(page)
            
            # Extract address
            address = self._extract_address(content)
            
            # Extract metadata
            meta_desc = await page.locator('meta[name="description"]').get_attribute('content') or ''
            
            # Calculate confidence
            confidence = self._calculate_confidence(emails, phones, social_links)
            
            return {
                'url': url,
                'title': title,
                'emails': emails,
                'phones': phones,
                'address': address,
                'social_links': social_links,
                'meta_description': meta_desc,
                'confidence_score': confidence,
                'email_count': len(emails),
                'phone_count': len(phones),
                'social_count': len(social_links),
                'scrape_timestamp': datetime.now().isoformat(),
                'scrape_method': 'async_browser'
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'title': '',
                'emails': [],
                'phones': [],
                'address': '',
                'social_links': [],
                'meta_description': '',
                'confidence_score': 0.0,
                'email_count': 0,
                'phone_count': 0,
                'social_count': 0,
                'scrape_timestamp': datetime.now().isoformat(),
                'scrape_method': 'async_browser',
                'error': str(e)
            }
        finally:
            await page.close()
    
    def _extract_emails(self, content: str) -> List[str]:
        """Extract email addresses from content"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = list(set(re.findall(email_pattern, content)))
        # Filter out common false positives
        emails = [e for e in emails if not any(x in e.lower() for x in ['example.com', 'test.com', 'domain.com'])]
        return emails[:10]  # Limit to 10
    
    def _extract_phones(self, content: str) -> List[str]:
        """Extract phone numbers from content"""
        phone_patterns = [
            r'\+?1?\s*\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US
            r'\+?([0-9]{1,3})\s*\(?([0-9]{2,4})\)?[-.\s]?([0-9]{3,4})[-.\s]?([0-9]{4})',  # International
        ]
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                    if len(phone) >= 10:
                        phones.append(phone)
        return list(set(phones))[:10]  # Limit to 10
    
    async def _extract_social_links(self, page: Page) -> List[str]:
        """Extract social media links"""
        social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 
                         'youtube.com', 'tiktok.com', 'pinterest.com']
        
        links = await page.locator('a[href]').all()
        social_links = []
        
        for link in links[:100]:  # Limit to first 100 links
            try:
                href = await link.get_attribute('href')
                if href and any(domain in href.lower() for domain in social_domains):
                    social_links.append(href)
            except:
                continue
        
        return list(set(social_links))[:10]  # Limit to 10
    
    def _extract_address(self, content: str) -> str:
        """Extract address from content"""
        # Simple address extraction - look for common patterns
        address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way)[,\s]+[\w\s]+,\s*[A-Z]{2}\s*\d{5}'
        matches = re.findall(address_pattern, content, re.IGNORECASE)
        return matches[0] if matches else ''
    
    def _calculate_confidence(self, emails: List, phones: List, socials: List) -> float:
        """Calculate confidence score"""
        score = 0.0
        if emails:
            score += 0.5
        if phones:
            score += 0.3
        if socials:
            score += 0.2
        return min(score, 1.0)
