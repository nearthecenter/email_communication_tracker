# 🚀 Email Communication Tracker - Getting Started

**Welcome!** Your automated email communication tracking system is ready to go.

## 📋 What You Have

A complete system that:
- ✅ **Reads** emails from your Gmail automatically (hourly)
- ✅ **Categorizes** emails using AI (Sales, Support, HR, etc.)
- ✅ **Auto-replies** with answers from a Google Drive .docx document
- ✅ **Logs** everything to Google Sheets for tracking
- ✅ **Shows** a beautiful dashboard with statistics

## 🎯 Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
cd /home/trainee16/onit
pip install -e ".[email-tracker]"
```

### Step 2: Test Installation
```bash
python test_email_tracker_setup.py
```

You should see ✅ checkmarks for all items.

### Step 3: Get Google Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → Enable Gmail, Drive, Sheets APIs
3. Create OAuth 2.0 credentials (Desktop app)
4. Download JSON file → Save as `credentials.json` in project root

### Step 4: Prepare Your Documents
1. In Google Drive: Create or upload a .docx file named **"Email Responses.docx"**
2. Add Q&A pairs (the system will match emails to these answers)
3. Create a Google Sheet for logging
4. Get the Sheet ID from the URL

### Step 5: Update Configuration
Edit `run_email_tracker.py`:
```python
SPREADSHEET_ID = "PASTE_YOUR_SHEET_ID_HERE"
```

### Step 6: Run!
```bash
python run_email_tracker.py
```

Open browser → **http://localhost:8000** ← Dashboard!

## 📚 Documentation

Read these in order:

1. **EMAIL_TRACKER_README.md** (2 min read)
   - Overview of what it does
   - How it works
   - Features

2. **SETUP_EMAIL_TRACKER.md** (10 min read)
   - Step-by-step setup guide
   - Google Cloud configuration
   - Troubleshooting

3. **EMAIL_TRACKER_QUICK_REFERENCE.md** (ref)
   - Code examples
   - Common commands
   - FAQ

4. **EMAIL_TRACKER_IMPLEMENTATION_SUMMARY.md** (ref)
   - Technical details
   - Architecture
   - File structure

## 📁 Key Files

```
onit/
├── run_email_tracker.py              👈 START HERE (main entry point)
├── test_email_tracker_setup.py       👈 Verify installation
├── EMAIL_TRACKER_README.md           👈 Read first
├── SETUP_EMAIL_TRACKER.md            👈 Follow for setup
├── EMAIL_TRACKER_QUICK_REFERENCE.md  👈 Code examples
├── EMAIL_TRACKER_IMPLEMENTATION_SUMMARY.md  👈 Technical details
└── src/email_tracker/
    ├── gmail_service.py    - Gmail integration
    ├── categorizer.py      - Email categorization
    ├── doc_reader.py       - Google Drive reader
    ├── response_matcher.py - Answer matching
    ├── sheets_logger.py    - Google Sheets logging
    ├── scheduler.py        - Hourly processing
    └── web/               - Dashboard
```

## 🎨 Dashboard Preview

When you run `python run_email_tracker.py` and open http://localhost:8000:

```
┌─────────────────────────────────────────────────┐
│         📧 Email Tracker Dashboard              │
├─────────────────────────────────────────────────┤
│                                                 │
│  📥 Incoming    ⏳ Pending    ✅ Answered     │
│    [42]         [15]          [28]             │
│                                                 │
│  🔧 Manual Reply    ✔️ Done                   │
│       [8]          [12]                        │
│                                                 │
│  ┌──────────────────────────────────┐          │
│  │ Email Statistics (Pie Chart)      │          │
│  │  • Incoming: 35%                  │          │
│  │  • Pending: 12%                   │          │
│  │  • Answered: 23%                  │          │
│  │  • Manual: 7%                     │          │
│  │  • Done: 10%                      │          │
│  └──────────────────────────────────┘          │
│                                                 │
└─────────────────────────────────────────────────┘
```

Real-time updates! 🔄

## 🔄 How It Works

```
1️⃣  GMAIL
    Unread emails come in

2️⃣  CATEGORIZE
    AI categorizes (Sales? Support? HR?)

3️⃣  LOAD ANSWERS
    Load Q&A from Google Drive .docx

4️⃣  MATCH
    Find matching answer using keywords

5️⃣  AUTO-REPLY OR FLAG
    ✅ If match: Send reply automatically
    ❌ If no match: Mark for manual review

