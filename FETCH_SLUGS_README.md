# Fetching WooCommerce Product Slugs

This guide explains how to fetch actual product slugs from the Rogue Herbalist WooCommerce store using the REST API.

## Problem

The current product catalog has **generated slugs** that don't always match the actual WooCommerce product URLs:

- Generated: `digestive-bitters-formula-2-oz` → https://rogueherbalist.com/product/digestive-bitters-formula-2-oz/ ❌ 404
- Actual: `digestive-bitters-formula-2oz-tincture` → https://rogueherbalist.com/product/digestive-bitters-formula-2oz-tincture/ ✅ 200

## Solution: WooCommerce REST API

The `fetch_woocommerce_slugs.py` script fetches all products from WooCommerce with their actual slugs.

## Prerequisites

1. **WooCommerce REST API Credentials**

   You need to generate API keys from the WooCommerce admin panel:

   - Log in to WordPress admin: https://rogueherbalist.com/wp-admin
   - Navigate to: **WooCommerce → Settings → Advanced → REST API**
   - Click **Add key**
   - Description: "Product Slug Fetcher"
   - User: Select admin user
   - Permissions: **Read** (we only need read access)
   - Click **Generate API key**
   - Copy the **Consumer key** and **Consumer secret**

2. **Python Dependencies**

   ```bash
   pip install requests
   ```

## Usage

### Option 1: Environment Variables (Recommended)

```bash
export WC_CONSUMER_KEY="ck_xxxxxxxxxxxxxxxxxxxx"
export WC_CONSUMER_SECRET="cs_xxxxxxxxxxxxxxxxxxxx"
python fetch_woocommerce_slugs.py
```

### Option 2: Edit Script (One-time use)

1. Open `fetch_woocommerce_slugs.py`
2. Find lines 23-24:
   ```python
   # CONSUMER_KEY = "ck_xxxxxxxxxxxxxxxxxxxx"
   # CONSUMER_SECRET = "cs_xxxxxxxxxxxxxxxxxxxx"
   ```
3. Uncomment and paste your credentials
4. Run: `python fetch_woocommerce_slugs.py`
5. **Delete credentials from script after use!**

## What It Does

1. **Fetches all products** from WooCommerce API (paginated, 100 per page)
2. **Extracts fields**: id, name, slug, sku, permalink, status, stock_status
3. **Saves raw API response**: `data/rogue-herbalist/woocommerce-api-products.json`
4. **Verifies 5 random URLs** to confirm slugs are correct
5. **Updates catalog**: Creates `data/rogue-herbalist/minimal-product-catalog-updated-slugs.csv`

## Example Output

```
======================================================================
WooCommerce Product Slug Fetcher
======================================================================
🔍 Fetching products from https://rogueherbalist.com...
   Page 1/8: Fetched 100 products (Total: 100/787)
   Page 2/8: Fetched 100 products (Total: 200/787)
   ...
   Page 8/8: Fetched 87 products (Total: 787/787)
✅ Fetched 787 total products
💾 Raw API response saved to: data/rogue-herbalist/woocommerce-api-products.json

🔍 Verifying 5 sample product URLs...
   ✅ 1111: four-mushroom-immune-complex-2oz
   ✅ 9083: digestive-bitters-formula-2oz-tincture
   ✅ 3678: hemp-bitters-2oz
   ✅ 5356: happy-belly-herbal-honey-6oz
   ✅ 9048: christophers-lower-bowel-formula-capsules

📝 Updating catalog: data/rogue-herbalist/minimal-product-catalog.csv
   Updated 9083: digestive-bitters-formula-2-oz → digestive-bitters-formula-2oz-tincture
   Updated 5234: milk-thistle-seed-1oz → milk-thistle-seed-organic-1oz-bag
   ...
✅ Updated catalog saved to: data/rogue-herbalist/minimal-product-catalog-updated-slugs.csv

======================================================================
✅ Done! Next steps:
   1. Review the updated catalog
   2. Backup current catalog if needed
   3. Replace minimal-product-catalog.csv with updated version
======================================================================
```

## Next Steps

After running the script:

1. **Review the updated catalog**:
   ```bash
   # Check how many slugs changed
   diff data/rogue-herbalist/minimal-product-catalog.csv \
        data/rogue-herbalist/minimal-product-catalog-updated-slugs.csv | wc -l
   ```

2. **Backup current catalog**:
   ```bash
   cp data/rogue-herbalist/minimal-product-catalog.csv \
      data/rogue-herbalist/backup/minimal-product-catalog-$(date +%Y%m%d).csv
   ```

3. **Replace with updated version**:
   ```bash
   mv data/rogue-herbalist/minimal-product-catalog-updated-slugs.csv \
      data/rogue-herbalist/minimal-product-catalog.csv
   ```

4. **Test health quiz** to verify product URLs work:
   ```bash
   python src/run_health_quiz.py --persona "Sarah Chen"
   ```

## API Details

- **Endpoint**: `GET https://rogueherbalist.com/wp-json/wc/v3/products`
- **Authentication**: HTTP Basic Auth (Consumer Key as username, Secret as password)
- **Pagination**: 100 products per page (max allowed)
- **Fields Requested**: `id,name,slug,sku,permalink,status,stock_status`
- **Total Products**: ~787 (as of October 2025)

## Troubleshooting

### Error: "WooCommerce API credentials not set"
- Set environment variables or edit script with credentials

### Error: HTTP 401 Unauthorized
- Check that API keys are correct
- Verify permissions are set to "Read" or "Read/Write"
- Ensure WordPress permalinks are NOT set to "Plain"

### Error: HTTP 404 on API endpoint
- Verify WordPress permalinks are configured (not "Plain")
- Try accessing: https://rogueherbalist.com/wp-json/wc/v3/products manually

### Verification failures (some URLs return 404)
- This is expected for draft/private products
- Check `status` field in JSON output
- Only `status: "publish"` products should have working URLs

## Security Notes

- **Never commit API credentials** to git
- Use environment variables for credentials
- Generate keys with **Read-only** permissions
- Delete keys from WooCommerce admin after use
- Keys can be regenerated anytime if compromised
