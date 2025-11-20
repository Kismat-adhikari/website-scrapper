"""
Website Scraper - Business and Contact Information Extractor

A Python-based web scraper that extracts comprehensive business and contact information
from websites using Playwright for browser automation. Supports proxy rotation and exports
data to CSV format for commercial lead generation.

INSTALLATION:
1. Install dependencies:
   pip install -r requirements.txt

2. Install Playwright browsers:
   playwright install chromium

3. (Optional) Create proxies.txt file with proxy configurations:
   Format options:
   - ip:port
   - ip:port:user:pass
   - http://ip:port
   - http://user:pass@ip:port

USAGE:
   python scraper.py

The script will prompt you for a website URL and begin scraping.
Results are saved to results.csv in the current directory.

Author: Generated via Kiro Spec-Driven Development
"""

import re
import csv
import time
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Union, Optional, Dict
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: Playwright not installed. Run: pip install playwright && playwright install chromium")
    exit(1)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ProxyConfig:
    """Configuration for proxy server connection"""
    server: str          # Format: http://ip:port
    username: Optional[str] = None  # Optional authentication
    password: Optional[str] = None  # Optional authentication


@dataclass
class ScrapedData:
    """Container for all extracted website data"""
    url: str
    title: str
    emails: Union[List[str], str]  # List or "NONE"
    phones: Union[List[str], str]  # List or "NONE"
    social_links: List[str]
    external_links: List[str]
    description: str
    meta_description: str
    og_title: str
    og_description: str
    og_image: str
    address: str  # Single address field (includes country if available)
    whatsapp: str
    telegram: str
    signal: str
    discord: str
    contact_form: bool
    industry: str
    blog_present: bool
    products_or_services: bool
    word_count: int
    scrape_timestamp: str
    # Metrics
    email_count: int
    phone_count: int
    social_count: int


# ============================================================================
# PROXY MANAGEMENT
# ============================================================================

# Global variables to track proxy rotation
_proxy_index = 0
_proxies_cache = []
_proxy_usage_count = 0  # Track how many times current proxy has been used
_max_uses_per_proxy = 7  # Rotate proxy after this many uses


def load_proxies(filename: str = "proxies.txt") -> List[ProxyConfig]:
    """
    Load and parse proxy configurations from a file.
    
    Supports four proxy formats:
    1. ip:port
    2. ip:port:user:pass
    3. http://ip:port
    4. http://user:pass@ip:port
    
    Args:
        filename: Path to the proxy configuration file
        
    Returns:
        List of ProxyConfig objects
        
    Note:
        Invalid proxy entries are skipped with a warning message.
        If file doesn't exist, returns empty list (proxy is optional).
    """
    global _proxies_cache
    
    proxy_path = Path(filename)
    if not proxy_path.exists():
        print(f"[!] No {filename} found. Continuing without proxy.")
        return []
    
    proxies = []
    with open(proxy_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                proxy_config = parse_proxy_line(line)
                if proxy_config:
                    proxies.append(proxy_config)
            except Exception as e:
                print(f"[!] Warning: Invalid proxy on line {line_num}: {line}")
                continue
    
    _proxies_cache = proxies
    print(f"[+] Loaded {len(proxies)} proxy configuration(s)")
    return proxies


def parse_proxy_line(line: str) -> Optional[ProxyConfig]:
    """
    Parse a single proxy line and detect its format.
    
    Detects and parses four formats:
    1. ip:port
    2. ip:port:user:pass
    3. http://ip:port
    4. http://user:pass@ip:port
    
    Args:
        line: A single proxy configuration string
        
    Returns:
        ProxyConfig object or None if parsing fails
    """
    line = line.strip()
    
    # Format 4: http://user:pass@ip:port
    if line.startswith('http://') and '@' in line:
        match = re.match(r'http://([^:]+):([^@]+)@([^:]+):(\d+)', line)
        if match:
            username, password, ip, port = match.groups()
            return ProxyConfig(
                server=f"http://{ip}:{port}",
                username=username,
                password=password
            )
    
    # Format 3: http://ip:port
    elif line.startswith('http://'):
        match = re.match(r'http://([^:]+):(\d+)', line)
        if match:
            ip, port = match.groups()
            return ProxyConfig(server=f"http://{ip}:{port}")
    
    # Format 2: ip:port:user:pass
    elif line.count(':') == 3:
        parts = line.split(':')
        if len(parts) == 4:
            ip, port, username, password = parts
            return ProxyConfig(
                server=f"http://{ip}:{port}",
                username=username,
                password=password
            )
    
    # Format 1: ip:port
    elif line.count(':') == 1:
        parts = line.split(':')
        if len(parts) == 2:
            ip, port = parts
            return ProxyConfig(server=f"http://{ip}:{port}")
    
    return None


def get_next_proxy(force_rotate: bool = False) -> Optional[ProxyConfig]:
    """
    Get the next proxy in rotation sequence.
    
    Rotates through all loaded proxies in order before repeating.
    Uses smart rotation: changes proxy after max uses or when forced.
    
    Args:
        force_rotate: Force rotation to next proxy regardless of usage count
    
    Returns:
        ProxyConfig object or None if no proxies available
    """
    global _proxy_index, _proxies_cache, _proxy_usage_count, _max_uses_per_proxy
    
    if not _proxies_cache:
        return None
    
    # Check if we should rotate to next proxy
    should_rotate = force_rotate or _proxy_usage_count >= _max_uses_per_proxy
    
    if should_rotate and len(_proxies_cache) > 1:
        # Move to next proxy
        _proxy_index = (_proxy_index + 1) % len(_proxies_cache)
        _proxy_usage_count = 0
        print(f"[*] Proxy rotated (used {_max_uses_per_proxy} times, switching for safety)")
    
    proxy = _proxies_cache[_proxy_index]
    _proxy_usage_count += 1
    
    return proxy


def reset_proxy_usage():
    """Reset proxy usage counter (useful when starting new session)"""
    global _proxy_usage_count
    _proxy_usage_count = 0


def format_proxy_for_playwright(proxy_config: Optional[ProxyConfig]) -> Optional[Dict]:
    """
    Convert ProxyConfig to Playwright-compatible proxy dictionary.
    
    Args:
        proxy_config: ProxyConfig object or None
        
    Returns:
        Dictionary with Playwright proxy configuration or None
    """
    if not proxy_config:
        return None
    
    proxy_dict = {"server": proxy_config.server}
    
    if proxy_config.username and proxy_config.password:
        proxy_dict["username"] = proxy_config.username
        proxy_dict["password"] = proxy_config.password
    
    return proxy_dict


# ============================================================================
# URL VALIDATION AND USER INPUT
# ============================================================================

def validate_url(url: str) -> bool:
    """
    Validate URL format using regex.
    
    Accepts URLs with:
    - http:// or https:// protocol
    - Valid domain name
    - Valid TLD (2+ characters)
    - Optional path, query, and fragment
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
        
    Examples:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("http://sub.example.com/path")
        True
        >>> validate_url("not-a-url")
        False
    """
    # URL validation regex pattern
    # Matches: http(s)://domain.tld with optional path/query/fragment
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',  # optional path
        re.IGNORECASE
    )
    
    return bool(url_pattern.match(url))


