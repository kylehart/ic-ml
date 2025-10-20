# Health Quiz MVP Deployment Guide
## Railway + Formbricks Integration

This guide walks you through deploying the Health Quiz service to Railway and integrating it with Formbricks.

---

## Architecture Overview

```
User fills Formbricks form
  ↓
Formbricks fires webhook → Railway endpoint (/api/v1/webhook/formbricks)
  ↓
Railway processes quiz in background (6-8 seconds)
  ↓
Railway stores results by email hash
  ↓
Railway sends email with results (via Resend)
  ↓
Formbricks redirects user → Railway results page (/results)
  ↓
User enters email → Views personalized health recommendations
```

---

## Prerequisites

1. **GitHub account** (you have this - authenticated with Railway and Formbricks)
2. **Railway account** (free tier: $5/month credit)
3. **Formbricks account** (free tier)
4. **Resend account** (free tier: 100 emails/day, 3000 emails/month)
5. **OpenAI or Anthropic API key** (for LLM processing)

---

## Part 1: Railway Deployment

### Step 1: Connect GitHub Repository

1. Go to [railway.app](https://railway.app) and sign in with GitHub
KH:  need to commit to GitHub first. 
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `ic-ml` repository
4. Railway will automatically detect the `Dockerfile` and `railway.json`

### Step 2: Configure Environment Variables

In Railway dashboard, go to Variables tab and add:

```bash
# Required - LLM API Key (choose one)
OPENAI_API_KEY=sk-your-openai-key-here

# Or use Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Resend Email Service (highly recommended)
RESEND_API_KEY=re_your-resend-key-here
RESEND_FROM_EMAIL=health-quiz@yourdomain.com

# Railway automatically provides PORT
```

### Step 3: Deploy

1. Click "Deploy" - Railway will build from Dockerfile
2. Wait 2-3 minutes for build to complete
3. Railway will provide a URL like: `https://your-app.up.railway.app`
4. Test health endpoint: `https://your-app.up.railway.app/health`

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T...",
  "version": "1.0.0",
  "use_cases": []
}
```

### Step 4: Note Your Railway URL

Save your Railway URL - you'll need it for Formbricks configuration.

**Example:** `https://ic-ml-production.up.railway.app`

---

## Part 2: Resend Email Setup

### Step 1: Get Resend API Key

