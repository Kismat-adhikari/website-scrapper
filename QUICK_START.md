# Quick Start Guide

## Which Scraper Should I Use?

### 🚀 **RECOMMENDED: `ultimate_scraper_optimized.py`**
Use this for best performance and reliability.

```bash
python ultimate_scraper_optimized.py
```

### 📝 Basic: `ultimate_scraper.py`
Use this only if you have a very old/slow computer.

```bash
python ultimate_scraper.py
```

---

## Simple Usage

### Interactive Mode (Easiest)
```bash
python ultimate_scraper_optimized.py
```
Then enter URLs when prompted.

### From File
```bash
python ultimate_scraper_optimized.py urls.txt
```

### Custom Settings
```bash
# Faster (20 parallel requests)
python ultimate_scraper_optimized.py urls.txt --max-concurrent 20

# More reliable (5 retry attempts)
python ultimate_scraper_optimized.py urls.txt --retry 5

# Slower but safer (avoid bans)
python ultimate_scraper_optimized.py urls.txt --rate-limit 2.0
```

---

## What's Different?

| Feature | Original | Optimized |
|---------|----------|-----------|
| Speed | Slow | **10x Faster** |
| Parallel Processing | ❌ No | ✅ Yes |
| Retry Logic | ❌ No | ✅ Yes |
| Browser Reuse | ❌ No | ✅ Yes |
| Logging | Basic | Advanced |
| Social Media Filter | ✅ Yes | ✅ Yes |

---

## Examples

### Scrape 1 URL
```bash
python ultimate_scraper_optimized.py
# Enter: https://example.com
```

### Scrape Multiple URLs
```bash
python ultimate_scraper_optimized.py
# Enter: https://example.com, https://another.com, https://third.com
```

### Scrape from File
Create `my_urls.txt`:
```
https://example.com
https://another.com
https://third.com
```

Then run:
```bash
python ultimate_scraper_optimized.py my_urls.txt
```

---

## Output

Results are saved to timestamped CSV files:
- `optimized_scrape_20251120_123456.csv`

Each file contains:
- URLs
- Titles
- Emails
- Phone numbers
- Social media links
- Addresses
- And much more!

---

## Tips

1. **Start small** - Test with 5-10 URLs first
2. **Check the log** - Look at `scraper.log` for errors
3. **Adjust settings** - Use `--max-concurrent` to control speed
4. **Be patient** - Browser scraping takes time
5. **Avoid social media** - The scraper will reject these automatically

---

## Need Help?

Check these files:
- `OPTIMIZATION_GUIDE.md` - Detailed comparison and settings
- `URL_VALIDATION.md` - Info about URL filtering
- `README.md` - Original documentation
- `scraper.log` - Error logs

---

## Common Issues

### "Too many open files"
```bash
python ultimate_scraper_optimized.py urls.txt --max-concurrent 5
```

### Getting blocked
```bash
python ultimate_scraper_optimized.py urls.txt --rate-limit 2.0
```

### Low success rate
```bash
python ultimate_scraper_optimized.py urls.txt --retry 5
```

---

## That's It!

Just run:
```bash
python ultimate_scraper_optimized.py
```

And follow the prompts. Easy! 🎉