def get_user_input() -> str:
    """
    Prompt user for website URL and validate input.
    
    Displays prompt "Enter the website URL to scrape:" and validates
    the entered URL. Re-prompts on invalid input until valid URL received.
    
    Returns:
        Valid URL string
    """
    while True:
        url = input("Enter the website URL to scrape: ").strip()
        
        if validate_url(url):
            return url
        else:
            print("[X] Error: Invalid URL format. Please enter a valid URL (e.g., https://example.com)")
            print()


# ============================================================================
# BROWSER MANAGEMENT
# ============================================================================

class BrowserManager:
    """Manages Playwright browser lifecycle and page operations"""
    
    def __init__(self, proxy_config: Optional[ProxyConfig] = None):
        """
        Initialize browser manager.
        
        Args:
            proxy_config: Optional proxy configuration
        """
        self.proxy_config = proxy_config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    def launch_browser(self):
        """
        Launch Playwright browser in headless mode with configuration.
        
        Configures:
        - Headless mode (headless=True) for background operation
        - 30-second timeout
        - Proxy settings if provided
        """
        print("[*] Launching browser...")
        
        self.playwright = sync_playwright().start()
        
        # Prepare browser launch arguments
        launch_args = {
            'headless': True,  # Headless mode - no visible browser
            'timeout': 30000,   # 30 second timeout
        }
        
        # Add proxy if configured
        proxy_dict = format_proxy_for_playwright(self.proxy_config)
        if proxy_dict:
            launch_args['proxy'] = proxy_dict
            print(f"   Using proxy: {proxy_dict['server']}")
        
        # Launch browser
        self.browser = self.playwright.chromium.launch(**launch_args)
        
        # Create new page with timeout
        self.page = self.browser.new_page()
        self.page.set_default_timeout(30000)  # 30 second timeout for all operations
        
        print("[+] Browser launched successfully")
        
    def handle_popups(self):
        """
        Automatically handle common popups, modals, and overlays.
        
        Handles:
        - Cookie notices
        - Age verification
        - Newsletter popups
        - Payment info modals
        - General "OK" / "Accept" / "Close" buttons
        """
        try:
            # Common selectors for popup close buttons
            close_selectors = [
                # Generic close buttons
                'button:has-text("OK")',
                'button:has-text("Accept")',
                'button:has-text("Close")',
                'button:has-text("Got it")',
                'button:has-text("I agree")',
                'button:has-text("Continue")',
                'button:has-text("Dismiss")',
                '[aria-label="Close"]',
                '[aria-label="Dismiss"]',
                '.close-button',
                '.modal-close',
                '.popup-close',
                # Cookie notices
                'button:has-text("Accept all")',
                'button:has-text("Accept cookies")',
                'button:has-text("Allow all")',
                '#accept-cookies',
                '.cookie-accept',
                // Age verification
                'button:has-text("Yes")',
                'button:has-text("I am 18+")',
                'button:has-text("Enter")',
                // X buttons
                'button.close',
                'button[aria-label*="close" i]',
                '[class*="close-icon"]',
                '[class*="modal-close"]',
            ]
            
            clicked_count = 0
            for selector in close_selectors:
                try:
                    # Check if element exists and is visible
                    if self.page.locator(selector).first.is_visible(timeout=1000):
                        self.page.locator(selector).first.click(timeout=2000)
                        clicked_count += 1
                        time.sleep(0.5)  # Wait for animation
                except:
                    continue  # Element not found or not clickable
            
            if clicked_count > 0:
                print(f"[+] Closed {clicked_count} popup(s)")
            
            # Also try pressing Escape key (works for many modals)
            try:
                self.page.keyboard.press('Escape')
                time.sleep(0.3)
            except:
                pass
                
        except Exception as e:
            # Silently fail - popup handling is optional
            pass
    
    def load_page(self, url: str, max_retries: int = 3) -> bool:
        """
        Load page with retry logic and wait for network idle.
        
        Args:
            url: URL to load
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if page loaded successfully, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[*] Loading page (attempt {attempt}/{max_retries})...")
                
                # Navigate to URL and wait for network idle
                self.page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Handle popups immediately after page load
                print("[*] Checking for popups...")
                self.handle_popups()
                
                print("[+] Page loaded successfully")
                return True
                
            except PlaywrightTimeout:
                print(f"[!] Timeout on attempt {attempt}")
                if attempt < max_retries:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("[X] Failed to load page after all retries")
                    return False
                    
            except Exception as e:
                print(f"[!] Error on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("[X] Failed to load page after all retries")
                    return False
        
        return False
    
    def scroll_to_bottom(self):
        """
        Smoothly scroll to bottom of page to trigger lazy-loaded content.
        
        Uses incremental scrolling with delays to ensure dynamic content loads.
        """
        print("[*] Scrolling page to load dynamic content...")
        
        try:
            # Get page height
            page_height = self.page.evaluate("document.body.scrollHeight")
            viewport_height = self.page.evaluate("window.innerHeight")
            
            # Scroll incrementally
            current_position = 0
            scroll_increment = viewport_height // 2  # Scroll half viewport at a time
            
            while current_position < page_height:
                current_position += scroll_increment
                self.page.evaluate(f"window.scrollTo(0, {current_position})")
                time.sleep(0.15)  # 150ms delay between scrolls
                
                # Update page height in case new content loaded
                page_height = self.page.evaluate("document.body.scrollHeight")
            
            # Scroll back to top for better extraction
            self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)  # Wait for any final content to settle
            
            # Handle any popups that appeared during scrolling
            self.handle_popups()
            
            print("[+] Scrolling complete")
            
        except Exception as e:
            print(f"[!] Scrolling error: {str(e)}")
            # Continue anyway - not critical
    
    def close_browser(self):
        """
        Close browser and cleanup resources.
        
        Ensures cleanup happens even on errors.
        """
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("[+] Browser closed")
        except Exception as e:
            print(f"[!] Error closing browser: {str(e)}")


# ============================================================================
# DATA EXTRACTION
# ============================================================================

def extract_url(page: Page) -> str:
    """Extract the current page URL"""
    return page.url


def extract_title(page: Page) -> str:
    """Extract page title"""
    try:
        return page.title() or ""
    except:
        return ""


def extract_metadata(page: Page) -> Dict[str, str]:
    """
    Extract comprehensive metadata including OpenGraph and JSON-LD.
    
    Returns:
        Dictionary with meta_description, og_data, and json_ld
    """
    try:
        metadata = {
            'meta_description': '',
            'og_title': '',
            'og_description': '',
            'og_image': '',
            'og_type': '',
            'json_ld': {}
        }
        
        # Standard meta description
        try:
            meta_desc = page.locator('meta[name="description"]').get_attribute('content')
            metadata['meta_description'] = meta_desc or ""
        except:
            pass
        
        # OpenGraph data
        try:
            og_title = page.locator('meta[property="og:title"]').get_attribute('content')
            metadata['og_title'] = og_title or ""
        except:
            pass
        
        try:
            og_desc = page.locator('meta[property="og:description"]').get_attribute('content')
            metadata['og_description'] = og_desc or ""
        except:
            pass
        
        try:
            og_image = page.locator('meta[property="og:image"]').get_attribute('content')
            metadata['og_image'] = og_image or ""
        except:
            pass
        
        try:
            og_type = page.locator('meta[property="og:type"]').get_attribute('content')
            metadata['og_type'] = og_type or ""
        except:
            pass
        
        # JSON-LD structured data
        try:
            import json
            json_ld_scripts = page.locator('script[type="application/ld+json"]').all()
            if json_ld_scripts:
                json_ld_text = json_ld_scripts[0].inner_text()
                metadata['json_ld'] = json.loads(json_ld_text)
        except:
            pass
        
        return metadata
    except:
        return {'meta_description': '', 'og_title': '', 'og_description': '', 'og_image': '', 'og_type': '', 'json_ld': {}}


def generate_timestamp() -> str:
    """Generate ISO 8601 formatted timestamp"""
    return datetime.now().isoformat()


def extract_emails(page: Page) -> Union[List[str], str]:
    """
    Extract all email addresses from page including obfuscated formats.
    
    Handles:
    - Standard: user@example.com
    - Obfuscated: user [at] example.com, user(at)example.com
    - Dot obfuscated: user [dot] example [dot] com
    
    Returns:
        List of unique validated emails or "NONE" if no emails found
    """
    try:
        # Get all text content from page
        content = page.content()
        emails = []
        
        # Pattern 1: Standard email format
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails.extend(re.findall(email_pattern, content))
        
        # Pattern 2: Obfuscated with [at], (at), or " at "
        obfuscated_at = r'([a-zA-Z0-9._%+-]+)\s*[\[\(]?\s*at\s*[\]\)]?\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        for match in re.finditer(obfuscated_at, content, re.IGNORECASE):
            email = f"{match.group(1)}@{match.group(2)}"
            emails.append(email)
        
        # Pattern 3: Obfuscated with [dot] or (dot)
        obfuscated_dot = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+)\s*[\[\(]?\s*dot\s*[\]\)]?\s*([a-zA-Z]{2,})'
        for match in re.finditer(obfuscated_dot, content, re.IGNORECASE):
            email = f"{match.group(1)}.{match.group(2)}"
            emails.append(email)
        
        # Validate and clean emails
        validated_emails = []
        for email in emails:
            email = email.lower().strip()
            # Basic validation: has @ and domain
            if '@' in email and '.' in email.split('@')[1]:
                # Remove common false positives
                if not any(bad in email for bad in ['.png', '.jpg', '.gif', '.css', '.js']):
                    validated_emails.append(email)
        
        # Remove duplicates and return
        unique_emails = list(dict.fromkeys(validated_emails))  # Preserve order
        return unique_emails if unique_emails else "NONE"
    except:
        return "NONE"


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to standard format.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Normalized phone in format: +1-XXX-XXX-XXXX or original if can't normalize
    """
    # Remove all non-digit characters except +
    digits = re.sub(r'[^\d+]', '', phone)
    
    # Handle US numbers (10 digits)
    if len(digits) == 10:
        return f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    
    # Handle US numbers with country code (11 digits starting with 1)
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    
    # Handle international with + prefix
    elif digits.startswith('+'):
        return digits
    
    # Return original if can't normalize
    return phone


