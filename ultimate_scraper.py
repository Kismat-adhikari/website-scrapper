"""
ULTIMATE SCRAPER - Fast + Accurate Hybrid System

Strategy:
1. Try FAST HTTP scraping first (10-50x faster)
2. If fails or detects JavaScript, fall back to BROWSER scraping
3. Best of both worlds: Speed + Accuracy

Usage:
    python ultimate_scraper.py urls.txt
    python ultimate_scraper.py urls.txt --force-browser  # Always use browser
"""

import asyncio
import aiohttp
import time
import csv
import re
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from bs4 import BeautifulSoup

# Import browser scraper components
from scraper import (
    BrowserManager, load_proxies, get_next_proxy, reset_proxy_usage,
    extract_emails, extract_phones, extract_address, extract_social_links,
    extract_external_links, extract_descriptions, extract_messaging_links,
    extract_metadata, extract_title, extract_url,
    infer_industry, detect_contact_form, calculate_word_count,
    detect_blog, detect_products_services,
    clean_text, normalize_data, apply_defaults,
    generate_timestamp, ScrapedData
)


class UltimateScraper:
    """
    Hybrid scraper: Fast HTTP + Accurate Browser fallback
    """
    
    # Social media and platforms to reject
    BLOCKED_DOMAINS = [
        'facebook.com', 'fb.com', 'instagram.com', 'twitter.com', 'x.com',
        'linkedin.com', 'youtube.com', 'tiktok.com', 'snapchat.com',
        'pinterest.com', 'reddit.com', 'tumblr.com', 'whatsapp.com',
        'telegram.org', 't.me', 'discord.com', 'discord.gg',
        'twitch.tv', 'vimeo.com', 'flickr.com', 'medium.com'
    ]
    
    def __init__(self, force_browser=False, max_concurrent=10):
        self.force_browser = force_browser
        self.max_concurrent = max_concurrent
        self.results = []
        self.stats = {
            'total': 0,
            'http_success': 0,
            'browser_success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
        self.proxies = load_proxies()
        reset_proxy_usage()
    
    def is_social_media_url(self, url: str) -> bool:
        """Check if URL is a social media platform"""
        url_lower = url.lower()
        for domain in self.BLOCKED_DOMAINS:
            if domain in url_lower:
                return True
        return False
    
    def validate_url(self, url: str) -> tuple[bool, str]:
        """
        Validate URL before scraping.
        Returns: (is_valid, error_message)
        """
        # Check if it's a social media URL
        if self.is_social_media_url(url):
            return False, "Social media URLs are not supported (use business websites only)"
        
        # Check if URL has proper format
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        # Check for common invalid patterns
        if url.count('.') < 1:
            return False, "Invalid URL format (missing domain)"
        
        return True, ""
    
    def needs_browser(self, html: str) -> bool:
        """
        Detect if page needs browser rendering.
        Returns True if heavy JavaScript detected.
        """
        if not html:
            return True
        
        # Check for heavy JavaScript frameworks
        js_indicators = [
            'react', 'angular', 'vue.js', 'next.js',
            '__NEXT_DATA__', 'ng-app', 'v-app',
            'data-reactroot', 'data-react-helmet'
        ]
        
        html_lower = html.lower()
        for indicator in js_indicators:
            if indicator in html_lower:
                return True
        
        # Check if page is mostly empty (likely needs JS)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().strip()
        if len(text) < 200:  # Very little content
            return True
        
        return False
    
    async def try_http_scrape(self, session, url):
        """Try fast HTTP scraping first"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, timeout=timeout, ssl=False) as response:
                html = await response.text()
                
                # Check if browser needed
                if self.needs_browser(html):
                    return None, "needs_browser"
                
                # Parse with BeautifulSoup
                data = self.parse_http_response(url, html)
                return data, "http_success"
                
        except Exception as e:
            return None, f"http_error: {str(e)}"
    
    def parse_http_response(self, url, html):
        """Parse HTTP response quickly"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract basic data
        title = soup.title.string if soup.title else ""
        
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')
        
        # Extract emails
        emails = []
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        emails = [e.lower() for e in emails if '@' in e and '.' in e.split('@')[1]]
        emails = list(set(emails))[:5]
        
        # Extract phones
        phones = []
        phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, html)
        phones = list(set(phones))[:5]
        
        # Extract social links
        social_domains = ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'youtube.com']
        social_links = []
        for domain in social_domains:
            pattern = rf'https?://(?:www\.)?{re.escape(domain)}/[^\s"\'>]+'
            social_links.extend(re.findall(pattern, html))
        social_links = list(set(social_links))[:5]
        
        # Word count
        text = soup.get_text()
        word_count = len(text.split())
        
        # Features
        has_form = bool(soup.find('form'))
        has_blog = bool(re.search(r'blog|article', html, re.IGNORECASE))
        
        return {
            'url': url,
            'title': title[:100] if title else "",
            'emails': emails if emails else "NONE",
            'phones': phones if phones else "NONE",
            'social_links': social_links,
            'meta_description': meta_desc[:200] if meta_desc else "",
            'word_count': word_count,
            'contact_form': has_form,
            'blog_present': has_blog,
            'method': 'http'
        }
    
    def browser_scrape(self, url):
        """Fall back to accurate browser scraping"""
        browser_manager = None
        try:
            print(f"  → Using BROWSER for accuracy...")
            
            # Get proxy
            proxy_config = get_next_proxy() if self.proxies else None
            
            # Launch browser
            browser_manager = BrowserManager(proxy_config)
            browser_manager.launch_browser()
            
            # Load page
            if not browser_manager.load_page(url):
                return None
            
            # Scroll
            browser_manager.scroll_to_bottom()
            
            # Extract data (using existing accurate functions)
            page = browser_manager.page
            
            extracted_url = extract_url(page)
            title = extract_title(page)
            metadata = extract_metadata(page)
            emails = extract_emails(page)
            phones = extract_phones(page)
            address_data = extract_address(page)
            social_links = extract_social_links(page)
            external_links = extract_external_links(page)
            description = extract_descriptions(page)
            messaging = extract_messaging_links(page)
            
            industry = infer_industry(page)
            contact_form = detect_contact_form(page)
            word_count = calculate_word_count(page)
            blog_present = detect_blog(page)
            products_or_services = detect_products_services(page)
            
            timestamp = generate_timestamp()
            
            # Clean data
            emails = clean_text(normalize_data(emails))
            phones = clean_text(phones)
            social_links = clean_text(normalize_data(social_links))
            external_links = clean_text(normalize_data(external_links))
            emails, phones = apply_defaults(emails, phones)
            
            # Calculate metrics
            email_count = len(emails) if isinstance(emails, list) else 0
            phone_count = len(phones) if isinstance(phones, list) else 0
            social_count = len(social_links) if isinstance(social_links, list) else 0
            
            # Format address: use full address with country if available
            address_str = address_data.get('full', '')
            if not address_str and address_data.get('country'):
                # If no full address but have country, just use country
                address_str = address_data.get('country', '')
            
            return {
                'url': extracted_url,
                'title': title,
                'emails': emails,
                'phones': phones,
                'social_links': social_links,
                'external_links': external_links,
                'description': description,
                'meta_description': metadata.get('meta_description', ''),
                'og_title': metadata.get('og_title', ''),
                'og_description': metadata.get('og_description', ''),
                'og_image': metadata.get('og_image', ''),
                'address': address_str,  # Single address field
                'whatsapp': messaging.get('whatsapp', ''),
                'telegram': messaging.get('telegram', ''),
                'signal': messaging.get('signal', ''),
                'discord': messaging.get('discord', ''),
                'contact_form': contact_form,
                'industry': industry,
                'blog_present': blog_present,
                'products_or_services': products_or_services,
                'word_count': word_count,
                'scrape_timestamp': timestamp,
                'email_count': email_count,
                'phone_count': phone_count,
                'social_count': social_count,
                'method': 'browser'
            }
            
        except Exception as e:
            print(f"  → Browser scraping failed: {e}")
            return None
        finally:
            if browser_manager:
                browser_manager.close_browser()
    
    async def scrape_url(self, session, url, index, total):
        """Scrape a single URL with hybrid approach"""
        print(f"\n[{index}/{total}] {url}")
        
        # Validate URL first
        is_valid, error_msg = self.validate_url(url)
        if not is_valid:
            print(f"  ✗ SKIPPED: {error_msg}")
            self.stats['skipped'] += 1
            return {'url': url, 'status': 'skipped', 'reason': error_msg}
        
        # Force browser mode
        if self.force_browser:
            print(f"  → Using BROWSER (forced mode)")
            data = self.browser_scrape(url)
            if data:
                self.stats['browser_success'] += 1
                return data
            else:
                self.stats['failed'] += 1
                return {'url': url, 'status': 'failed', 'method': 'browser'}
        
        # Try HTTP first
        print(f"  → Trying FAST HTTP...")
        data, status = await self.try_http_scrape(session, url)
        
        if status == "http_success":
            print(f"  ✓ HTTP Success (FAST)")
            self.stats['http_success'] += 1
            return data
        
        elif status == "needs_browser":
            print(f"  → JavaScript detected, switching to BROWSER...")
            data = self.browser_scrape(url)
            if data:
                self.stats['browser_success'] += 1
                return data
            else:
                self.stats['failed'] += 1
                return {'url': url, 'status': 'failed', 'method': 'browser'}
        
        else:
            # HTTP failed, try browser
            print(f"  → HTTP failed, trying BROWSER...")
            data = self.browser_scrape(url)
            if data:
                self.stats['browser_success'] += 1
                return data
            else:
                self.stats['failed'] += 1
                return {'url': url, 'status': 'failed'}
    
    async def scrape_all(self, urls):
        """Scrape all URLs with hybrid approach"""
        self.stats['total'] = len(urls)
        self.stats['start_time'] = time.time()
        
        print("=" * 60)
        print("ULTIMATE SCRAPER - Fast + Accurate Hybrid")
        print("=" * 60)
        print(f"URLs to scrape: {len(urls)}")
        print(f"Strategy: HTTP first, Browser fallback")
        print("=" * 60)
        
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(limit=self.max_concurrent, ssl=False)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i, url in enumerate(urls, 1):
                data = await self.scrape_url(session, url, i, len(urls))
                if data:
                    self.results.append(data)
        
        self.stats['end_time'] = time.time()
    
    def save_to_csv(self, filename):
        """Save results to CSV"""
        if not self.results:
            print("\n[!] No results to save")
            return
        
        # Determine fieldnames based on data
        all_keys = set()
        for result in self.results:
            all_keys.update(result.keys())
        
        fieldnames = sorted(list(all_keys))
        
        # Format list fields
        for result in self.results:
            for key, value in result.items():
                if isinstance(value, list):
                    result[key] = '; '.join(str(v) for v in value) if value else ""
        
        # Always create new file with headers
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"\n[+] Results saved to: {filename}")
    
    def print_stats(self):
        """Print final statistics"""
        elapsed = self.stats['end_time'] - self.stats['start_time']
        total_success = self.stats['http_success'] + self.stats['browser_success']
        
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETE")
        print("=" * 60)
        print(f"Total URLs:        {self.stats['total']}")
        print(f"Successful:        {total_success}")
        print(f"  - HTTP (fast):   {self.stats['http_success']}")
        print(f"  - Browser:       {self.stats['browser_success']}")
        print(f"Skipped:           {self.stats['skipped']}")
        print(f"Failed:            {self.stats['failed']}")
        if self.stats['total'] > 0:
            print(f"Success Rate:      {(total_success/self.stats['total']*100):.1f}%")
        if elapsed > 0 and total_success > 0:
            print(f"Time Elapsed:      {elapsed:.2f} seconds")
            print(f"Average Speed:     {(total_success/elapsed):.2f} URLs/second")
        print("=" * 60)
        print()


