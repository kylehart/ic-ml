# Formbricks ID Verification - October 21, 2025

## ✅ VERIFICATION RESULT: ALL IDS ARE CORRECT

Extracted actual IDs from Formbricks production survey via Management API and compared with our code mappings.

## Question IDs (All Correct ✅)

| Question | ID in Code | ID in Formbricks | Status |
|----------|------------|------------------|--------|
| Email | `d9klpkum9vi8x9vkunhu63fn` | `d9klpkum9vi8x9vkunhu63fn` | ✅ Match |
| Health Issue | `dc185mu0h2xzutpzfgq8eyjy` | `dc185mu0h2xzutpzfgq8eyjy` | ✅ Match |
| Primary Area | `ty1zv10pffpxh2a2bymi2wz7` | `ty1zv10pffpxh2a2bymi2wz7` | ✅ Match |
| Severity | `iht7n48iwkoc1jc8ubnzrqi7` | `iht7n48iwkoc1jc8ubnzrqi7` | ✅ Match |
| Tried Already | `ud6nnuhrgf9trqwe8j3kibii` | `ud6nnuhrgf9trqwe8j3kibii` | ✅ Match |
| Age Range | `yru7w3e402yk8vpf1dfbw0tr` | `yru7w3e402yk8vpf1dfbw0tr` | ✅ Match |
| Lifestyle | `pr4jtzy9epmquvwdksj9tctb` | `pr4jtzy9epmquvwdksj9tctb` | ✅ Match |

## Primary Health Area Choice IDs (All Correct ✅)

| Choice Label | ID in Code | ID in Formbricks | Status |
|--------------|------------|------------------|--------|
| Digestive Health | `k7ly7nx8lvgwedl1yctb215y` | `k7ly7nx8lvgwedl1yctb215y` | ✅ Match |
| Immune Support | `xugvsda3meo6onr84icgen6j` | `xugvsda3meo6onr84icgen6j` | ✅ Match |
| Stress & Anxiety | `qir7u9yy7eh9rqad1jvgh41e` | `qir7u9yy7eh9rqad1jvgh41e` | ✅ Match |
| Sleep Issues | `mn3195wdsqv6qf80tt299v2q` | `mn3195wdsqv6qf80tt299v2q` | ✅ Match |
| Joint & Muscle Pain | `jhs5ehsljo52rrd9yuxbw7td` | `jhs5ehsljo52rrd9yuxbw7td` | ✅ Match |
| Energy & Vitality | `zhu8gde20tnv7talgv5ruec8` | `zhu8gde20tnv7talgv5ruec8` | ✅ Match |
| Women's Health | `xlzt05zhync9v1ysegm4a80c` | `xlzt05zhync9v1ysegm4a80c` | ✅ Match |
| Men's Health | `m3jjnnug2s1iwtf1lo0l6uip` | `m3jjnnug2s1iwtf1lo0l6uip` | ✅ Match |
| Other | `other` | `other` | ✅ Match |

## Age Range Choice IDs (All Correct ✅)

| Choice Label | ID in Code | ID in Formbricks | Status |
|--------------|------------|------------------|--------|
| 18-25 | `owv82s8m0kumnrp08j8gaqhu` | `owv82s8m0kumnrp08j8gaqhu` | ✅ Match |
| 26-35 | `nults2ndbrn6bovvs4ce03ax` | `nults2ndbrn6bovvs4ce03ax` | ✅ Match |
| 36-45 | `u9fy0mtyjddkzrkhruh0682p` | `u9fy0mtyjddkzrkhruh0682p` | ✅ Match |
| 46-55 | `e7drxvgsjys4vewrmq5qvkoy` | `e7drxvgsjys4vewrmq5qvkoy` | ✅ Match |
| 56-65 | `l9xn0kf9c8rbndzgghthsr73` | `l9xn0kf9c8rbndzgghthsr73` | ✅ Match |
| 66+ | `lu5l0u7myjxy8b8to0zaix8m` | `lu5l0u7myjxy8b8to0zaix8m` | ✅ Match |

## Conclusion

**All IDs in `src/web_service.py` are correct and match Formbricks exactly.**

The prefill bugs reported by the user are NOT caused by incorrect ID mappings. The root cause must be elsewhere in the data flow:

1. **Possible issues:**
   - Data extraction from webhook (lines 404-461)
   - User_data dict construction (lines 540-548)
   - URL generation logic (lines 1066-1157)
   - URL encoding/escaping
   - Circular bug: bad prefilled URL → bad data → bad new URL

2. **Next debugging steps:**
   - Submit FRESH form (no prefill) with clean data
   - Check Railway logs for user_data values
   - Verify URL generation with good input
   - Test generated prefill URL manually

## Verification Method

```bash
# Extracted via Formbricks Management API
export FORMBRICKS_API_KEY=2a553b11fe1e97fe0d5c8cacbadfb571
python3 extract_formbricks_ids.py

# Compared output in formbricks_survey_structure.json
# with mappings in src/web_service.py lines 367-402 and 1090-1118
```

Verified by: Claude Code
Date: October 21, 2025
Survey ID: `cmf5homcz0p1kww010hzezjjp`
Environment: Production