def extract_phones(page: Page) -> Union[List[str], str]:
    """
    Extract and normalize phone numbers in various formats.
    
    Supports formats:
    - US: (123) 456-7890, 123-456-7890, 123.456.7890
    - International: +1 123 456 7890, +44 20 1234 5678
    - Extensions: 123-456-7890 ext. 123
    
    Returns:
        List of unique normalized phone numbers or "NONE" if none found
    """
    try:
        content = page.content()
        phones = []
        
        # Pattern 1: International format with country code
        intl_pattern = r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        phones.extend(re.findall(intl_pattern, content))
        
        # Pattern 2: US format with parentheses
        us_pattern1 = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones.extend(re.findall(us_pattern1, content))
        
        # Pattern 3: Simple 10-digit numbers
        simple_pattern = r'\b\d{10}\b'
        phones.extend(re.findall(simple_pattern, content))
        
        # Validate and normalize
        validated_phones = []
        for phone in phones:
            # Skip if too short or looks like a date/year
            if len(re.sub(r'\D', '', phone)) < 10:
                continue
            if re.match(r'^(19|20)\d{2}', phone):  # Skip years
                continue
                
            # Normalize and add
            normalized = normalize_phone(phone)
            validated_phones.append(normalized)
        
        # Remove duplicates
        unique_phones = list(dict.fromkeys(validated_phones))
        return unique_phones if unique_phones else "NONE"
    except:
        return "NONE"


