# EmailMCP Sample Frontend Integration

A complete, production-ready sample frontend application demonstrating full integration with EmailMCP service including Google OAuth authentication, email sending, and analytics.

## 🎯 Features

- ✅ **Google OAuth Sign-In** - User authentication with Google
- ✅ **Gmail OAuth Integration** - Complete OAuth flow for Gmail API access
- ✅ **Connection Testing** - Real-time status checks for all services
- ✅ **Email Sending** - Full-featured email composer with HTML support, CC, BCC
- ✅ **Email Analytics** - Dashboard with charts and statistics
- ✅ **Recent Emails** - View email history with status
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile
- ✅ **Real-time Notifications** - User feedback for all actions

## 📁 File Structure

```
sample-frontend/
├── index.html          # Main application page
├── callback.html       # OAuth callback handler
├── config.js          # Configuration file
├── app.js             # Main application logic
├── style.css          # Styles and responsive design
├── README.md          # This file
└── test-connection.html # Connection testing utility
```

## 🚀 Quick Start

### Option 1: Serve with Python

```bash
cd sample-frontend
python3 -m http.server 8000
```

Then open: http://localhost:8000

### Option 2: Serve with Node.js

```bash
cd sample-frontend
npx http-server -p 8000
```

Then open: http://localhost:8000

### Option 3: Open Directly in Browser

You can also open `index.html` directly in your browser, though some browsers may restrict OAuth callbacks.

## ⚙️ Configuration

All configuration is in `config.js`:

```javascript
const CONFIG = {
    // EmailMCP Service (Production)
    EMAILMCP_SERVICE_URL: 'https://emailmcp-hcnqp547xa-uc.a.run.app',
    EMAILMCP_API_KEY: 'emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw',
    
    // Google OAuth
    GOOGLE_CLIENT_ID: '480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com',
    
    // OAuth Callback
    OAUTH_REDIRECT_URI: window.location.origin + '/callback.html',
};
```

### For Production Deployment

1. **Update Google OAuth Settings**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to APIs & Services > Credentials
   - Add your production domain to Authorized JavaScript origins
   - Add `https://yourdomain.com/callback.html` to Authorized redirect URIs

2. **Update `config.js`**:
   ```javascript
   OAUTH_REDIRECT_URI: 'https://yourdomain.com/callback.html'
   ```

## 📖 How to Use

### 1. Sign In with Google

1. Open the application
2. Click "Sign in with Google"
3. Select your Google account
4. You'll be signed into the app

### 2. Connect Gmail

1. After signing in, you'll see the Gmail Integration section
2. Click "Connect Gmail Account"
3. You'll be redirected to Google's OAuth consent screen
4. Grant permissions to send emails
5. You'll be redirected back to the app
6. Gmail connection status will update to "Connected"

### 3. Send an Email

1. Navigate to the "Compose Email" section
2. Fill in:
   - **To**: Recipient email(s) (comma-separated for multiple)
   - **CC/BCC**: Optional carbon copies
   - **Subject**: Email subject line
   - **Message**: Email body
   - **Send as HTML**: Check to enable HTML formatting
3. Click "Send Email"
4. Wait for confirmation notification

### 4. View Analytics

The analytics section automatically updates and shows:
- Total emails sent
- Success rate
- Failed emails count
- Email activity chart over time
- Recent email history

### 5. Test Connections

Click "Test All Connections" to verify:
- EmailMCP service availability
- Gmail connection status
- Backend server status (if using proxy)

## 🔧 API Integration Details

### Authentication Flow

```
1. User signs in with Google OAuth
   ↓
2. App stores user info in session
   ↓
3. User initiates Gmail connection
   ↓
4. App calls POST /v1/oauth/authorize
   ↓
5. User redirected to Google OAuth
   ↓
6. Google redirects to /callback.html with code
   ↓
7. Callback page calls POST /v1/oauth/callback
   ↓
8. EmailMCP stores Gmail tokens
   ↓
9. User can now send emails
```

