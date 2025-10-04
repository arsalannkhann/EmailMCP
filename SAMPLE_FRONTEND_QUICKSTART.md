# 🚀 EmailMCP Sample Frontend - Quick Start Guide

This guide will get you up and running with the complete EmailMCP frontend integration in **under 5 minutes**.

## 📦 What You're Getting

A **complete, working frontend application** that demonstrates:
- ✅ Google OAuth authentication
- ✅ Gmail OAuth integration (send emails as users)
- ✅ Email sending with HTML, CC, BCC support
- ✅ Email analytics dashboard with charts
- ✅ Real-time connection testing
- ✅ Production-ready code

## ⚡ Quick Start (3 Steps)

### Step 1: Navigate to the Frontend
```bash
cd sample-frontend
```

### Step 2: Start the Server

Choose one option:

**Option A - Python (Recommended):**
```bash
python3 -m http.server 8000
```

**Option B - Node.js:**
```bash
npx http-server -p 8000
```

**Option C - Interactive Setup:**
```bash
./setup.sh
```

### Step 3: Open in Browser
```
http://localhost:8000
```

**That's it!** The application is now running.

## 🎯 Try It Out

### 1. Sign In
- Click "Sign in with Google"
- Select your Google account

### 2. Connect Gmail
- Click "Connect Gmail Account"
- Grant permissions
- You'll be redirected back automatically

### 3. Send an Email
- Fill in the email form:
  - To: your-email@example.com
  - Subject: Test Email
  - Message: Hello from EmailMCP!
- Click "Send Email"
- Check your inbox!

### 4. View Analytics
- See your email stats
- View the activity chart
- Check recent emails

## 📁 What's Included

```
sample-frontend/
├── index.html              # Main app
├── callback.html          # OAuth handler
├── test-connection.html   # Test utility
├── app.js                 # Application logic
├── style.css              # Styling
├── config.js              # Configuration
├── setup.sh               # Setup script
├── Dockerfile             # Docker config
├── README.md              # Detailed docs
├── TESTING.md             # Test guide
└── backend-proxy/         # Optional proxy server
    ├── server.js
    ├── package.json
    └── README.md
```

## 🔧 Configuration

All settings are in `config.js`:

```javascript
const CONFIG = {
    EMAILMCP_SERVICE_URL: 'https://emailmcp-hcnqp547xa-uc.a.run.app',
    EMAILMCP_API_KEY: 'emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw',
    GOOGLE_CLIENT_ID: '480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com',
    ...
};
```

### For Production

1. Update Google OAuth Console with your domain
2. Update `OAUTH_REDIRECT_URI` in config.js
3. Consider using the backend proxy to hide API keys

## 🧪 Testing

### Test All Connections
```
http://localhost:8000/test-connection.html
```

Click "Run All Tests" to verify:
- ✅ EmailMCP service health
- ✅ API authentication
- ✅ User profile endpoint
- ✅ OAuth flow
- ✅ Email sending endpoint
- ✅ Analytics endpoint

### Manual Testing
See `TESTING.md` for 50+ detailed test scenarios.

## 🐛 Troubleshooting

### OAuth Redirect Error?
**Fix:** Add `http://localhost:8000/callback.html` to Google Cloud Console > Credentials > Authorized redirect URIs

### CORS Error?
**Fix:** Don't open the file directly. Use HTTP server (Python/Node.js)

### Gmail Won't Connect?
**Fix:** 
1. Check EmailMCP service is running
2. Verify API key in config.js
3. Try in incognito mode

### Email Not Sending?
**Fix:**
1. Ensure Gmail is connected (green status)
2. Check all required fields are filled
3. View browser console for errors

## 📚 Documentation

- **[sample-frontend/README.md](sample-frontend/README.md)** - Detailed documentation
- **[sample-frontend/TESTING.md](sample-frontend/TESTING.md)** - Complete testing guide
- **[sample-frontend/backend-proxy/README.md](sample-frontend/backend-proxy/README.md)** - Backend setup

