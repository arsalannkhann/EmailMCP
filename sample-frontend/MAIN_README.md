# 📧 EmailMCP Sample Frontend - Complete Integration Guide

This is a **complete, production-ready sample frontend application** that demonstrates full integration with the EmailMCP multi-tenant email service. It includes Google OAuth authentication, Gmail integration, email sending, and analytics dashboard.

## 🎯 What's Included

### Frontend Application
- **Complete Single-Page App** with Google OAuth sign-in
- **Gmail OAuth Integration** with full OAuth flow
- **Email Composer** with HTML support, CC, BCC
- **Analytics Dashboard** with charts and statistics
- **Real-time Status Checks** for all services
- **Responsive Design** for mobile, tablet, and desktop
- **Production Ready** - No build step required

### Backend Proxy (Optional)
- **Express.js proxy server** to hide API keys
- **CORS Configuration** for frontend integration
- **Request logging and error handling**
- **Ready to deploy** to Heroku, AWS, GCP, or Docker

### Testing & Documentation
- **Connection testing utility** to validate all endpoints
- **Comprehensive testing guide** with 50+ test scenarios
- **Deployment guides** for multiple platforms
- **API integration examples**

## 🚀 Quick Start (2 Minutes)

### Step 1: Navigate to Directory
```bash
cd sample-frontend
```

### Step 2: Start Server

**Option A: Python (Recommended)**
```bash
python3 -m http.server 8000
```

**Option B: Node.js**
```bash
npx http-server -p 8000
```

**Option C: Use Setup Script**
```bash
./setup.sh
```

### Step 3: Open in Browser
```
http://localhost:8000
```

### Step 4: Test the Application
1. Click "Sign in with Google"
2. Click "Connect Gmail Account"
3. Send a test email!

## 📁 Project Structure

```
sample-frontend/
│
├── index.html              # Main application page
├── callback.html          # OAuth callback handler
├── test-connection.html   # Connection testing utility
│
├── config.js             # Configuration (API keys, URLs)
├── app.js                # Main application logic
├── style.css             # Styles and responsive design
│
├── README.md             # This file
├── TESTING.md            # Comprehensive testing guide
├── setup.sh              # Interactive setup script
├── Dockerfile            # Docker deployment config
│
└── backend-proxy/        # Optional backend server
    ├── server.js         # Express.js proxy server
    ├── package.json      # Node.js dependencies
    ├── .env.example      # Environment variables template
    └── README.md         # Backend setup guide
```

## ⚙️ Configuration

All configuration is centralized in `config.js`:

```javascript
const CONFIG = {
    // EmailMCP Service (Production)
    EMAILMCP_SERVICE_URL: 'https://emailmcp-hcnqp547xa-uc.a.run.app',
    EMAILMCP_API_KEY: 'emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw',
    
    // Google OAuth
    GOOGLE_CLIENT_ID: '480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com',
    
    // OAuth Callback URL
    OAUTH_REDIRECT_URI: window.location.origin + '/callback.html',
    
    // Optional: Use backend proxy to hide API key
    USE_BACKEND_PROXY: false,
    BACKEND_URL: null,
};
```

### For Production Deployment

1. **Update Google OAuth Console:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Add your production domain to Authorized JavaScript origins
   - Add `https://yourdomain.com/callback.html` to Authorized redirect URIs

2. **Update `config.js`:**
   ```javascript
   OAUTH_REDIRECT_URI: 'https://yourdomain.com/callback.html'
   ```

3. **Consider using backend proxy** to hide API key from frontend

## 🎯 Features Demonstrated

### 1. Google OAuth Authentication
- Sign in with Google
- Session persistence
- Secure logout
- User profile display

### 2. Gmail OAuth Integration  
- Initiate OAuth flow
- Handle callback
- Store credentials securely (via EmailMCP)
- Disconnect Gmail

### 3. Email Sending
- Send to multiple recipients
- CC and BCC support
- HTML and plain text
- Form validation
- Success/error notifications

### 4. Email Analytics
- Total emails sent
- Success rate percentage
- Daily activity chart
- Recent emails list
- Real-time updates

### 5. Connection Testing
- Service health checks
- Gmail connection status
- Real-time status indicators
- Comprehensive test utility

## 🔧 Development Guide

### Running Locally

```bash
# Navigate to directory
cd sample-frontend

# Start development server
python3 -m http.server 8000

# Open browser
open http://localhost:8000
```

### Using Backend Proxy (Optional)

If you want to hide the API key from the frontend:

```bash
# Setup backend
cd backend-proxy
npm install
cp .env.example .env
# Edit .env with your settings

# Start backend
npm run dev

# In config.js, set:
USE_BACKEND_PROXY: true
BACKEND_URL: 'http://localhost:3000/api'
```

### Testing

```bash
# Open connection tester
open http://localhost:8000/test-connection.html

# Or run comprehensive tests
# See TESTING.md for full test suite
```

## 📚 Documentation

- **[README.md](README.md)** - Main documentation (this file)
- **[TESTING.md](TESTING.md)** - Complete testing guide with 50+ scenarios
- **[backend-proxy/README.md](backend-proxy/README.md)** - Backend proxy setup and deployment

## 🌐 Deployment Options

### Static Hosting (Frontend Only)

**Vercel:**
```bash
npm i -g vercel
vercel --prod
```

**Netlify:**
```bash
npm i -g netlify-cli  
netlify deploy --prod --dir=.
```

**GitHub Pages:**
```bash
git subtree push --prefix sample-frontend origin gh-pages
```

**AWS S3:**
```bash
aws s3 sync . s3://your-bucket-name --acl public-read
```

### Docker Deployment