### Email Sending Flow

```
1. User composes email in UI
   ↓
2. App calls POST /v1/users/{user_id}/messages
   ↓
3. EmailMCP validates user has Gmail connected
   ↓
4. EmailMCP sends email via Gmail API
   ↓
5. Returns message_id and thread_id
   ↓
6. App shows success notification
   ↓
7. Analytics automatically refresh
```

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check service health |
| `/v1/oauth/authorize` | POST | Initiate Gmail OAuth |
| `/v1/oauth/callback` | POST | Complete Gmail OAuth |
| `/v1/users/{id}/profile` | GET | Get user profile & status |
| `/v1/users/{id}/messages` | POST | Send email |
| `/v1/users/{id}/gmail` | DELETE | Disconnect Gmail |
| `/v1/reports/users/{id}` | GET | Get email analytics |

## 🔐 Security Considerations

### API Key Protection
- The API key is exposed in the frontend (in `config.js`)
- For production, consider using a backend proxy to hide the API key
- Set `USE_BACKEND_PROXY: true` in config.js if using a backend

### User Data
- User data is stored in browser `sessionStorage`
- Data is cleared when the browser session ends
- No sensitive data is persisted in localStorage

### OAuth Tokens
- OAuth tokens are stored securely by EmailMCP service
- Tokens are never exposed to the frontend
- Tokens can be revoked by disconnecting Gmail

## 🧪 Testing

### Manual Testing Checklist

- [ ] Sign in with Google works
- [ ] User profile displays correctly
- [ ] Connection tests show correct status
- [ ] Gmail OAuth flow completes successfully
- [ ] Email sends with all fields (to, cc, bcc, subject, body)
- [ ] HTML emails send correctly
- [ ] Analytics display after sending emails
- [ ] Recent emails list updates
- [ ] Notifications appear for all actions
- [ ] Disconnect Gmail works
- [ ] Logout clears session
- [ ] Responsive design works on mobile

### Connection Testing

Use the included `test-connection.html` page to test:
- EmailMCP service availability
- API authentication
- Gmail OAuth flow
- Email sending
- Analytics retrieval

## 🌐 Deployment Options

### Static Hosting

Deploy to any static hosting service:

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
# Push to gh-pages branch
git subtree push --prefix sample-frontend origin gh-pages
```

### Docker

Create a `Dockerfile`:
```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t emailmcp-frontend .
docker run -p 8080:80 emailmcp-frontend
```

## 🐛 Troubleshooting

### OAuth Callback Fails

**Problem**: Redirect URI mismatch error

**Solution**: 
1. Check Google Cloud Console > Credentials
2. Ensure callback URL matches exactly: `http://localhost:8000/callback.html`
3. Update `config.js` if needed

### Gmail Not Connecting

**Problem**: OAuth flow starts but doesn't complete

**Solution**:
1. Check browser console for errors
2. Verify EmailMCP service is running: `curl https://emailmcp-hcnqp547xa-uc.a.run.app/health`
3. Check API key is correct in `config.js`

### Email Send Fails

**Problem**: "User not connected" error

**Solution**:
1. Verify Gmail is connected in the app
2. Try disconnecting and reconnecting Gmail
3. Check user profile endpoint shows `gmail_connected: true`

### CORS Errors

**Problem**: CORS policy blocks requests

**Solution**:
1. Serve the app via HTTP server (not file://)
2. Use Python or Node.js http server
3. Or deploy to a proper hosting service

## 📚 Additional Resources

- [EmailMCP API Documentation](https://emailmcp-hcnqp547xa-uc.a.run.app/docs)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Reference](https://developers.google.com/gmail/api)

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review EmailMCP service logs
3. Check browser console for errors
4. Verify all configuration settings

## 📝 License

This sample frontend is provided as-is for integration purposes.
