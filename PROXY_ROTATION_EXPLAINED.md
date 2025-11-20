# 🔄 Smart Proxy Rotation System

## How It Works:

### 📊 Rotation Logic:
- **Every 7 URLs scraped** → Automatically switches to next proxy
- **10 proxies available** → Cycles through all of them
- **Random delays** → 2-5 seconds between URLs (human-like behavior)
- **Browser restart** → New browser session with new proxy

### 🎯 Example with 20 URLs:

```
URLs 1-7   → Proxy #1 (72.46.139.137:6697)
URLs 8-14  → Proxy #2 (rotates automatically)
URLs 15-20 → Proxy #3 (rotates automatically)
```

### 🛡️ Anti-Detection Features:

1. **Proxy Rotation** - Changes IP every 7 requests
2. **Random Delays** - 2-5 second pauses between scrapes
3. **Browser Restart** - Fresh browser session with each proxy
4. **Human-like Scrolling** - Smooth, incremental scrolling
5. **Network Idle Wait** - Waits for page to fully load

### 📈 Benefits:

✅ **Avoids rate limiting** - Different IP addresses
✅ **Bypasses captchas** - Looks like different users
✅ **Prevents blocking** - Distributes requests across proxies
✅ **Safer scraping** - Mimics human behavior
✅ **Automatic** - No manual intervention needed

### 🔢 Math:

- **10 proxies** × **7 uses each** = **70 URLs** before cycling back to first proxy
- Each proxy gets a break while others are used
- Reduces detection risk significantly

### 💡 Usage:

Just enter your URLs - the system handles everything automatically!

```bash
python scraper.py
```

Enter: `https://site1.com, https://site2.com, https://site3.com, ...`

The scraper will:
1. Use Proxy #1 for first 7 URLs
2. Switch to Proxy #2 for next 7 URLs
3. Continue rotating through all 10 proxies
4. Add random delays between requests
5. Restart browser with each proxy change
