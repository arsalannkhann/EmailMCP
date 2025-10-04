# EmailMCP Simple Integration Guide

## Overview
Direct integration with EmailMCP service - no backend server, JWT tokens, or complex authentication needed!

## Environment Setup

Create `.env` file:
```bash
# ONLY THESE 2 VARIABLES NEEDED
REACT_APP_EMAILMCP_SERVICE_URL=https://emailmcp-hcnqp547xa-uc.a.run.app
REACT_APP_EMAILMCP_API_KEY=emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw
```

## Installation

```bash
npm install @react-oauth/google
```

## Core Components

### 1. User Login (Simple)

```javascript
// components/SimpleLogin.js
import React from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

const SimpleLogin = () => {
  const handleGoogleSuccess = (credentialResponse) => {
    // Simple user storage - no backend needed
    const userInfo = {
      id: `user_${Date.now()}`,
      email: 'user@example.com', // Decode from credentialResponse if needed
      name: 'User Name'
    };
    
    localStorage.setItem('user', JSON.stringify(userInfo));
    window.location.href = '/dashboard';
  };

  return (
    <GoogleOAuthProvider clientId="your-google-client-id">
      <div>
        <h2>Login to EmailMCP</h2>
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={() => console.log('Login Failed')}
        />
      </div>
    </GoogleOAuthProvider>
  );
};

export default SimpleLogin;
```

### 2. Gmail Connection

```javascript
// components/GmailConnection.js
import React, { useState, useEffect } from 'react';

const GmailConnection = () => {
  const [user, setUser] = useState(null);
  const [gmailConnected, setGmailConnected] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const userData = JSON.parse(localStorage.getItem('user') || '{}');
    setUser(userData);
  }, []);

  const connectGmail = async () => {
    setLoading(true);
    try {
      const userId = JSON.parse(localStorage.getItem('user'))?.id;
      
      const response = await fetch(`${process.env.REACT_APP_EMAILMCP_SERVICE_URL}/v1/oauth/authorize`, {
        method: 'POST',
        headers: {
          'Authorization': process.env.REACT_APP_EMAILMCP_API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          redirect_uri: `${window.location.origin}/gmail/callback`
        })
      });

      const result = await response.json();
      
      if (result.authorization_url) {
        // Redirect to Google OAuth
        window.location.href = result.authorization_url;
      }
    } catch (error) {
      console.error('Gmail connection error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>Gmail Connection</h3>
      {gmailConnected ? (
        <div>✅ Gmail Connected</div>
      ) : (
        <button onClick={connectGmail} disabled={loading}>
          {loading ? 'Connecting...' : 'Connect Gmail'}
        </button>
      )}
    </div>
  );
};

export default GmailConnection;
```

### 3. Email Composer

```javascript
// components/EmailComposer.js
import React, { useState } from 'react';

const EmailComposer = () => {
  const [email, setEmail] = useState({
    to: '',
    subject: '',
    body: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const sendEmail = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const userId = JSON.parse(localStorage.getItem('user'))?.id;
      
      const response = await fetch(`${process.env.REACT_APP_EMAILMCP_SERVICE_URL}/v1/users/${userId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': process.env.REACT_APP_EMAILMCP_API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to: [email.to],
          subject: email.subject,
          html_body: email.body,
          provider: 'gmail_api'
        })
      });

      const result = await response.json();
      
      if (result.status === 'sent') {
        setMessage('Email sent successfully!');
        setEmail({ to: '', subject: '', body: '' });
      } else {
        setMessage(`Failed to send: ${result.error}`);
      }
    } catch (error) {
      console.error('Send error:', error);
      setMessage('Failed to send email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>Send Email</h3>
      <form onSubmit={sendEmail}>
        <div>
          <input
            type="email"
            placeholder="To"
            value={email.to}
            onChange={(e) => setEmail({...email, to: e.target.value})}
            required
          />
        </div>
        <div>
          <input
            type="text"
            placeholder="Subject"
            value={email.subject}
            onChange={(e) => setEmail({...email, subject: e.target.value})}
            required
          />
        </div>
        <div>
          <textarea
            placeholder="Message"
            value={email.body}
            onChange={(e) => setEmail({...email, body: e.target.value})}
            rows="6"
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send Email'}
        </button>
      </form>
      {message && <div>{message}</div>}
    </div>
  );
};