## 🌐 Deployment

### Static Hosting (Easiest)

**Vercel:**
```bash
npm i -g vercel
cd sample-frontend
vercel --prod
```

**Netlify:**
```bash
npm i -g netlify-cli
cd sample-frontend
netlify deploy --prod --dir=.
```

**GitHub Pages:**
```bash
git subtree push --prefix sample-frontend origin gh-pages
```

### Docker

```bash
cd sample-frontend
docker build -t emailmcp-frontend .
docker run -p 8080:80 emailmcp-frontend
```

Open: http://localhost:8080

### With Backend Proxy (Hide API Key)

```bash
cd sample-frontend/backend-proxy
npm install
cp .env.example .env
# Edit .env with your settings
npm start
```

Then update `config.js`:
```javascript
USE_BACKEND_PROXY: true,
BACKEND_URL: 'http://localhost:3000/api'
```

## 🎓 How It Works

### Architecture
```
Frontend (Browser)
    ↓
Google OAuth Sign-In
    ↓
Gmail OAuth Flow → EmailMCP Service
    ↓
Send Emails via Gmail API
    ↓
View Analytics
```

### Key Files
- **index.html** - UI layout and structure
- **app.js** - All application logic
- **config.js** - Configuration management
- **callback.html** - Handles OAuth callbacks
- **style.css** - Responsive design

### API Endpoints Used
| Endpoint | Purpose |
|----------|---------|
| `/health` | Check service health |
| `/v1/oauth/authorize` | Start Gmail OAuth |
| `/v1/oauth/callback` | Complete OAuth |
| `/v1/users/{id}/profile` | Get user info |
| `/v1/users/{id}/messages` | Send email |
| `/v1/reports/users/{id}` | Get analytics |

## 🔐 Security Notes

### Current Setup
- API key is in frontend (OK for demo)
- OAuth tokens stored by EmailMCP service
- Session data in browser sessionStorage

### For Production
- Use backend proxy to hide API key
- Add your own authentication layer
- Implement rate limiting
- Use HTTPS

## 💡 Customization

### Change Colors
Edit `style.css`:
```css
:root {
    --primary-color: #4285f4;  /* Change this */
    --secondary-color: #34a853;
    ...
}
```

### Add Features
- Edit `app.js` for new functionality
- Add sections to `index.html`
- Style with `style.css`

### Use Your Own OAuth
Update `config.js` with your Google Client ID.

## 🎉 Features Showcase

### Google Sign-In
- One-click authentication
- Profile picture and name display
- Secure session management

### Gmail Integration
- Complete OAuth 2.0 flow
- Automatic token management
- Easy disconnect option

### Email Composer
- Send to multiple recipients
- CC and BCC support
- HTML or plain text
- Form validation
- Real-time feedback

### Analytics Dashboard
- Total emails sent
- Success rate percentage
- Interactive charts
- Recent email history

### Status Monitoring
- Real-time service checks
- Connection status indicators
- Automated testing

## 📞 Need Help?

1. Check `sample-frontend/README.md` for detailed docs
2. Review `sample-frontend/TESTING.md` for troubleshooting
3. Test with `test-connection.html`
4. Check browser console for errors
5. Verify EmailMCP service: https://emailmcp-hcnqp547xa-uc.a.run.app/docs

## ✨ Next Steps

1. **Test Locally** - Try all features
2. **Customize** - Update branding, colors
3. **Deploy** - Choose hosting platform
4. **Integrate** - Add to your application
5. **Scale** - Add more features

## 📊 Stats

- **Setup Time**: < 5 minutes
- **Lines of Code**: ~1,200
- **Dependencies**: 0 (frontend), 4 (backend)
- **Features**: 15+
- **Test Scenarios**: 50+

---

**Ready to start?** Run:
```bash
cd sample-frontend && python3 -m http.server 8000
```

Then open http://localhost:8000 🚀
