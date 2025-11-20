# URL Validation Feature

## Overview
The scraper now automatically detects and rejects social media URLs to ensure you only scrape business websites.

## Blocked Platforms
The following social media and platform URLs are automatically rejected:

- **Facebook** (facebook.com, fb.com)
- **Instagram** (instagram.com)
- **Twitter/X** (twitter.com, x.com)
- **LinkedIn** (linkedin.com)
- **YouTube** (youtube.com)
- **TikTok** (tiktok.com)
- **Snapchat** (snapchat.com)
- **Pinterest** (pinterest.com)
- **Reddit** (reddit.com)
- **Tumblr** (tumblr.com)
- **WhatsApp** (whatsapp.com)
- **Telegram** (telegram.org, t.me)
- **Discord** (discord.com, discord.gg)
- **Twitch** (twitch.tv)
- **Vimeo** (vimeo.com)
- **Flickr** (flickr.com)
- **Medium** (medium.com)

## How It Works

### Interactive Mode
When you enter URLs manually, the scraper will:
1. Show a warning about social media URLs
2. Validate each URL you provide
3. Display any invalid URLs with reasons
4. Ask if you want to continue with valid URLs only

Example:
```
Enter website URL(s) to scrape: https://facebook.com/page, https://example.com

[!] WARNING: Some URLs are invalid:
    ✗ https://facebook.com/page
      Reason: Social media URLs are not supported (use business websites only)

Continue with remaining valid URLs? (y/n):
```

### File Mode
When using a file with URLs, invalid URLs are skipped during scraping:
```
[1/3] https://facebook.com/page
  ✗ SKIPPED: Social media URLs are not supported (use business websites only)

[2/3] https://example.com
  → Trying FAST HTTP...
  ✓ HTTP Success (FAST)
```

## Statistics
The final report now includes skipped URLs:
```
SCRAPING COMPLETE
==================
Total URLs:        3
Successful:        2
  - HTTP (fast):   2
  - Browser:       0
Skipped:           1
Failed:            0
Success Rate:      66.7%
```

## Valid URL Requirements
URLs must:
- Start with `http://` or `https://`
- Have a proper domain format (contain at least one dot)
- NOT be a social media platform

## Examples

### ✓ Valid URLs
- `https://example.com`
- `https://www.mycompany.com`
- `http://business-site.co.uk`

### ✗ Invalid URLs
- `https://facebook.com/mypage` (social media)
- `https://instagram.com/brand` (social media)
- `example.com` (missing http://)
- `invalid-url` (invalid format)