1. Go to [resend.com](https://resend.com) and sign up
2. Navigate to API Keys → Create API Key
3. Copy the key (starts with `re_`)

### Step 2: Verify Domain (Optional for Production)

For testing, you can send from `onboarding@resend.dev`

For production:
1. Add your domain in Resend dashboard
2. Add DNS records (SPF, DKIM, DMARC)
3. Update `RESEND_FROM_EMAIL` to use your domain

### Step 3: Update Railway Environment

Add to Railway Variables:
```bash
RESEND_API_KEY=re_your-actual-key-here
RESEND_FROM_EMAIL=health-quiz@yourdomain.com
```

Redeploy Railway after adding these.

---

## Part 3: Formbricks Survey Setup

### Step 1: Create New Survey

1. Log into [app.formbricks.com](https://app.formbricks.com)
2. Click "Create Survey" → "Link Survey" (for standalone form)
3. Name it "Health Quiz"

### Step 2: Add Survey Questions

Add these questions in order:

#### Question 1: Email (Required)
- **Type:** Free Text / Email
- **Question:** "What's your email address?"
- **ID:** Note this ID (e.g., `email-123`)
- **Required:** Yes
- **Placeholder:** "your.email@example.com"

#### Question 2: Health Issue Description (Required)
- **Type:** Long Text
- **Question:** "Please describe your main health concern or issue"
- **ID:** Note this ID (e.g., `health-issue-456`)
- **Required:** Yes
- **Placeholder:** "e.g., I've been experiencing digestive issues..."

#### Question 3: Primary Health Area
- **Type:** Single Select
- **Question:** "Which area best describes your primary concern?"
- **Options:**
  - Digestive Health
  - Immune Support
  - Stress & Anxiety
  - Sleep Issues
  - Joint & Muscle Pain
  - Energy & Vitality
  - Women's Health
  - Men's Health
  - Other

#### Question 4: Severity Level
- **Type:** Rating (1-10)
- **Question:** "On a scale of 1-10, how severe would you rate your concern?"
- **Min:** 1
- **Max:** 10

#### Question 5: What Have You Tried?
- **Type:** Long Text
- **Question:** "What have you already tried for this issue?"
- **Required:** No

#### Question 6: Age Range (Optional)
- **Type:** Single Select
- **Question:** "What's your age range?"
- **Options:**
  - 18-25
  - 26-35
  - 36-45
  - 46-55
  - 56-65
  - 66+

#### Question 7: Lifestyle Factors (Optional)
- **Type:** Long Text
- **Question:** "Any relevant lifestyle factors? (diet, exercise, stress levels, etc.)"

### Step 3: Configure Ending Card

1. Go to survey settings → "Thank You Card"
2. Set **Type:** "Redirect to URL"
3. Set **URL:** `https://your-app.up.railway.app/results`
4. Message: "Processing your health recommendations... You'll be redirected shortly."

### Step 4: Configure Webhook

1. In Formbricks, go to Integrations → Webhooks
2. Click "Add Webhook"
3. **URL:** `https://your-app.up.railway.app/api/v1/webhook/formbricks`
4. **Triggers:** Select "responseFinished"
5. **Surveys:** Select your "Health Quiz" survey
6. Click "Test Webhook" to verify connection
7. Save

---

## Part 4: Testing the Integration

### Test 1: Webhook Test (from Formbricks)

1. In Formbricks webhook settings, click "Send Test Webhook"
2. Check Railway logs for: `Received Formbricks webhook: responseFinished`
3. Should see response: `{"status": "accepted", "message": "Health quiz processing started"}`

### Test 2: Complete Survey End-to-End

1. Get your survey link from Formbricks (e.g., `https://app.formbricks.com/s/xyz`)
2. Fill out the survey completely with a real email you can access
3. Submit the form
4. You should be redirected to `https://your-app.up.railway.app/results`
5. Enter the same email address
6. Wait 3-5 seconds (auto-retry if still processing)
7. View your personalized health recommendations!

### Test 3: Email Delivery

1. Check the email inbox you used in the test
2. Should receive "Your Personalized Health Quiz Results from Rogue Herbalist"
3. Email contains full HTML report with product recommendations

---

## Part 5: Mapping Formbricks Question IDs

The webhook endpoint uses keyword matching to map Formbricks questions to our data model. You may need to adjust the mapping based on your actual question IDs.

### How to Find Question IDs

1. Submit a test form in Formbricks
2. Check Railway logs for the webhook payload
3. Look for the `data.response.data` object
4. Question IDs will be like: `{questionId: value}`

### Update Mapping (if needed)

Edit `src/web_service.py` line ~338:

```python
# Current keyword matching
if "email" in question_id.lower():
    email = value
elif "health" in question_id.lower() or "issue" in question_id.lower():
    health_issue = value
# ... etc

# If keyword matching doesn't work, use exact IDs:
QUESTION_ID_MAP = {
    "clx1a2b3c4d5": "email",
    "clx2b3c4d5e6": "health_issue",
    # ... add your actual IDs
}
```

---

## Part 6: Monitoring and Debugging

### Check Railway Logs

```bash
# View logs in real-time
# In Railway dashboard: Deployments → View Logs

# Look for these log messages:
✅ "Received Formbricks webhook: responseFinished"
✅ "Queued health quiz processing for user@example.com"
✅ "Processing health quiz for user@example.com"
✅ "Email sent successfully to user@example.com"
✅ "Successfully processed health quiz for user@example.com"
```

### Common Issues and Solutions

#### Issue: Webhook not receiving data
- **Check:** Formbricks webhook URL is correct
- **Check:** Railway app is running (check health endpoint)
- **Fix:** Make sure Railway deployment succeeded

#### Issue: "No email found in webhook payload"
- **Check:** Email question is actually required in Formbricks
- **Check:** Railway logs show what `question_id` keys are received
- **Fix:** Update question ID mapping in `web_service.py`

#### Issue: "Email sending disabled" in logs
- **Check:** `RESEND_API_KEY` is set in Railway environment
- **Check:** `RESEND_FROM_EMAIL` is set
- **Fix:** Add environment variables and redeploy

#### Issue: Results show "processing" forever
- **Check:** Railway logs for errors in `process_health_quiz_webhook`
- **Check:** LLM API key is valid (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
- **Fix:** Check logs for specific error, fix and redeploy

#### Issue: Results not found
- **Check:** Using the exact same email as submitted in form
- **Check:** Results expire after 24 hours
- **Fix:** Resubmit the quiz

---

## Part 7: Local Testing with ngrok

For local development before deploying to Railway:

### Step 1: Install ngrok

```bash
# macOS with Homebrew
brew install ngrok

# Or download from ngrok.com
```

### Step 2: Start Local Server

```bash
cd /Users/kylehart/Documents/dev/repos/all/ic-ml

# Set environment variables
export OPENAI_API_KEY=your-key
export RESEND_API_KEY=your-resend-key
export RESEND_FROM_EMAIL=health-quiz@yourdomain.com

# Start server
uvicorn src.web_service:app --reload --port 8000
```

### Step 3: Expose with ngrok

```bash
# In another terminal
ngrok http 8000
```

You'll get a URL like: `https://abc123.ngrok.io`

### Step 4: Update Formbricks Webhook

Temporarily update Formbricks webhook URL to:
```
https://abc123.ngrok.io/api/v1/webhook/formbricks
```

Now you can test locally with Formbricks sending real webhooks!

---

## Part 8: Cost Estimates

### Free Tier Limits

**Railway:**
- $5/month credit included in Hobby plan
- ~750 hours of uptime with basic container
- LLM costs are separate (paid to OpenAI/Anthropic)

**Formbricks:**
- Unlimited surveys on free tier
- Webhook integration included

**Resend:**
- 100 emails/day
- 3000 emails/month
- Perfect for MVP testing

**LLM Costs (per quiz):**
- OpenAI GPT-4o-mini: ~$0.0003 per quiz
- Anthropic Claude Haiku: ~$0.0007 per quiz

### When to Upgrade

**Railway:** If you exceed $5/month in compute
- ~1000 quizzes/month = well within free tier

**Resend:** If you exceed 3000 emails/month
- Next tier: $20/month for 50,000 emails

---

## Part 9: Going to Production

### Before Launch Checklist

- [ ] Test complete flow 5+ times with different emails
- [ ] Verify email delivery works
- [ ] Test on mobile devices
- [ ] Update `RESEND_FROM_EMAIL` to your verified domain
- [ ] Set up Railway alerts for errors
- [ ] Add Railway auto-scaling if expecting high traffic
- [ ] Consider adding PostgreSQL for persistent storage
- [ ] Add webhook signature verification for security
- [ ] Set up monitoring (Railway has built-in metrics)

### Security Enhancements

1. **Webhook Signature Verification** (future)
   - Formbricks may provide webhook signatures
   - Verify signatures to prevent spam

2. **Rate Limiting** (future)
   - Add rate limiting per email
   - Prevent abuse

3. **Data Privacy**
   - Results stored with email hash, not plaintext
   - 24-hour expiration built in
   - Consider GDPR compliance if targeting EU

---

## Part 10: Next Steps

### Phase 2 Enhancements

1. **Persistent Storage**
   - Add Railway PostgreSQL plugin
   - Store quiz results permanently
   - Enable "view past results" feature

2. **Real-time Processing**
   - Add WebSocket support
   - Show processing progress
   - Eliminate polling

3. **Analytics**
   - Track popular health concerns
   - Track product recommendation patterns
   - Measure email open rates (Resend provides this)

4. **Advanced Features**
   - Multi-language support
   - Follow-up quiz recommendations
   - User accounts and profiles

---

## Troubleshooting Quick Reference

| Symptom | Check | Solution |
|---------|-------|----------|
| Webhook not firing | Formbricks webhook config | Verify URL, trigger, survey selection |
| Health endpoint 404 | Railway deployment | Check build logs, redeploy |
| Email not sending | Railway env vars | Add RESEND_API_KEY, redeploy |
| Results not found | Email match | Use exact same email |
| Processing forever | Railway logs | Check for LLM API errors |
| CORS errors | Frontend domain | Update CORS in web_service.py |

---

## Support Resources

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Formbricks Docs:** [formbricks.com/docs](https://formbricks.com/docs)
- **Resend Docs:** [resend.com/docs](https://resend.com/docs)
- **Railway CLI:** `railway logs` for debugging

---

## Appendix: Environment Variables Reference

```bash
# Required for all deployments
OPENAI_API_KEY=sk-...              # Or ANTHROPIC_API_KEY
RESEND_API_KEY=re_...              # For email delivery
RESEND_FROM_EMAIL=quiz@domain.com  # Sender address

# Optional
PORT=8000                          # Railway provides this
ENVIRONMENT=production             # For logging
LOG_LEVEL=info                     # Logging verbosity
```

---

## Summary

You now have a complete Health Quiz MVP:

✅ **Formbricks** collects health information from users
✅ **Railway** processes quizzes with LLM (6-8 seconds)
✅ **Resend** emails beautiful HTML reports with product recommendations
✅ **Results page** allows users to retrieve their recommendations anytime (24hrs)

**Total setup time:** ~2 hours
**Cost:** $0/month (within free tiers)
**Scalability:** Can handle 1000s of quizzes/month before needing upgrades

Happy deploying! 🚀