def extract_address(page: Page) -> Dict[str, str]:
    """
    Extract detailed address information with components.
    
    Returns:
        Dictionary with street, city, state, zip, country
    """
    try:
        content = page.content()
        address_data = {
            'street': '',
            'city': '',
            'state': '',
            'zip': '',
            'country': '',
            'full': ''
        }
        
        # Pattern 1: Full US address
        us_pattern = r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way))[,\s]+([A-Za-z\s]+)[,\s]+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
        match = re.search(us_pattern, content)
        if match:
            address_data['street'] = match.group(1).strip()
            address_data['city'] = match.group(2).strip()
            address_data['state'] = match.group(3).strip()
            address_data['zip'] = match.group(4).strip()
            address_data['country'] = 'USA'
            address_data['full'] = f"{address_data['street']}, {address_data['city']}, {address_data['state']} {address_data['zip']}"
            return address_data
        
        # Pattern 2: Schema.org markup
        try:
            street = page.locator('[itemprop="streetAddress"]').first.inner_text() if page.locator('[itemprop="streetAddress"]').count() > 0 else ''
            city = page.locator('[itemprop="addressLocality"]').first.inner_text() if page.locator('[itemprop="addressLocality"]').count() > 0 else ''
            state = page.locator('[itemprop="addressRegion"]').first.inner_text() if page.locator('[itemprop="addressRegion"]').count() > 0 else ''
            zip_code = page.locator('[itemprop="postalCode"]').first.inner_text() if page.locator('[itemprop="postalCode"]').count() > 0 else ''
            country = page.locator('[itemprop="addressCountry"]').first.inner_text() if page.locator('[itemprop="addressCountry"]').count() > 0 else ''
            
            if any([street, city, state, zip_code]):
                address_data['street'] = street
                address_data['city'] = city
                address_data['state'] = state
                address_data['zip'] = zip_code
                address_data['country'] = country
                address_data['full'] = ', '.join(filter(None, [street, city, state, zip_code, country]))
                return address_data
        except:
            pass
        
        return address_data
    except:
        return {'street': '', 'city': '', 'state': '', 'zip': '', 'country': '', 'full': ''}


def extract_social_links(page: Page) -> List[str]:
    """
    Extract social media links for specified platforms.
    
    Platforms: Facebook, Instagram, Twitter, TikTok, LinkedIn, 
               YouTube, Pinterest, Snapchat
    """
    try:
        content = page.content()
        
        social_domains = [
            'facebook.com',
            'instagram.com',
            'twitter.com',
            'x.com',  # Twitter/X
            'tiktok.com',
            'linkedin.com',
            'youtube.com',
            'pinterest.com',
            'snapchat.com',
        ]
        
        social_links = []
        for domain in social_domains:
            # Find links containing the social domain
            pattern = rf'https?://(?:www\.)?{re.escape(domain)}/[^\s"\'>]+'
            matches = re.findall(pattern, content)
            social_links.extend(matches)
        
        return list(set(social_links))
    except:
        return []


