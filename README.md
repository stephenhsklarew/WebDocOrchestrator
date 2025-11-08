# WebDocOrchestrator

A modern web-based dashboard for orchestrating **DocIdeaGenerator** and **PersonalizedDocGenerator** with real-time progress updates and interactive topic selection.

## 🌟 Features

- ✅ **Web-based Dashboard** - Modern, responsive UI accessible from any browser
- ✅ **Real-time Progress** - WebSocket-powered live updates during execution
- ✅ **Interactive Topic Selection** - Visual cards with preview and selection
- ✅ **Mobile-friendly** - Responsive design works on phones and tablets
- ✅ **Remote Access** - Run on a server, access from anywhere
- ✅ **Configuration UI** - No YAML editing required
- ✅ **Live Monitoring** - See exactly what's happening in real-time

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- DocIdeaGenerator installed at `../DocIdeaGenerator`
- PersonalizedDocGenerator installed at `../PersonalizedDocGenerator`

### Installation

```bash
cd /Users/stephensklarew/Development/Scripts/WebDocOrchestrator

# Install dependencies
pip3 install -r requirements.txt
```

### Run the Server

```bash
python3 app.py
```

Open your browser to: **http://localhost:5000**

## 📖 How to Use

### Step 1: Configure Pipeline

1. Open the dashboard in your browser
2. Fill in the configuration form:
   - **Pipeline Name**: Give your pipeline a name
   - **Mode**: Choose test (free) or production (GPT-4o)
   - **Idea Generation**: Configure source, date range, labels
   - **Document Generation**: Set audience, type, size, output location
3. Click **🚀 Start Pipeline**

### Step 2: Watch Stage 1 (Idea Generation)

- Real-time progress bar shows status
- DocIdeaGenerator runs in the background
- Progress updates appear automatically
- Wait for "Ready for review" message

### Step 3: Review and Select Topics

- Interactive cards show all generated topics
- Click to select/deselect topics
- See title, preview, and word count for each
- Use **Select All** or **Select None** buttons
- Click **✍️ Generate Documents**

### Step 4: Watch Stage 2 (Document Generation)

- Progress bar shows current document being generated
- See X/Y progress counter
- Real-time status updates
- Wait for completion

### Step 5: View Results

- Summary shows successful vs failed documents
- Detailed breakdown per document
- Click **🔄 Start New Pipeline** to run again

## 🎨 Interface

### Configuration Panel
```
┌─────────────────────────────────────────────────┐
│ ⚙️ Pipeline Configuration                       │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Pipeline Name]  [Mode: test/production]      │
│                                                 │
│  Idea Generation     │  Document Generation    │
│  ├─ Source           │  ├─ Audience            │
│  ├─ Start Date       │  ├─ Type                │
│  ├─ Label            │  ├─ Size                │
│  └─ Focus            │  └─ Output              │
│                                                 │
│         [🚀 Start Pipeline]                     │
└─────────────────────────────────────────────────┘
```

### Progress Indicator
```
┌─────────────────────────────────────────────────┐
│ ①──────────── ②──────────── ③                   │
│ Idea Gen      Review        Doc Gen             │
│ ████████████  ░░░░░░░░░░░░  ░░░░░░░░░░░░        │
│                                                 │
│ Status: Generating ideas... 75%                 │
└─────────────────────────────────────────────────┘
```

### Topic Review
```
┌─────────────────────────────────────────────────┐
│ 📋 Review Generated Topics (5 found)            │
├─────────────────────────────────────────────────┤
│                                                 │
│ ☑ AI in Healthcare                              │
│   Exploring AI's role in modern medicine...    │
│   [342 words]                                   │
│                                                 │
│ ☐ Remote Work Trends                            │
│   The future of distributed teams...           │
│   [298 words]                                   │
│                                                 │
│ [Select All] [Select None]  [✍️ Generate Docs]  │
└─────────────────────────────────────────────────┘
```

## 🔧 Configuration Options

All configuration is done through the web UI:

### Global Settings
- **Pipeline Name**: Identify your pipeline
- **Mode**: `test` (Gemini - free) or `production` (GPT-4o)

### Idea Generation
- **Source**: `gmail` or `drive`
- **Start Date**: Filter from date (MMDDYYYY)
- **Label**: Gmail label filter
- **Focus**: Content analysis perspective

