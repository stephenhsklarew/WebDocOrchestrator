# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd /Users/stephensklarew/Development/Scripts/WebDocOrchestrator
pip3 install -r requirements.txt
```

### 2. Start the Server

```bash
python3 app.py
```

You'll see:
```
============================================================
🚀 WebDocOrchestrator Starting
============================================================

Open your browser to: http://localhost:5000

Press Ctrl+C to stop the server

============================================================
```

### 3. Open the Dashboard

Open your browser to: **http://localhost:5000**

### 4. Configure Your Pipeline

Fill in the form with your settings:

**Required fields:**
- Pipeline Name: "My Blog Pipeline"
- Mode: "test" (free) or "production" (GPT-4o)
- Source: "gmail" or "drive"
- Audience: "business executives"
- Document Type: "blog post"
- Size: "800 words"
- Output: "./output"

**Optional fields:**
- Start Date: "01012025" (MMDDYYYY)
- Gmail Label: "AIQ"
- Content Focus: "AI transformation"
- Writing Style File: "/path/to/style.txt"
- Customer Story: "/path/to/story.txt"

### 5. Start Pipeline

Click **🚀 Start Pipeline** button

### 6. Watch Stage 1 Progress

- Progress bar shows idea generation status
- Wait for "Ready for review" message
- This may take a few minutes

### 7. Review Topics

- Interactive cards show all generated topics
- Click to select topics you want
- First 3 are auto-selected
- Use **Select All** or **Select None** as needed
- Click **✍️ Generate Documents**

### 8. Watch Stage 2 Progress

- Progress bar shows document generation
- See which document is being generated
- Wait for completion

### 9. View Results

- See summary: X/Y documents successful
- Review detailed status per document
- Click **🔄 Start New Pipeline** to run again

## Example Session

```
┌─ Configuration ─────────────────────────────────┐
│ Pipeline: Weekly Blog Posts                    │
│ Mode: test (free)                              │
│ Source: gmail                                  │
│ Start Date: 01012025                           │
│                                                │
│ [🚀 Start Pipeline]                            │
└─────────────────────────────────────────────────┘

↓ Stage 1: Generating Ideas... 100%

┌─ Review Topics (5 found) ───────────────────────┐
│ ☑ AI in Healthcare (342 words)                 │
│ ☐ Remote Work Trends (298 words)               │
│ ☑ Data Integration (415 words)                 │
│ ☐ DevOps Practices (267 words)                 │
│ ☑ Cloud Security (389 words)                   │
│                                                │
│ [Select All] [Select None] [✍️ Generate Docs]  │
└─────────────────────────────────────────────────┘

↓ Stage 2: Generating Documents... 100%

┌─ Results ────────────────────────────────────────┐
│ ✅ 3 / 3 Documents Generated Successfully       │
│                                                 │
│ ✅ AI in Healthcare                             │
│ ✅ Data Integration                             │
│ ✅ Cloud Security                               │
│                                                 │
│ [🔄 Start New Pipeline]                         │
└─────────────────────────────────────────────────┘
```

## Troubleshooting

### "Cannot connect to server"
- Make sure `python3 app.py` is running
- Check http://localhost:5000 not https
- Try http://127.0.0.1:5000 instead

### "DocIdeaGenerator not found"
- Ensure DocIdeaGenerator is at `../DocIdeaGenerator`
- Check file paths in `app.py`

### "credentials.json not found"
- DocIdeaGenerator needs credentials.json
- Copy from another project or download from Google Cloud

### Port Already in Use
- Edit `app.py` last line: change `port=5000` to `port=5001`
- Access via http://localhost:5001

## Tips

### Cost Management
- Use **test mode** (free Gemini) for development
- Switch to **production mode** (GPT-4o) for final content
- Test mode has 1,500 free requests/day

### Topic Selection
- Preview shows first 300 characters
- Word count helps estimate topic depth
- Select 2-3 topics for quick testing
- Scale up to 5-10 for production

### Remote Access
Server runs on `0.0.0.0:5000` - accessible from network:
- Find your IP: `ifconfig | grep "inet "`
- Access from other devices: `http://YOUR_IP:5000`
- Works on phones and tablets!

### Multiple Pipelines
- Run one at a time (single session limitation)
- Wait for completion before starting another
- Future version will support concurrent sessions

## Next Steps

1. **Test Run**: Start with test mode, 1-2 topics
2. **Iterate**: Adjust configuration based on results
3. **Scale**: Increase to more topics per run
4. **Production**: Switch to production mode for final content
5. **Team Access**: Share URL for team review

Enjoy your web-based content pipeline! 🚀