def extract_external_links(page: Page) -> List[str]:
    """
    Extract all external links (excluding internal navigation).
    
    External links are those pointing to different domains.
    """
    try:
        current_domain = re.search(r'https?://([^/]+)', page.url).group(1)
        
        # Get all links
        all_links = page.locator('a[href]').all()
        external_links = []
        
        for link in all_links:
            href = link.get_attribute('href')
            if href and href.startswith('http'):
                link_domain = re.search(r'https?://([^/]+)', href)
                if link_domain and link_domain.group(1) != current_domain:
                    external_links.append(href)
        
        return list(set(external_links))
    except:
        return []


def extract_descriptions(page: Page) -> str:
    """
    Extract visible description text from page body.
    
    Looks for common description patterns and about sections.
    """
    try:
        # Try to find description in common locations
        selectors = [
            '.description',
            '#description',
            '.about',
            '#about',
            '[class*="description"]',
            '[class*="about"]',
            'p',  # Fallback to first few paragraphs
        ]
        
        for selector in selectors:
            elements = page.locator(selector).all()
            if elements:
                texts = [el.inner_text() for el in elements[:3]]  # Get first 3 matches
                combined = ' '.join(texts).strip()
                if len(combined) > 50:  # Only return if substantial
                    return combined[:500]  # Limit to 500 chars
        
        return ""
    except:
        return ""


def extract_messaging_links(page: Page) -> Dict[str, str]:
    """
    Extract messaging app links (WhatsApp, Telegram, Signal, Discord).
    
    Returns:
        Dictionary with messaging platform links
    """
    try:
        content = page.content()
        messaging = {
            'whatsapp': '',
            'telegram': '',
            'signal': '',
            'discord': ''
        }
        
        # WhatsApp patterns
        whatsapp_pattern = r'https?://(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com)/[^\s"\'>]+'
        whatsapp_matches = re.findall(whatsapp_pattern, content)
        messaging['whatsapp'] = whatsapp_matches[0] if whatsapp_matches else ""
        
        # Telegram patterns
        telegram_pattern = r'https?://(?:t\.me|telegram\.me|telegram\.org)/[^\s"\'>]+'
        telegram_matches = re.findall(telegram_pattern, content)
        messaging['telegram'] = telegram_matches[0] if telegram_matches else ""
        
        # Signal patterns
        signal_pattern = r'https?://signal\.(?:group|me)/[^\s"\'>]+'
        signal_matches = re.findall(signal_pattern, content)
        messaging['signal'] = signal_matches[0] if signal_matches else ""
        
        # Discord patterns
        discord_pattern = r'https?://(?:discord\.gg|discord\.com/invite)/[^\s"\'>]+'
        discord_matches = re.findall(discord_pattern, content)
        messaging['discord'] = discord_matches[0] if discord_matches else ""
        
        return messaging
    except:
        return {'whatsapp': '', 'telegram': '', 'signal': '', 'discord': ''}


# ============================================================================
# BUSINESS INTELLIGENCE INFERENCE
# ============================================================================

def infer_industry(page: Page) -> str:
    """
    Infer industry/category using keyword analysis.
    
    Analyzes page content for industry-specific keywords.
    """
    try:
        content = page.content().lower()
        
        # Industry keyword mappings
        industries = {
            'Technology': ['software', 'tech', 'app', 'digital', 'cloud', 'saas', 'api', 'developer'],
            'E-commerce': ['shop', 'store', 'buy', 'cart', 'checkout', 'product', 'price', 'shipping'],
            'Healthcare': ['health', 'medical', 'doctor', 'clinic', 'hospital', 'patient', 'care', 'wellness'],
            'Finance': ['bank', 'finance', 'investment', 'loan', 'credit', 'insurance', 'trading'],
            'Education': ['education', 'school', 'university', 'course', 'learning', 'student', 'teacher'],
            'Real Estate': ['property', 'real estate', 'house', 'apartment', 'rent', 'buy', 'listing'],
            'Food & Restaurant': ['restaurant', 'food', 'menu', 'dining', 'cafe', 'delivery', 'cuisine'],
            'Marketing': ['marketing', 'advertising', 'seo', 'social media', 'branding', 'campaign'],
            'Legal': ['law', 'legal', 'attorney', 'lawyer', 'court', 'litigation'],
            'Consulting': ['consulting', 'consultant', 'advisory', 'strategy', 'business'],
        }
        
        # Count keyword matches for each industry
        scores = {}
        for industry, keywords in industries.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                scores[industry] = score
        
        # Return industry with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return "General"
    except:
        return "Unknown"


def detect_contact_form(page: Page) -> bool:
    """
    Detect presence of contact forms.
    
    Checks for form elements on the page.
    """
    try:
        # Look for forms
        forms = page.locator('form').count()
        if forms > 0:
            return True
        
        # Look for common contact form indicators
        contact_indicators = [
            'input[type="email"]',
            'textarea',
            'input[name*="message"]',
            'input[name*="contact"]',
        ]
        
        for indicator in contact_indicators:
            if page.locator(indicator).count() > 0:
                return True
        
        return False
    except:
        return False


