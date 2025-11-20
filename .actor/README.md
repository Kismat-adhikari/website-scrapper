# Website & Email Scraper - Professional Data Extraction

Fast and accurate website scraper that extracts emails, phone numbers, addresses, and social media links from any website. Perfect for lead generation, contact discovery, and business intelligence.

## 🚀 Features

- ✅ **Email Extraction** - Plain text, obfuscated, mailto links
- ✅ **Phone Numbers** - US and international formats
- ✅ **Physical Addresses** - Street, city, state, country
- ✅ **Social Media Links** - Facebook, Instagram, LinkedIn, Twitter, TikTok, YouTube, etc.
- ✅ **Metadata** - Page title, description, word count
- ✅ **Auto-Discovery** - Automatically finds contact, about, support pages
- ✅ **Verification** - Confidence scores for data quality
- ✅ **Error Handling** - Automatic retries and failure logging
- ✅ **Resume Capability** - Continue from where it left off if interrupted
- ✅ **Bulk Processing** - Handle 1 to 10,000+ URLs efficiently

## 📊 Input

```json
{
  "urls": [
    "https://example.com",
    "https://another-site.com"
  ],
  "maxConcurrency": 10,
  "depth": 2,
  "autoDiscoverPages": true,
  "extractEmails": true,
  "extractPhones": true,
  "extractAddresses": true,
  "extractSocials": true,
  "minConfidenceScore": 0.0
}
```

### Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `urls` | Array | Required | List of URLs to scrape |
| `maxConcurrency` | Number | 10 | Max concurrent requests |
| `depth` | Number | 2 | Crawl depth (0-3) |
| `autoDiscoverPages` | Boolean | true | Auto-find contact/about pages |
| `targetPages` | Array | ["contact", "about", ...] | Pages to discover |
| `retryAttempts` | Number | 3 | Retry failed requests |
| `timeout` | Number | 30 | Page timeout (seconds) |
| `useProxy` | Boolean | false | Use Apify proxy |
| `extractEmails` | Boolean | true | Extract emails |
| `extractPhones` | Boolean | true | Extract phone numbers |
| `extractAddresses` | Boolean | true | Extract addresses |
| `extractSocials` | Boolean | true | Extract social links |
| `minConfidenceScore` | Number | 0.0 | Min confidence (0.0-1.0) |

## 📤 Output

```json
{
  "url": "https://example.com",
  "title": "Example Company",
  "emails": ["contact@example.com", "support@example.com"],
  "phones": ["+1-555-123-4567"],
  "address": "123 Main St, City, State 12345, USA",
  "social_links": [
    "https://facebook.com/example",
    "https://linkedin.com/company/example"
  ],
  "meta_description": "Example company description",
  "contact_form": true,
  "blog_present": true,
  "industry": "Technology",
  "word_count": 1500,
  "email_count": 2,
  "phone_count": 1,
  "social_count": 2,
  "confidence_score": 0.95,
  "scrape_timestamp": "2025-11-20T12:00:00Z"
}
```

## 🎯 Use Cases

### Lead Generation
Extract contact information from company websites for sales outreach.

### Market Research
Gather business data and contact details for market analysis.

### Contact Discovery
Find email addresses and phone numbers for networking.

### Data Enrichment
Enhance existing databases with additional contact information.

### Competitor Analysis
Collect contact and social media information from competitors.

## 💡 Tips

### For Best Results

1. **Use Auto-Discovery** - Enable `autoDiscoverPages` to find contact pages automatically
2. **Set Appropriate Depth** - Use depth 2 for most websites (homepage + 2 levels)
3. **Check Confidence Scores** - Higher scores indicate more reliable data
4. **Use Proxies for Large Jobs** - Enable `useProxy` when scraping 100+ URLs
5. **Filter by Confidence** - Set `minConfidenceScore` to 0.5 for higher quality results

### Performance

- **Small Jobs (1-10 URLs):** ~1-2 minutes
- **Medium Jobs (10-100 URLs):** ~5-15 minutes
- **Large Jobs (100-1000 URLs):** ~30-90 minutes
- **Very Large Jobs (1000+ URLs):** ~2-5 hours

### Cost Estimation

- **Per URL:** ~0.001-0.005 CU (depending on page complexity)
- **100 URLs:** ~$0.05-$0.25
- **1000 URLs:** ~$0.50-$2.50

## 🔧 Advanced Features

### Resume Capability
If the Actor is interrupted, it will automatically resume from where it left off.

### Confidence Scoring
Each result includes a confidence score (0.0-1.0) based on:
- Email found: +0.5
- Phone found: +0.2
- Social links found: +0.15
- Contact form found: +0.15

### Error Handling
- Automatic retries (configurable)
- Failed URLs logged separately
- Graceful degradation (continues on errors)

### Data Quality
- Email deduplication
- Phone number normalization
- Address formatting
- Social link validation

## 📊 Output Formats

Results can be downloaded as:
- **JSON** - Structured data
- **CSV** - Spreadsheet format
- **Excel** - Microsoft Excel format
- **RSS** - Feed format

## 🆘 Troubleshooting

### No Emails Found
- Check if website has contact page
- Try increasing `depth` to 3
- Enable `autoDiscoverPages`
- Check confidence score (may be low quality site)

### Slow Performance
- Reduce `maxConcurrency`
- Decrease `depth`
- Enable `useProxy` for better reliability

### High Failure Rate
- Increase `retryAttempts`
- Enable `useProxy`
- Check if websites are blocking scrapers

## 📚 Related Actors

- **Email Validator** - Validate extracted emails
- **Phone Validator** - Verify phone numbers
- **Social Media Scraper** - Deep scrape social profiles

## 🔗 Links

- **GitHub:** https://github.com/Kismat-adhikari/website-scrapper
- **Support:** Open an issue on GitHub
- **Documentation:** See GitHub README

## 📝 License

MIT License - Free to use and modify

## 🎉 Credits

Built with:
- Playwright for browser automation
- BeautifulSoup for HTML parsing
- Apify SDK for cloud deployment

---

**Need help?** Open an issue on GitHub or contact support through Apify.