```bash
# Build image
docker build -t emailmcp-frontend .

# Run container
docker run -p 8080:80 emailmcp-frontend
```

### Backend Proxy Deployment

See [backend-proxy/README.md](backend-proxy/README.md) for:
- Heroku deployment
- Google Cloud Run
- AWS Elastic Beanstalk
- Docker deployment

## 🔐 Security Considerations

### API Key Protection
- **Current Setup**: API key is exposed in frontend (acceptable for demo)
- **Production**: Use backend proxy to hide API key
- **Alternative**: Implement your own authentication layer

### OAuth Security
- OAuth tokens stored securely by EmailMCP service
- Tokens never exposed to frontend
- User can revoke access anytime

### Session Management
- User data in `sessionStorage` (clears on browser close)
- No sensitive data in `localStorage`
- Logout clears all session data

### CORS
- EmailMCP service has CORS enabled
- Configure `FRONTEND_URL` in backend proxy
- Use HTTPS in production

## 🧪 Testing the Integration

### Manual Testing
1. Open `http://localhost:8000/test-connection.html`
2. Click "Run All Tests"
3. Verify all tests pass or show expected warnings

### Test Scenarios
See [TESTING.md](TESTING.md) for:
- 50+ test scenarios
- Step-by-step testing guide
- Expected results
- Troubleshooting tips

### Key Tests
- ✅ Google sign-in works
- ✅ Gmail OAuth flow completes
- ✅ Emails send successfully
- ✅ Analytics update correctly
- ✅ All status checks pass

## 🐛 Troubleshooting

### OAuth Redirect URI Mismatch
**Symptom:** Error during Google OAuth  
**Solution:**
1. Go to Google Cloud Console > Credentials
2. Add your exact callback URL to Authorized redirect URIs
3. Format: `http://localhost:8000/callback.html`

### CORS Errors
**Symptom:** Network errors in console  
**Solution:**
- Don't open `index.html` directly as `file://`
- Use HTTP server (Python/Node.js)
- Check CORS settings if using backend proxy

### Gmail Won't Connect
**Symptom:** OAuth flow fails  
**Solution:**
1. Verify EmailMCP service is running
2. Check API key in `config.js`
3. Clear browser cache/cookies
4. Try in incognito mode

### Email Send Fails
**Symptom:** "User not connected" error  
**Solution:**
1. Ensure Gmail connection status is green
2. Reconnect Gmail if needed
3. Check all required form fields
4. Review browser console for errors

### Service Unreachable
**Symptom:** Connection tests fail  
**Solution:**
1. Verify EmailMCP service URL
2. Check internet connection
3. Test: `curl https://emailmcp-hcnqp547xa-uc.a.run.app/health`
4. Check API key is correct

## 📞 Getting Help

### Resources
- **API Documentation**: https://emailmcp-hcnqp547xa-uc.a.run.app/docs
- **Testing Guide**: [TESTING.md](TESTING.md)
- **Backend Setup**: [backend-proxy/README.md](backend-proxy/README.md)

### Common Questions

**Q: Do I need a backend server?**  
A: No, the frontend works directly with EmailMCP. Use backend proxy only if you want to hide the API key.

**Q: Can I customize the UI?**  
A: Yes! All styles are in `style.css`. Modify as needed.

**Q: Is this production-ready?**  
A: Yes, but consider:
- Using backend proxy for API key security
- Adding your own authentication
- Implementing rate limiting
- Customizing error handling

**Q: How do I add my own users?**  
A: Each Google user automatically gets a unique user ID (`user_{google_sub}`). EmailMCP creates user profiles automatically on first OAuth.

**Q: Can I use my own Gmail credentials?**  
A: Yes! Just update `GOOGLE_CLIENT_ID` in `config.js` with your own Google OAuth credentials.

## 🎓 Learning Resources

### Understanding the Code
- **index.html**: UI structure and layout
- **app.js**: Application logic and API calls
- **config.js**: Configuration management
- **style.css**: Responsive design and styling

### Key Concepts
- Google OAuth 2.0 flow
- RESTful API integration
- Session management
- Async/await patterns
- Error handling
- Chart.js for visualizations

## 🤝 Contributing

This is a sample/reference implementation. Feel free to:
- Fork and modify for your needs
- Submit improvements
- Share feedback
- Report issues

## 📝 License

This sample frontend is provided as-is for integration and reference purposes.

## 🎉 Next Steps

1. **Test Locally**
   - Run the application
   - Sign in with Google
   - Connect Gmail
   - Send test emails

2. **Customize**
   - Update branding and colors
   - Add your own features
   - Modify email templates
   - Integrate with your app

3. **Deploy**
   - Choose hosting platform
   - Configure production URLs
   - Set up backend proxy (optional)
   - Monitor and test

4. **Scale**
   - Add user management
   - Implement rate limiting
   - Add more features
   - Monitor usage

## 📊 Project Stats

- **Files**: 12 core files
- **Lines of Code**: ~1,200 (JavaScript, HTML, CSS)
- **Dependencies**: None (frontend), 4 (backend)
- **Features**: 15+ implemented
- **Test Scenarios**: 50+
- **Documentation Pages**: 3

## 🌟 Highlights

✅ **Zero Build Required** - Pure HTML/CSS/JS  
✅ **Complete OAuth Flow** - Google + Gmail integration  
✅ **Production Ready** - Error handling, loading states  
✅ **Well Documented** - Code comments, guides, tests  
✅ **Responsive Design** - Works on all devices  
✅ **Easy to Deploy** - Multiple deployment options  
✅ **Extensible** - Clean code, easy to customize  

---

**Ready to get started?** Run `./setup.sh` or `python3 -m http.server 8000`!
