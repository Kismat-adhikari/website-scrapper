"""
Speed Test - Run scraper locally with timing
Tests the optimized scraper with 110 URLs
"""

import asyncio
import json
import csv
import time
from datetime import datetime
from apify_scraper_async import AsyncWebsiteScraper

# Extract URLs from test_urls.txt
def load_urls():
    with open('test_urls.txt', 'r') as f:
        content = f.read()
        # Parse the JSON-like structure
        urls = []
        for line in content.split('\n'):
            if '"url":' in line:
                url = line.split('"url":')[1].strip().strip('"').strip(',').strip()
                if url:
                    urls.append(url)
        return urls

async def scrape_with_semaphore(url, scraper, semaphore, results, index, total):
    """Scrape a single URL with semaphore control"""
    async with semaphore:
        print(f"[{index}/{total}] Scraping: {url}")
        result = await scraper.scrape_url(url)
        results.append(result)
        print(f"✓ [{index}/{total}] Done: {result['email_count']} emails, {result['phone_count']} phones")
        return result

async def main():
    print("=" * 70)
    print("🚀 SPEED TEST - Optimized Scraper")
    print("=" * 70)
    
    # Load URLs
    urls = load_urls()
    print(f"📋 Loaded {len(urls)} URLs from test_urls.txt")
    
    # Configuration
    MAX_CONCURRENT = 20  # Our optimized setting
    print(f"⚙️  Concurrency: {MAX_CONCURRENT} URLs at once")
    print(f"⚙️  Timeout: 8 seconds per page")
    print(f"⚙️  Wait times: 0.3s + 0.2s = 0.5s total")
    print("=" * 70)
    
    # Start timing
    start_time = time.time()
    start_datetime = datetime.now()
    print(f"⏱️  Start time: {start_datetime.strftime('%H:%M:%S')}")
    print()
    
    # Initialize scraper
    scraper = AsyncWebsiteScraper(use_proxy=False)
    await scraper.start()
    
    try:
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        results = []
        
        # Create tasks for all URLs
        tasks = [
            scrape_with_semaphore(url, scraper, semaphore, results, i+1, len(urls))
            for i, url in enumerate(urls)
        ]
        
        # Run all tasks in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        
    finally:
        await scraper.close()
    
    # End timing
    end_time = time.time()
    end_datetime = datetime.now()
    elapsed = end_time - start_time
    
    # Calculate stats
    total_emails = sum(r.get('email_count', 0) for r in results)
    total_phones = sum(r.get('phone_count', 0) for r in results)
    total_socials = sum(r.get('social_count', 0) for r in results)
    successful = len([r for r in results if r.get('email_count', 0) > 0 or r.get('phone_count', 0) > 0])
    
    # Print results
    print()
    print("=" * 70)
    print("✅ SCRAPING COMPLETE!")
    print("=" * 70)
    print(f"⏱️  End time: {end_datetime.strftime('%H:%M:%S')}")
    print(f"⏱️  Total time: {elapsed:.1f} seconds ({elapsed/60:.2f} minutes)")
    print(f"📊 URLs processed: {len(results)}")
    print(f"📧 Total emails found: {total_emails}")
    print(f"📱 Total phones found: {total_phones}")
    print(f"🔗 Total social links: {total_socials}")
    print(f"✓ Successful scrapes: {successful}")
    print(f"⚡ Speed: {len(urls)/elapsed:.1f} URLs per minute")
    print(f"⚡ Average: {elapsed/len(urls):.2f} seconds per URL")
    print("=" * 70)
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'speed_test_results_{timestamp}.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'url', 'title', 'emails', 'phones', 'address', 
            'social_links', 'email_count', 'phone_count', 'social_count',
            'confidence_score', 'scrape_timestamp'
        ])
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'url': result.get('url', ''),
                'title': result.get('title', ''),
                'emails': ', '.join(result.get('emails', [])),
                'phones': ', '.join(result.get('phones', [])),
                'address': result.get('address', ''),
                'social_links': ', '.join(result.get('social_links', [])),
                'email_count': result.get('email_count', 0),
                'phone_count': result.get('phone_count', 0),
                'social_count': result.get('social_count', 0),
                'confidence_score': result.get('confidence_score', 0),
                'scrape_timestamp': result.get('scrape_timestamp', '')
            })
    
    print(f"💾 Results saved to: {csv_filename}")
    print()
    
    # Save timing report
    report_filename = f'speed_test_report_{timestamp}.txt'
    with open(report_filename, 'w') as f:
        f.write("SPEED TEST REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Test Date: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Configuration: {MAX_CONCURRENT} concurrent URLs\n")
        f.write(f"Timeout: 8 seconds per page\n")
        f.write(f"Wait times: 0.5 seconds total per page\n\n")
        f.write(f"Total URLs: {len(urls)}\n")
        f.write(f"Total Time: {elapsed:.1f} seconds ({elapsed/60:.2f} minutes)\n")
        f.write(f"Speed: {len(urls)/elapsed:.1f} URLs per minute\n")
        f.write(f"Average: {elapsed/len(urls):.2f} seconds per URL\n\n")
        f.write(f"Results:\n")
        f.write(f"- Emails found: {total_emails}\n")
        f.write(f"- Phones found: {total_phones}\n")
        f.write(f"- Social links: {total_socials}\n")
        f.write(f"- Successful scrapes: {successful}/{len(results)}\n")
    
    print(f"📄 Report saved to: {report_filename}")
    print()

if __name__ == '__main__':
    asyncio.run(main())