def calculate_word_count(page: Page) -> int:
    """
    Calculate estimated word count of visible content.
    
    Counts words in the visible text of the page body.
    """
    try:
        # Get visible text from body
        body_text = page.locator('body').inner_text()
        
        # Split by whitespace and count
        words = body_text.split()
        return len(words)
    except:
        return 0


def detect_blog(page: Page) -> bool:
    """
    Detect if blog section exists.
    
    Looks for blog indicators in URLs, links, and content.
    """
    try:
        content = page.content().lower()
        url = page.url.lower()
        
        # Check URL for blog indicators
        if 'blog' in url or 'news' in url or 'article' in url:
            return True
        
        # Check for blog-related links
        blog_links = page.locator('a[href*="blog"], a[href*="news"], a[href*="article"]').count()
        if blog_links > 0:
            return True
        
        # Check content for blog indicators
        blog_keywords = ['blog', 'article', 'post', 'news']
        if any(keyword in content for keyword in blog_keywords):
            return True
        
        return False
    except:
        return False


def detect_products_services(page: Page) -> bool:
    """
    Detect if products or services are mentioned.
    
    Looks for product/service keywords in content.
    """
    try:
        content = page.content().lower()
        
        # Product/service keywords
        keywords = [
            'product', 'service', 'offer', 'solution', 'package',
            'pricing', 'price', 'buy', 'purchase', 'order',
            'features', 'plans', 'subscription'
        ]
        
        # Check if any keywords present
        return any(keyword in content for keyword in keywords)
    except:
        return False


# ============================================================================
# DATA CLEANING AND NORMALIZATION
# ============================================================================