6️⃣  LOG
    Record everything in Google Sheets

7️⃣  DASHBOARD
    See real-time stats and status
```

## ⚡ What Happens Next

### First Run
1. System authenticates with Google
2. Creates tokens (saved locally)
3. Loads your answer document
4. Dashboard becomes available

### Every Hour (Default)
1. Checks Gmail for unread emails
2. Processes each one
3. Logs to Google Sheets
4. Updates dashboard

### You Can Also
- **Manual process**: Call immediately with code
- **Adjust sensitivity**: Change SIMILARITY_THRESHOLD
- **Add categories**: Customize categorizer
- **Change interval**: Modify EMAIL_CHECK_INTERVAL_MINUTES

## 🆘 Help!

### Issue: "File not found"
→ Check document name matches exactly ("Email Responses.docx")

### Issue: "Authorization required"
→ Delete `.pickle` files and re-run

### Issue: Dashboard won't load
→ Check port 8000 isn't in use

### Issue: No emails being processed
→ Verify Gmail API is enabled
→ Check emails are actually UNREAD

**More help?** See SETUP_EMAIL_TRACKER.md #Troubleshooting

## 🎓 Example Use Cases

### Sales Follow-ups
Map common sales questions to answers:
- "What's your pricing?" → Pricing document
- "Do you have a demo?" → Demo video link
- "Can I get a discount?" → Discount policy

### Customer Support
Automate FAQ responses:
- "How do I track my order?"
- "What's your return policy?"
- "How do I reset my password?"

### HR & Recruiting
Handle recruitment questions:
- "What's the salary range?"
- "What's your culture like?"
- "Am I qualified for this role?"

### Lead Generation
Qualify inbound inquiries:
- Auto-respond with qualification form
- Log interested leads
- Flag priority inquiries for follow-up

## ⚙️ Configuration (Advanced)

In `src/email_tracker/config.py`:

```python
# Basic Settings
SPREADSHEET_ID = "your-sheet-id"
DOC_FILE_NAME = "Email Responses.docx"
DASHBOARD_PORT = 8000

# Advanced
EMAIL_CHECK_INTERVAL_MINUTES = 60   # More frequent? Change to 15
SIMILARITY_THRESHOLD = 0.4           # Too aggressive? Change to 0.6
```

## 🔐 Security Notes

- Keep `credentials.json` private (add to .gitignore)
- Tokens are cached in `.pickle` files
- Google Drive: Read-only access only
- Gmail: Minimal scopes (read + reply only)

## 📊 Monitoring

Check these to see what's happening:

1. **Terminal output** - See processing logs
2. **Google Sheets** - View all logged emails
3. **Dashboard** - See real-time statistics
4. **Gmail** - See sent auto-replies

## 🚀 Next Steps

1. ✅ Read EMAIL_TRACKER_README.md
2. ✅ Follow SETUP_EMAIL_TRACKER.md
3. ✅ Run test_email_tracker_setup.py
4. ✅ Update run_email_tracker.py with your Sheets ID
5. ✅ Run `python run_email_tracker.py`
6. ✅ Open http://localhost:8000
7. ✅ Watch it process emails!
8. ✅ Check Google Sheets for logs

## 💡 Pro Tips

- **Test first**: Add a few test emails to Gmail before deploying
- **Monitor logs**: Watch terminal output to see what's happening
- **Check Sheets**: Verify logs are being recorded correctly
- **Review matches**: Make sure auto-replies are appropriate
- **Fine-tune**: Adjust SIMILARITY_THRESHOLD based on results

## 📞 Support

Everything is documented! Check:
- EMAIL_TRACKER_README.md - Overview
- SETUP_EMAIL_TRACKER.md - Setup help
- EMAIL_TRACKER_QUICK_REFERENCE.md - Code examples
- Code comments - In each module

## ✨ Key Features

✅ **Fully Automated**
✅ **Google Integration** (Gmail, Drive, Sheets)
✅ **Intelligent Categorization**
✅ **Keyword-Based Matching**
✅ **Real-Time Dashboard**
✅ **Complete Audit Trail**
✅ **Production Ready**
✅ **Easy to Configure**

---

## 🎉 You're All Set!

Your email tracker system is ready. Time to automate your inbox! 🚀

**Questions?** Read the documentation first, then check the code.

**Questions about Onit?** Check the main Onit README.

**Happy automating!** ✉️

---

*Built with ❤️ using FastAPI, Google APIs, and Onit*