### Document Generation
- **Audience**: Target audience description
- **Type**: Document type (blog post, whitepaper, etc.)
- **Size**: Document length (e.g., "800 words")
- **Output**: Output location (local path or Google Drive URL)
- **Style File**: Optional writing style guide
- **Customer Story**: Optional customer story file

### Advanced
- **Retry on Failure**: Continue if a document fails
- **Timeouts**: Stage 1 and Stage 2 timeouts

## 🌐 Remote Access

### Run on Local Network

```bash
# The server binds to 0.0.0.0, so it's accessible from any device on your network
python3 app.py
```

Access from other devices: `http://YOUR_IP:5000`

### Run on a Server

```bash
# For production, use gunicorn with eventlet
pip3 install gunicorn

gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
```

### Secure with HTTPS (Optional)

Use a reverse proxy like nginx:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📊 Real-time Updates

The dashboard uses WebSockets for real-time communication:

- **Progress Updates**: Live progress bars and status messages
- **Stage Completion**: Automatic transition between stages
- **Error Notifications**: Immediate error display
- **No Polling**: Efficient, instant updates

## 🎯 Use Cases

### Single User (Desktop)
- Run locally on your machine
- Quick access via `localhost:5000`
- Ideal for personal content creation

### Team Access (Network)
- Run on a shared server
- Team members access via URL
- Centralized content pipeline
- No software installation for team members

### Remote Work (Cloud)
- Deploy to cloud server (AWS, DigitalOcean, etc.)
- Access from anywhere
- Mobile-friendly for review on the go
- Secure with authentication (future feature)

## 🔒 Security

**Current**: Single-user, no authentication

**For Production**:
- Add authentication (Flask-Login, OAuth)
- Use HTTPS with SSL certificates
- Set `SECRET_KEY` to a strong random value
- Restrict network access with firewall
- Consider adding rate limiting

## 🛠️ Troubleshooting

### Port Already in Use

```bash
# Change port in app.py (last line)
socketio.run(app, host='0.0.0.0', port=5001, debug=True)
```

### WebSocket Connection Failed

- Check firewall settings
- Ensure port 5000 is open
- Try accessing via IP address instead of hostname

### DocIdeaGenerator Not Found

- Verify paths in `app.py` lines ~179-180
- Ensure DocIdeaGenerator is at `../DocIdeaGenerator`

### Credentials Error

- DocIdeaGenerator needs `credentials.json` in its directory
- Token files must be accessible
- See main DocOrchestrator README for credential setup

## 📁 Project Structure

```
WebDocOrchestrator/
├── app.py                  # Main Flask application
├── templates/
│   └── index.html          # Web dashboard UI
├── static/
│   ├── css/               # Custom CSS (future)
│   └── js/                # Custom JS (future)
├── sessions/              # Session data (created at runtime)
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── .gitignore            # Git exclusions
```

## 🚧 Limitations

**Phase 1 Limitations**:
- ⚠️ Single concurrent session (one pipeline at a time)
- ⚠️ No authentication (single-user)
- ⚠️ DocIdeaGenerator must complete for Stage 1 to finish
- ⚠️ Session state not persisted (lost on server restart)

**Future Enhancements** (Phase 2):
- Multiple concurrent sessions
- User authentication and multi-user support
- Session persistence and recovery
- Advanced topic filtering and sorting
- Document preview before finalization
- Webhook notifications (Slack, email)
- API endpoints for programmatic access

## 📈 Performance

- **Fast UI**: Modern responsive design
- **Efficient**: WebSockets (not polling)
- **Scalable**: Can handle multiple users (with modifications)
- **Low overhead**: Minimal resource usage

## 🆚 vs. CLI Orchestrator

| Feature | CLI | Web |
|---------|-----|-----|
| Interface | Terminal | Browser |
| Progress | Text updates | Visual progress bars |
| Topic Review | Text checkboxes | Interactive cards |
| Remote Access | SSH required | URL access |
| Mobile Support | Poor | Excellent |
| Multi-user | No | Yes (with auth) |
| Real-time Updates | No | Yes (WebSockets) |

## 🤝 Contributing

This is a personal project, but improvements welcome!

## 📄 License

Same as parent projects (DocIdeaGenerator, PersonalizedDocGenerator)

## 🙏 Credits

- Built with Flask, Flask-SocketIO, TailwindCSS
- Orchestrates DocIdeaGenerator and PersonalizedDocGenerator
- Created with Claude Code

---

**Enjoy your web-based content generation pipeline!** 🚀✨