def clean_text(text: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    Strip whitespace and remove duplicate entries.
    
    Args:
        text: String or list of strings to clean
        
    Returns:
        Cleaned string or list with duplicates removed
    """
    if isinstance(text, list):
        # Clean each item and remove duplicates
        cleaned = [item.strip() for item in text if item and item.strip()]
        return list(dict.fromkeys(cleaned))  # Preserve order while removing duplicates
    elif isinstance(text, str):
        return text.strip()
    return text


def normalize_data(data: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    Normalize emails and links for consistent formatting.
    
    - Lowercase domains
    - Trim whitespace
    - Remove duplicates
    
    Args:
        data: String or list of strings to normalize
        
    Returns:
        Normalized data
    """
    if isinstance(data, list):
        normalized = []
        for item in data:
            item = item.strip().lower()
            if item and item not in normalized:
                normalized.append(item)
        return normalized
    elif isinstance(data, str):
        return data.strip().lower()
    return data


def apply_defaults(emails: Union[List[str], str], phones: Union[List[str], str]) -> tuple:
    """
    Apply "NONE" default for missing emails and phones.
    
    Args:
        emails: Email list or string
        phones: Phone list or string
        
    Returns:
        Tuple of (emails, phones) with defaults applied
    """
    if not emails or (isinstance(emails, list) and len(emails) == 0):
        emails = "NONE"
    if not phones or (isinstance(phones, list) and len(phones) == 0):
        phones = "NONE"
    
    return emails, phones


# ============================================================================
# CSV EXPORT
# ============================================================================

def format_list_field(items: Union[List[str], str]) -> str:
    """
    Convert lists to semicolon-delimited strings for CSV.
    
    Args:
        items: List of strings or single string
        
    Returns:
        Semicolon-delimited string or original string
    """
    if isinstance(items, list):
        return '; '.join(items)
    return items


def generate_csv_filename() -> str:
    """
    Generate a unique CSV filename with timestamp.
    
    Returns:
        Filename in format: scrape_YYYYMMDD_HHMMSS.csv
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"scrape_{timestamp}.csv"


def save_to_csv(data: ScrapedData, filename: str = None):
    """
    Save extracted data to CSV file.
    
    Creates file with headers if it doesn't exist, otherwise appends.
    Properly escapes special characters and handles multi-value fields.
    
    Args:
        data: ScrapedData object to save
        filename: Output CSV filename (if None, generates timestamped filename)
    """
    try:
        if filename is None:
            filename = generate_csv_filename()
        
        print(f"[*] Saving data to {filename}...")
        
        # Define column order with all new fields
        fieldnames = [
            'url', 'title', 'emails', 'phones', 'social_links', 'external_links',
            'description', 'meta_description', 'og_title', 'og_description', 'og_image',
            'address',  # Simplified: single address field
            'whatsapp', 'telegram', 'signal', 'discord',
            'contact_form', 'industry', 'blog_present', 'products_or_services',
            'word_count', 'scrape_timestamp',
            'email_count', 'phone_count', 'social_count'
        ]
        
        # Check if file exists
        file_exists = Path(filename).exists()
        
        # Open file in append mode
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if new file
            if not file_exists:
                writer.writeheader()
            
            # Convert data to dict and format list fields
            row = asdict(data)
            row['emails'] = format_list_field(row['emails'])
            row['phones'] = format_list_field(row['phones'])
            row['social_links'] = format_list_field(row['social_links'])
            row['external_links'] = format_list_field(row['external_links'])
            
            # Write row
            writer.writerow(row)
        
        print(f"[+] Data saved successfully to {filename}")
        return filename
        
    except Exception as e:
        print(f"[X] Error saving to CSV: {str(e)}")
        return None


# ============================================================================
# URL VALIDATION AND USER INPUT
# ============================================================================

def validate_url(url: str) -> bool:
    """
    Validate URL format using regex.
    
    Accepts URLs with http:// or https:// protocol, valid domain, and TLD.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
        
    Examples:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("not-a-url")
        False
    """
    # URL regex pattern: protocol + domain + optional path
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',  # optional path
        re.IGNORECASE
    )
    
    return bool(url_pattern.match(url.strip()))


def get_user_input() -> List[str]:
    """
    Prompt user for website URL(s) and validate input.
    
    Displays prompt "Enter the website URL(s) to scrape:" and validates URLs.
    Supports multiple URLs separated by commas.
    Re-prompts on invalid input until valid URL(s) are provided.
    
    Returns:
        List of valid URL strings
    """
    while True:
        user_input = input("Enter the website URL(s) to scrape (comma-separated for multiple): ").strip()
        
        # Split by comma and clean up
        urls = [url.strip() for url in user_input.split(',') if url.strip()]
        
        if not urls:
            print("[X] No URLs provided. Please enter at least one URL.")
            print()
            continue
        
        # Validate all URLs
        invalid_urls = [url for url in urls if not validate_url(url)]
        
        if invalid_urls:
            print(f"[X] Invalid URL format(s): {', '.join(invalid_urls)}")
            print("    Please enter valid URLs (e.g., https://example.com)")
            print()
        else:
            return urls


# ============================================================================
# TERMINAL OUTPUT AND DISPLAY
# ============================================================================

def display_summary(data: ScrapedData):
    """
    Display a formatted summary of extracted data in the terminal.
    
    Shows each data category with found values or "None detected".
    
    Args:
        data: ScrapedData object to display
    """
    print()
    print("=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print()
    
    # Helper function to format display
    def format_value(value):
        if value == "NONE" or not value or (isinstance(value, list) and len(value) == 0):
            return "None detected"
        elif isinstance(value, list):
            return f"{len(value)} found: {', '.join(value[:3])}{'...' if len(value) > 3 else ''}"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, int):
            return str(value)
        else:
            # Truncate long strings
            return value[:100] + "..." if len(str(value)) > 100 else str(value)
    
    # Display each field
    print(f"URL:              {data.url}")
    print(f"Title:            {format_value(data.title)}")
    print()
    print("CONTACT INFORMATION:")
    print(f"  Emails:         {format_value(data.emails)} ({data.email_count} found)")
    print(f"  Phones:         {format_value(data.phones)} ({data.phone_count} found)")
    print(f"  Address:        {format_value(data.address)}")
    print()
    print("MESSAGING APPS:")
    print(f"  WhatsApp:       {format_value(data.whatsapp)}")
    print(f"  Telegram:       {format_value(data.telegram)}")
    print(f"  Signal:         {format_value(data.signal)}")
    print(f"  Discord:        {format_value(data.discord)}")
    print()
    print("SOCIAL MEDIA:")
    print(f"  Links:          {format_value(data.social_links)} ({data.social_count} found)")
    print()
    print("WEBSITE DATA:")
    print(f"  Description:    {format_value(data.description)}")
    print(f"  Meta Desc:      {format_value(data.meta_description)}")
    print(f"  OG Title:       {format_value(data.og_title)}")
    print(f"  External Links: {format_value(data.external_links)}")
    print(f"  Word Count:     {format_value(data.word_count)}")
    print()
    print("BUSINESS INTELLIGENCE:")
    print(f"  Industry:       {format_value(data.industry)}")
    print(f"  Contact Form:   {format_value(data.contact_form)}")
    print(f"  Blog Present:   {format_value(data.blog_present)}")
    print(f"  Products/Svcs:  {format_value(data.products_or_services)}")
    print()
    print(f"Timestamp:        {data.scrape_timestamp}")
    print()
    print("=" * 60)


def display_error(message: str):
    """
    Display a user-friendly error message without stack traces.
    
    Args:
        message: Error message to display
    """
    print()
    print("[X] ERROR")
    print("-" * 60)
    print(message)
    print("-" * 60)
    print()


def display_success():
    """Display a clean success message"""
    print()
    print("=" * 60)
    print("[+] SCRAPING COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def scrape_single_url(url: str, browser_manager: BrowserManager, csv_filename: str, add_delay: bool = False) -> Optional[ScrapedData]:
    """
    Scrape a single URL and return the data.
    
    Args:
        url: URL to scrape
        browser_manager: BrowserManager instance
        csv_filename: CSV file to save results to
        add_delay: Whether to add random delay before scraping (for anti-detection)
        
    Returns:
        ScrapedData object or None if failed
    """
    try:
        print()
        print("-" * 60)
        print(f"[*] Processing: {url}")
        print("-" * 60)
        
        # Add random delay for anti-detection (human-like behavior)
        if add_delay:
            import random
            delay = random.uniform(2, 5)  # Random delay between 2-5 seconds
            print(f"[*] Waiting {delay:.1f}s (anti-detection)...")
            time.sleep(delay)
        
        # Load page
        print("[*] Loading page...")
        if not browser_manager.load_page(url):
            print(f"[X] Failed to load {url}")
            return None
        
        # Scroll page
        print("[*] Scrolling to load dynamic content...")
        browser_manager.scroll_to_bottom()
        
        # Extract data
        print("[*] Extracting data...")
        page = browser_manager.page
        
        # Extract all data fields
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
        
        # Business intelligence
        industry = infer_industry(page)
        contact_form = detect_contact_form(page)
        word_count = calculate_word_count(page)
        blog_present = detect_blog(page)
        products_or_services = detect_products_services(page)
        
        # Timestamp
        timestamp = generate_timestamp()
        
        print("[+] Data extraction complete")
        
        # Clean and normalize data
        print("[*] Cleaning and normalizing data...")
        emails = clean_text(normalize_data(emails))
        phones = clean_text(phones)
        social_links = clean_text(normalize_data(social_links))
        external_links = clean_text(normalize_data(external_links))
        
        # Apply defaults
        emails, phones = apply_defaults(emails, phones)
        
        # Calculate metrics
        email_count = len(emails) if isinstance(emails, list) else 0
        phone_count = len(phones) if isinstance(phones, list) else 0
        social_count = len(social_links) if isinstance(social_links, list) else 0
        
        print("[+] Data cleaned")
        print(f"[*] Metrics: {email_count} emails, {phone_count} phones, {social_count} social links")
        
        # Create ScrapedData object
        # Format address: use full address with country if available
        address_str = address_data.get('full', '')
        if not address_str and address_data.get('country'):
            # If no full address but have country, just use country
            address_str = address_data.get('country', '')
        
        scraped_data = ScrapedData(
            url=extracted_url,
            title=title,
            emails=emails,
            phones=phones,
            social_links=social_links,
            external_links=external_links,
            description=description,
            meta_description=metadata.get('meta_description', ''),
            og_title=metadata.get('og_title', ''),
            og_description=metadata.get('og_description', ''),
            og_image=metadata.get('og_image', ''),
            address=address_str,  # Single address field
            whatsapp=messaging.get('whatsapp', ''),
            telegram=messaging.get('telegram', ''),
            signal=messaging.get('signal', ''),
            discord=messaging.get('discord', ''),
            contact_form=contact_form,
            industry=industry,
            blog_present=blog_present,
            products_or_services=products_or_services,
            word_count=word_count,
            scrape_timestamp=timestamp,
            email_count=email_count,
            phone_count=phone_count,
            social_count=social_count
        )
        
        # Save to CSV
        print("[*] Saving to CSV...")
        save_to_csv(scraped_data, csv_filename)
        
        # Display summary
        display_summary(scraped_data)
        
        return scraped_data
        
    except Exception as e:
        print(f"[X] Error scraping {url}: {str(e)}")
        return None


def main():
    """
    Main orchestration function for the web scraping workflow.
    Coordinates: input → proxy → browser → extract → clean → export → display
    """
    print("=" * 60)
    print("Website Scraper - Business Intelligence Extractor")
    print("=" * 60)
    print()
    
    browser_manager = None
    
    try:
        # Step 1: Load proxies (optional)
        print("[*] Step 1: Loading proxy configuration...")
        proxies = load_proxies()
        reset_proxy_usage()  # Reset usage counter for new session
        print()
        
        # Step 2: Get user input (can be multiple URLs)
        print("[*] Step 2: Getting target URL(s)...")
        urls = get_user_input()
        print(f"[+] {len(urls)} URL(s) to scrape:")
        for i, url in enumerate(urls, 1):
            print(f"    {i}. {url}")
        print()
        
        # Generate CSV filename with timestamp
        csv_filename = generate_csv_filename()
        print(f"[+] Results will be saved to: {csv_filename}")
        print()
        
        # Step 3: Launch browser with first proxy
        print("[*] Step 3: Launching browser...")
        proxy_config = get_next_proxy() if proxies else None
        browser_manager = BrowserManager(proxy_config)
        browser_manager.launch_browser()
        print()
        
        # Step 4: Process each URL with smart proxy rotation
        print("[*] Step 4: Processing URLs...")
        if proxies:
            print(f"[*] Smart proxy rotation: Changes proxy every {_max_uses_per_proxy} uses")
            print(f"[*] Total proxies available: {len(proxies)}")
        print()
        
        successful = 0
        failed = 0
        
        for idx, url in enumerate(urls):
            # Add delay after first URL (human-like behavior)
            add_delay = idx > 0
            
            # Check if we need to rotate proxy (every 7 uses)
            if proxies and _proxy_usage_count >= _max_uses_per_proxy:
                old_proxy = proxy_config.server if proxy_config else "None"
                
                # Close current browser
                browser_manager.close_browser()
                
                # Get next proxy (will auto-rotate due to usage count)
                proxy_config = get_next_proxy()
                new_proxy = proxy_config.server if proxy_config else "None"
                
                print()
                print(f"[*] PROXY ROTATION: {old_proxy} -> {new_proxy}")
                print(f"[*] Reason: Used {_max_uses_per_proxy} times (anti-detection)")
                print()
                
                # Brief pause between browser sessions (human-like)
                time.sleep(2)
                
                # Relaunch browser with new proxy
                browser_manager = BrowserManager(proxy_config)
                browser_manager.launch_browser()
            
            result = scrape_single_url(url, browser_manager, csv_filename, add_delay)
            if result:
                successful += 1
            else:
                failed += 1
        
        # Final summary
        print()
        print("=" * 60)
        print("SCRAPING SESSION COMPLETE")
        print("=" * 60)
        print(f"Total URLs processed: {len(urls)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Results saved to: {csv_filename}")
        print("=" * 60)
        print()
        
    except KeyboardInterrupt:
        print("\n\n[!] Scraping interrupted by user")
        
    except Exception as e:
        display_error(f"An unexpected error occurred: {str(e)}")
        
    finally:
        # Always cleanup browser
        if browser_manager:
            print("[*] Cleaning up...")
            browser_manager.close_browser()
            print()


if __name__ == "__main__":
    main()
