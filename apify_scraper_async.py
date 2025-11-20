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
            # Load page FAST - aggressive timeout
            await page.goto(url, wait_until='domcontentloaded', timeout=8000)
            
            # Minimal wait for dynamic content
            await page.wait_for_timeout(300)
            
            # Quick scroll to load lazy content
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(200)
            
            # Extract data
            title = await page.title()
            content = await page.content()
            
            # Also get visible text for better extraction
            try:
                visible_text = await page.evaluate('document.body.innerText')
                # Combine HTML and visible text for better extraction
                full_content = content + '\n' + visible_text
            except:
                full_content = content
            
            # Extract emails
            emails = self._extract_emails(full_content)
            
            # Extract phones
            phones = self._extract_phones(full_content)
            
            # Extract social links
            social_links = await self._extract_social_links(page)
            
            # Extract address
            address = self._extract_address(full_content)
            
            # Extract metadata
            try:
                meta_desc = await page.locator('meta[name="description"]').get_attribute('content', timeout=5000) or ''
            except:
                meta_desc = ''
            
            # Calculate confidence
            confidence = self._calculate_confidence(emails, phones, social_links)
            
            logger.info(f"✓ {url}: {len(emails)} emails, {len(phones)} phones, {len(social_links)} socials")
            
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
        
        # Filter out common false positives and invalid emails
        filtered = []
        for email in emails:
            email_lower = email.lower()
            
            # Skip image files (major false positive source)
            if any(ext in email_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp', '.tiff']):
                continue
            
            # Skip common false positives
            if any(x in email_lower for x in ['example.com', 'test.com', 'domain.com', 'sentry.io', 
                                               'schema.org', 'w3.org', 'example.org', 'placeholder',
                                               'yourname', 'youremail', 'noreply@', 'no-reply@']):
                continue
            
            # Skip emails with weird patterns
            if email.count('@') != 1:
                continue
            
            # Skip very short or very long emails
            if len(email) < 6 or len(email) > 100:
                continue
            
            # Must have valid TLD (top level domain)
            if not re.search(r'\.(com|org|net|edu|gov|mil|co|io|ai|dev|app|tech|info|biz)$', email_lower):
                continue
            
            # Skip if it looks like a file path or URL parameter
            if '/' in email or '\\' in email or '?' in email or '&' in email:
                continue
            
            filtered.append(email)
        
        return filtered[:10]  # Limit to 10
    
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
                    
                    # Only accept phones between 10-11 digits (standard phone length)
                    if len(phone) < 10 or len(phone) > 11:
                        continue
                    
                    # Skip if it looks like a timestamp (starts with 16 or 17 = year 2016/2017)
                    if phone.startswith('16') or phone.startswith('17') or phone.startswith('20'):
                        continue
                    
                    # Skip if all digits are the same (like 1111111111)
                    if len(set(phone)) == 1:
                        continue
                    
                    # Skip if too many repeating digits (more than 4 of the same digit in a row)
                    if any(str(i)*5 in phone for i in range(10)):
                        continue
                    
                    # Skip if it looks like an ID (too many repeating patterns)
                    if phone.count('0000') > 0 or phone.count('1111') > 0 or phone.count('9999') > 0:
                        continue
                    
                    # Skip obvious fake patterns
                    if phone.count('666666') > 0 or phone.count('777777') > 0 or phone.count('888888') > 0:
                        continue
                    
                    # Skip if more than 60% of digits are the same
                    most_common_digit = max(phone.count(str(i)) for i in range(10))
                    if most_common_digit > len(phone) * 0.6:
                        continue
                    
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