async def main():
    parser = argparse.ArgumentParser(
        description="Ultimate Scraper - Fast HTTP + Accurate Browser Hybrid"
    )
    parser.add_argument('urls_file', nargs='?', help='Text file with URLs (one per line) - optional')
    parser.add_argument('--force-browser', action='store_true',
                       help='Always use browser (most accurate)')
    parser.add_argument('--output', type=str,
                       help='Output CSV filename')
    
    args = parser.parse_args()
    
    # Load URLs - either from file or user input
    if args.urls_file:
        # Load from file
        with open(args.urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        # Ask user for URLs
        print("=" * 60)
        print("ULTIMATE SCRAPER - Fast + Accurate")
        print("=" * 60)
        print()
        print("NOTE: Social media URLs (Facebook, Instagram, Twitter, etc.) are not supported.")
        print("      Please provide business website URLs only.")
        print()
        user_input = input("Enter website URL(s) to scrape (comma-separated for multiple): ").strip()
        
        if not user_input:
            print("[X] No URLs provided!")
            return
        
        # Split by comma and clean
        urls = [url.strip() for url in user_input.split(',') if url.strip()]
        
        if not urls:
            print("[X] No valid URLs provided!")
            return
        
        # Pre-validate URLs and warn user
        scraper_temp = UltimateScraper()
        invalid_urls = []
        for url in urls[:]:  # Copy list to modify during iteration
            is_valid, error_msg = scraper_temp.validate_url(url)
            if not is_valid:
                invalid_urls.append((url, error_msg))
        
        if invalid_urls:
            print("\n[!] WARNING: Some URLs are invalid:")
            for url, error in invalid_urls:
                print(f"    ✗ {url}")
                print(f"      Reason: {error}")
            print()
            proceed = input("Continue with remaining valid URLs? (y/n): ").strip().lower()
            if proceed != 'y':
                print("[X] Scraping cancelled.")
                return
    
    # Create scraper
    scraper = UltimateScraper(force_browser=args.force_browser)
    
    # Scrape
    await scraper.scrape_all(urls)
    
    # Save
    if args.output:
        csv_filename = args.output
    else:
        # Generate timestamped filename for each run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"ultimate_scrape_{timestamp}.csv"
    
    scraper.save_to_csv(csv_filename)
    scraper.print_stats()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    finally:
        import os
        os._exit(0)