export default EmailComposer;
```

### 4. Email Analytics

```javascript
// components/EmailAnalytics.js
import React, { useState, useEffect } from 'react';

const EmailAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const userId = JSON.parse(localStorage.getItem('user'))?.id;
      
      const response = await fetch(`${process.env.REACT_APP_EMAILMCP_SERVICE_URL}/v1/reports/users/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': process.env.REACT_APP_EMAILMCP_API_KEY,
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      setAnalytics(result);
    } catch (error) {
      console.error('Analytics error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading analytics...</div>;

  return (
    <div>
      <h3>Email Analytics</h3>
      {analytics && (
        <div>
          <p>Total Emails Sent: {analytics.total_emails_sent}</p>
          <p>Success Rate: {analytics.success_rate}%</p>
          <p>Gmail Connected: {analytics.gmail_connected ? 'Yes' : 'No'}</p>
        </div>
      )}
    </div>
  );
};

export default EmailAnalytics;
```

### 5. OAuth Callback Handler

```javascript
// components/GmailCallback.js
import React, { useEffect } from 'react';

const GmailCallback = () => {
  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state'); // This is the user_id
      
      if (code && state) {
        try {
          const response = await fetch(`${process.env.REACT_APP_EMAILMCP_SERVICE_URL}/v1/oauth/callback`, {
            method: 'POST',
            headers: {
              'Authorization': process.env.REACT_APP_EMAILMCP_API_KEY,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              code: code,
              user_id: state
            })
          });
          
          const result = await response.json();
          
          if (result.success) {
            // Update user data
            const userData = JSON.parse(localStorage.getItem('user') || '{}');
            userData.gmail_connected = true;
            userData.email_address = result.email_address;
            localStorage.setItem('user', JSON.stringify(userData));
            
            // Redirect to dashboard
            window.location.href = '/dashboard';
          }
        } catch (error) {
          console.error('Callback error:', error);
        }
      }
    };
    
    handleCallback();
  }, []);

  return <div>Processing Gmail connection...</div>;
};

export default GmailCallback;
```

## Main App Component

```javascript
// App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SimpleLogin from './components/SimpleLogin';
import GmailConnection from './components/GmailConnection';
import EmailComposer from './components/EmailComposer';
import EmailAnalytics from './components/EmailAnalytics';
import GmailCallback from './components/GmailCallback';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<SimpleLogin />} />
          <Route path="/dashboard" element={
            <div>
              <GmailConnection />
              <EmailComposer />
              <EmailAnalytics />
            </div>
          } />
          <Route path="/gmail/callback" element={<GmailCallback />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
```

## Key Points

✅ **What You Need:**
- EmailMCP API key: `emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw`
- Service URL: `https://emailmcp-hcnqp547xa-uc.a.run.app`
- Simple user ID (any string)

❌ **What You DON'T Need:**
- JWT tokens
- Backend authentication server
- Firestore database
- Complex user management

## How It Works

1. **User logs in** → Store simple user info in localStorage
2. **Connect Gmail** → EmailMCP handles OAuth with Google
3. **Send emails** → Direct API calls to EmailMCP
4. **View analytics** → Fetch data from EmailMCP

All Gmail OAuth tokens are automatically stored in GCP Secret Manager by EmailMCP!

## Testing

Test each endpoint directly:

```bash
# Test OAuth initiation
curl -X POST "https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/authorize" \
  -H "Authorization: emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "redirect_uri": "http://localhost:3000/gmail/callback"}'

# Test email sending (after Gmail connection)
curl -X POST "https://emailmcp-hcnqp547xa-uc.a.run.app/v1/users/test_user/messages" \
  -H "Authorization: emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw" \
  -H "Content-Type: application/json" \
  -d '{"to": ["test@example.com"], "subject": "Test", "html_body": "Hello!"}'
```

That's it! Simple, direct integration with EmailMCP.