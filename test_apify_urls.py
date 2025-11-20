"""
Quick test of the URLs to see if scraper works locally
"""
from scraper import BrowserManager, extract_emails, extract_phones, extract_social_links

# Test one URL
url = "https://www.djangoproject.com/foundation/contact/"

print(f"Testing: {url}")
print("=" * 60)

browser = BrowserManager()
browser.launch_browser()

try:
    success = browser.load_page(url)
    print(f"Page loaded: {success}")
    
    if success:
        browser.scroll_to_bottom()
        
        emails = extract_emails(browser.page)
        phones = extract_phones(browser.page)
        socials = extract_social_links(browser.page)
        
        print(f"\nEmails found: {emails}")
        print(f"Phones found: {phones}")
        print(f"Socials found: {socials}")
        
        # Get page content to debug
        content = browser.page.content()
        print(f"\nPage content length: {len(content)} characters")
        print(f"Contains 'foundation@': {'foundation@' in content}")
        
finally:
    browser.close_browser()
