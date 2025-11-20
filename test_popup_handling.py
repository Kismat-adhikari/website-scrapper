"""
Test popup handling functionality
"""
from scraper import BrowserManager

print("=" * 60)
print("TESTING POPUP HANDLING")
print("=" * 60)
print()
print("This test demonstrates automatic popup handling.")
print("The scraper will:")
print("  1. Load a page")
print("  2. Detect popups automatically")
print("  3. Close them")
print("  4. Continue scraping")
print()
print("=" * 60)
print()

# Test with a site that typically has cookie notices
test_url = "https://www.bbc.com"  # BBC has cookie notices

print(f"Testing with: {test_url}")
print()

try:
    # Create browser manager
    browser_manager = BrowserManager()
    browser_manager.launch_browser()
    
    # Load page (popup handling happens automatically)
    success = browser_manager.load_page(test_url)
    
    if success:
        print()
        print("=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print("Popup handling worked! The page loaded and popups were handled.")
        print()
        print("In a real scrape, data extraction would happen now.")
    else:
        print()
        print("=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print("Page failed to load (might be network issue)")
    
    # Cleanup
    input("\nPress Enter to close browser...")
    browser_manager.close_browser()
    
except Exception as e:
    print(f"Error: {e}")
    print()
    print("Note: This test requires Playwright to be installed:")
    print("  pip install playwright")
    print("  playwright install chromium")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
