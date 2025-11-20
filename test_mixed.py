"""Test mixed URLs (valid + social media)"""
from ultimate_scraper_optimized import OptimizedScraper

# Create scraper
scraper = OptimizedScraper()

# Test URLs (mix of valid and social media)
test_urls = [
    'https://example.com',
    'https://facebook.com/page',
    'https://httpbin.org',
    'https://instagram.com/user',
    'https://wikipedia.org',
    'https://twitter.com/handle',
]

print("=" * 60)
print("TESTING MIXED URLs (Valid + Social Media)")
print("=" * 60)
print()

for url in test_urls:
    is_valid, error_msg = scraper.validate_url(url)
    
    if is_valid:
        print(f"✅ {url}")
        print(f"   → Will be scraped")
    else:
        print(f"❌ {url}")
        print(f"   → SKIPPED: {error_msg}")
    print()

print("=" * 60)
print("SUMMARY")
print("=" * 60)
valid_count = sum(1 for url in test_urls if scraper.validate_url(url)[0])
invalid_count = len(test_urls) - valid_count

print(f"Total URLs:     {len(test_urls)}")
print(f"Valid:          {valid_count} (will be scraped)")
print(f"Invalid:        {invalid_count} (will be skipped)")
print(f"Success Rate:   {(valid_count/len(test_urls)*100):.1f}%")
print("=" * 60)
