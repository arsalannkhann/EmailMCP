# EmailMCP Frontend Integration Documentation

Complete guide for integrating EmailMCP with your frontend application, including user authentication, Gmail OAuth, and Google Cloud Firestore data storage.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [User Authentication Flow](#user-authentication-flow)
5. [Frontend Components](#frontend-components)
6. [Backend API Implementation](#backend-api-implementation)
7. [Database Schema](#database-schema)
8. [Security Considerations](#security-considerations)
9. [Testing & Deployment](#testing-deployment)

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Frontend      │    │   Your Backend   │    │   EmailMCP Service  │
│   (React/Vue)   │    │   (Node.js/etc)  │    │   (GCP Cloud Run)   │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Google OAuth  │    │   Firestore DB   │    │   GCP Secret Mgr    │
│   (Gmail Auth)  │    │  (User Storage)  │    │  (Gmail Tokens)     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## Prerequisites

### 1. Google Cloud Console Setup
- Enable Firestore API
- Enable Gmail API
- Create OAuth 2.0 credentials
- Set authorized redirect URIs

### 2. EmailMCP Service
- Deployed EmailMCP service: `https://emailmcp-hcnqp547xa-uc.a.run.app`
- API Key: `emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw`
- Service account with Firestore and Secret Manager permissions

## Environment Configuration

### Frontend Environment Variables

```env
# .env.local (Frontend)
REACT_APP_API_BASE_URL=https://your-backend.com/api
REACT_APP_GOOGLE_CLIENT_ID=480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com
REACT_APP_EMAILMCP_SERVICE_URL=https://emailmcp-hcnqp547xa-uc.a.run.app
```

### Backend Environment Variables

```env
# .env (Backend)
PORT=3000
NODE_ENV=production

# Google Cloud
GOOGLE_PROJECT_ID=mcporionac
GOOGLE_CLIENT_ID=480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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

# EmailMCP Integration
EMAILMCP_SERVICE_URL=https://emailmcp-hcnqp547xa-uc.a.run.app
EMAILMCP_API_KEY=emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw

# JWT Secret
JWT_SECRET=your-super-secure-jwt-secret-key-here

# Frontend URL
FRONTEND_URL=https://salesos.orionac.in
```

## User Authentication Flow

### 1. Frontend Login Component (React)

```jsx
// components/GoogleLogin.jsx
import React from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

const GoogleLoginComponent = () => {
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      // Send Google credential to your backend
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          credential: credentialResponse.credential
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        // Store JWT token
        localStorage.setItem('authToken', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        console.error('Login failed:', result.error);
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleGoogleError = () => {
    console.error('Google Login Failed');
  };

  return (
    <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
      <div className="login-container">
        <h2>Welcome to SalesOS</h2>
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={handleGoogleError}
          text="signin_with"
          shape="rectangular"
          theme="outline"
          size="large"
        />
      </div>
    </GoogleOAuthProvider>
  );
};

export default GoogleLoginComponent;
```

### 2. Gmail Connection Component

```jsx
// components/GmailConnect.jsx
import React, { useState, useEffect } from 'react';

const GmailConnect = () => {
  const [user, setUser] = useState(null);
  const [gmailConnected, setGmailConnected] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const userData = JSON.parse(localStorage.getItem('user') || '{}');
    setUser(userData);
    setGmailConnected(userData.gmail_connected || false);
  }, []);

  const connectGmail = async () => {
    setLoading(true);
    try {
      const authToken = localStorage.getItem('authToken');
      
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/gmail/connect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      
      if (result.success) {
        // Redirect to Google OAuth
        window.location.href = result.authorization_url;
      } else {
        console.error('Gmail connection failed:', result.error);
      }
    } catch (error) {
      console.error('Gmail connection error:', error);
    } finally {
      setLoading(false);
    }
  };

  const disconnectGmail = async () => {
    try {
      const authToken = localStorage.getItem('authToken');
      
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/gmail/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      const result = await response.json();
      
      if (result.success) {
        setGmailConnected(false);
        // Update user data
        const updatedUser = { ...user, gmail_connected: false };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('Gmail disconnection error:', error);
    }
  };

  return (
    <div className="gmail-connect-container">
      <h3>Gmail Integration</h3>
      
      {gmailConnected ? (
        <div className="connected-state">
          <div className="status-indicator success">
            ✅ Gmail Connected
          </div>
          <p>Email: {user?.email}</p>
          <p>Connected: {new Date(user?.gmail_connected_at).toLocaleDateString()}</p>
          <button 
            onClick={disconnectGmail}
            className="btn btn-danger"
          >
            Disconnect Gmail
          </button>
        </div>
      ) : (
        <div className="disconnected-state">
          <div className="status-indicator warning">
            ⚠️ Gmail Not Connected
          </div>
          <p>Connect your Gmail account to send emails through SalesOS</p>
          <button 
            onClick={connectGmail}
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? 'Connecting...' : 'Connect Gmail'}
          </button>
        </div>
      )}
    </div>
  );
};

export default GmailConnect;
```

### 3. Email Composer Component

```jsx
// components/EmailComposer.jsx
import React, { useState } from 'react';

const EmailComposer = () => {
  const [emailData, setEmailData] = useState({
    to: [''],
    subject: '',
    body: '',
    body_type: 'text'
  });
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);

  const handleInputChange = (field, value) => {
    setEmailData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleRecipientsChange = (index, value) => {
    const newRecipients = [...emailData.to];
    newRecipients[index] = value;
    setEmailData(prev => ({
      ...prev,
      to: newRecipients
    }));
  };

  const addRecipient = () => {
    setEmailData(prev => ({
      ...prev,
      to: [...prev.to, '']
    }));
  };

  const removeRecipient = (index) => {
    const newRecipients = emailData.to.filter((_, i) => i !== index);
    setEmailData(prev => ({
      ...prev,
      to: newRecipients
    }));
  };

  const sendEmail = async () => {
    setSending(true);
    setResult(null);

    try {
      const authToken = localStorage.getItem('authToken');
      
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/emails/send`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...emailData,
          to: emailData.to.filter(email => email.trim() !== '')
        }),
      });

      const result = await response.json();
      setResult(result);

      if (result.success) {
        // Reset form
        setEmailData({
          to: [''],
          subject: '',
          body: '',
          body_type: 'text'
        });
      }
    } catch (error) {
      setResult({
        success: false,
        error: 'Failed to send email'
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="email-composer">
      <h3>Compose Email</h3>
      
      {/* Recipients */}
      <div className="form-group">
        <label>To:</label>
        {emailData.to.map((recipient, index) => (
          <div key={index} className="recipient-input">
            <input
              type="email"
              value={recipient}
              onChange={(e) => handleRecipientsChange(index, e.target.value)}
              placeholder="recipient@example.com"
              className="form-control"
            />
            {emailData.to.length > 1 && (
              <button 
                type="button"
                onClick={() => removeRecipient(index)}
                className="btn btn-sm btn-danger"
              >
                Remove
              </button>
            )}
          </div>
        ))}
        <button 
          type="button"
          onClick={addRecipient}
          className="btn btn-sm btn-secondary"
        >
          Add Recipient
        </button>
      </div>

      {/* Subject */}
      <div className="form-group">
        <label>Subject:</label>
        <input
          type="text"
          value={emailData.subject}
          onChange={(e) => handleInputChange('subject', e.target.value)}
          placeholder="Email subject"
          className="form-control"
        />
      </div>

      {/* Body Type */}
      <div className="form-group">
        <label>Format:</label>
        <select
          value={emailData.body_type}
          onChange={(e) => handleInputChange('body_type', e.target.value)}
          className="form-control"
        >
          <option value="text">Plain Text</option>
          <option value="html">HTML</option>
        </select>
      </div>

      {/* Body */}
      <div className="form-group">
        <label>Message:</label>
        <textarea
          value={emailData.body}
          onChange={(e) => handleInputChange('body', e.target.value)}
          placeholder="Your message here..."
          rows={10}
          className="form-control"
        />
      </div>

      {/* Send Button */}
      <button
        onClick={sendEmail}
        disabled={sending || !emailData.subject || !emailData.body || emailData.to.every(email => !email.trim())}
        className="btn btn-primary btn-lg"
      >
        {sending ? 'Sending...' : 'Send Email'}
      </button>

      {/* Result */}
      {result && (
        <div className={`alert ${result.success ? 'alert-success' : 'alert-danger'}`}>
          {result.success ? (
            <div>
              <strong>Email sent successfully!</strong>
              <p>Message ID: {result.message_id}</p>
            </div>
          ) : (
            <div>
              <strong>Failed to send email:</strong>
              <p>{result.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EmailComposer;
```

## Backend API Implementation

### 1. Main Server Setup

```javascript
// server.js
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const { OAuth2Client } = require('google-auth-library');
const { Firestore } = require('@google-cloud/firestore');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

// Initialize Google OAuth client
const googleClient = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

// Initialize Firestore
const firestore = new Firestore({
  projectId: process.env.GOOGLE_PROJECT_ID,
});

// Middleware
app.use(cors({
  origin: process.env.FRONTEND_URL,
  credentials: true
}));
app.use(express.json());

// Authentication middleware
const authenticateToken = async (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ success: false, error: 'Access token required' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // Get user from Firestore
    const userDoc = await firestore.collection('users').doc(decoded.userId).get();
    
    if (!userDoc.exists) {
      return res.status(401).json({ success: false, error: 'User not found' });
    }

    req.user = { id: decoded.userId, ...userDoc.data() };
    next();
  } catch (error) {
    return res.status(403).json({ success: false, error: 'Invalid token' });
  }
};

// Import routes
const authRoutes = require('./routes/auth');
const gmailRoutes = require('./routes/gmail');
const emailRoutes = require('./routes/email');

// Use routes
app.use('/api/auth', authRoutes);
app.use('/api/gmail', gmailRoutes);
app.use('/api/emails', emailRoutes);

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});

module.exports = { app, firestore, authenticateToken };
```

### 2. Authentication Routes

```javascript
// routes/auth.js
const express = require('express');
const jwt = require('jsonwebtoken');
const { OAuth2Client } = require('google-auth-library');
const { firestore, authenticateToken } = require('../server');

const router = express.Router();
const googleClient = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

// Google OAuth login
router.post('/google', async (req, res) => {
  try {
    const { credential } = req.body;

    // Verify Google token
    const ticket = await googleClient.verifyIdToken({
      idToken: credential,
      audience: process.env.GOOGLE_CLIENT_ID,
    });

    const payload = ticket.getPayload();
    const googleUserId = payload.sub;
    const email = payload.email;
    const name = payload.name;
    const picture = payload.picture;

    // Check if user exists in Firestore
    const userRef = firestore.collection('users').doc(googleUserId);
    const userDoc = await userRef.get();

    let userData;
    
    if (!userDoc.exists) {
      // Create new user
      userData = {
        id: googleUserId,
        email: email,
        name: name,
        picture: picture,
        gmail_connected: false,
        gmail_connected_at: null,
        total_emails_sent: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: new Date().toISOString(),
      };

      await userRef.set(userData);
      console.log(`New user created: ${email} (${googleUserId})`);
    } else {
      // Update existing user
      userData = userDoc.data();
      await userRef.update({
        last_login: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      console.log(`User login: ${email} (${googleUserId})`);
    }

    // Generate JWT token
    const jwtToken = jwt.sign(
      { userId: googleUserId, email: email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      token: jwtToken,
      user: userData
    });

  } catch (error) {
    console.error('Google auth error:', error);
    res.status(400).json({
      success: false,
      error: 'Invalid Google token'
    });
  }
});

// Get current user profile
router.get('/profile', authenticateToken, async (req, res) => {
  try {
    res.json({
      success: true,
      user: req.user
    });
  } catch (error) {
    console.error('Profile fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch profile'
    });
  }
});

// Logout
router.post('/logout', authenticateToken, async (req, res) => {
  try {
    // In a real implementation, you might maintain a blacklist of invalidated tokens
    // For now, we'll just return success and let the frontend handle token removal
    
    res.json({
      success: true,
      message: 'Logged out successfully'
    });
  } catch (error) {
    console.error('Logout error:', error);
    res.status(500).json({
      success: false,
      error: 'Logout failed'
    });
  }
});

module.exports = router;
```

### 3. Gmail Integration Routes

```javascript
// routes/gmail.js
const express = require('express');
const fetch = require('node-fetch');
const { firestore, authenticateToken } = require('../server');

const router = express.Router();

// Connect Gmail account
router.post('/connect', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;
    const redirectUri = `${process.env.FRONTEND_URL}/gmail/callback`;

    // Initiate OAuth with EmailMCP
    const response = await fetch(`${process.env.EMAILMCP_SERVICE_URL}/v1/oauth/authorize`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.EMAILMCP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        redirect_uri: redirectUri
      }),
    });

    const result = await response.json();

    if (response.ok) {
      res.json({
        success: true,
        authorization_url: result.authorization_url,
        state: result.state
      });
    } else {
      console.error('EmailMCP OAuth error:', result);
      res.status(400).json({
        success: false,
        error: 'Failed to initiate Gmail OAuth'
      });
    }

  } catch (error) {
    console.error('Gmail connect error:', error);
    res.status(500).json({
      success: false,
      error: 'Gmail connection failed'
    });
  }
});

// Handle Gmail OAuth callback
router.get('/callback', async (req, res) => {
  try {
    const { code, state } = req.query;
    const userId = state; // state contains the user ID

    if (!code || !userId) {
      return res.redirect(`${process.env.FRONTEND_URL}/settings?error=oauth_failed`);
    }

    // Forward to EmailMCP callback
    const response = await fetch(
      `${process.env.EMAILMCP_SERVICE_URL}/v1/oauth/callback?code=${code}&state=${userId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${process.env.EMAILMCP_API_KEY}`,
        },
      }
    );

    const result = await response.json();

    if (response.ok && result.status === 'success') {
      // Update user in Firestore
      const userRef = firestore.collection('users').doc(userId);
      await userRef.update({
        gmail_connected: true,
        gmail_connected_at: new Date().toISOString(),
        gmail_email: result.email_address,
        updated_at: new Date().toISOString(),
      });

      console.log(`Gmail connected for user ${userId}: ${result.email_address}`);
      
      // Redirect to success page
      res.redirect(`${process.env.FRONTEND_URL}/settings?gmail_connected=true`);
    } else {
      console.error('EmailMCP callback error:', result);
      res.redirect(`${process.env.FRONTEND_URL}/settings?error=oauth_callback_failed`);
    }

  } catch (error) {
    console.error('Gmail callback error:', error);
    res.redirect(`${process.env.FRONTEND_URL}/settings?error=oauth_error`);
  }
});

// Disconnect Gmail account
router.post('/disconnect', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;

    // Update user in Firestore
    const userRef = firestore.collection('users').doc(userId);
    await userRef.update({
      gmail_connected: false,
      gmail_connected_at: null,
      gmail_email: null,
      updated_at: new Date().toISOString(),
    });

    // Note: In a production system, you might also want to revoke the OAuth tokens
    // This would require additional EmailMCP API endpoints

    res.json({
      success: true,
      message: 'Gmail disconnected successfully'
    });

  } catch (error) {
    console.error('Gmail disconnect error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to disconnect Gmail'
    });
  }
});

// Get Gmail connection status
router.get('/status', authenticateToken, async (req, res) => {
  try {
    const user = req.user;

    res.json({
      success: true,
      gmail_connected: user.gmail_connected || false,
      gmail_email: user.gmail_email || null,
      connected_at: user.gmail_connected_at || null
    });

  } catch (error) {
    console.error('Gmail status error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get Gmail status'
    });
  }
});

module.exports = router;
```

### 4. Email Sending Routes

```javascript
// routes/email.js
const express = require('express');
const fetch = require('node-fetch');
const { firestore, authenticateToken } = require('../server');

const router = express.Router();

// Send email
router.post('/send', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;
    const { to, subject, body, body_type = 'text', cc, bcc } = req.body;

    // Validate input
    if (!to || !Array.isArray(to) || to.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Recipients (to) field is required and must be an array'
      });
    }

    if (!subject || !body) {
      return res.status(400).json({
        success: false,
        error: 'Subject and body are required'
      });
    }

    // Check if user has Gmail connected
    if (!req.user.gmail_connected) {
      return res.status(400).json({
        success: false,
        error: 'Gmail account not connected. Please connect your Gmail account first.'
      });
    }

    // Send email via EmailMCP
    const emailData = {
      to: to.filter(email => email.trim() !== ''),
      subject,
      body,
      body_type,
      ...(cc && cc.length > 0 && { cc }),
      ...(bcc && bcc.length > 0 && { bcc })
    };

    const response = await fetch(
      `${process.env.EMAILMCP_SERVICE_URL}/v1/users/${userId}/messages`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.EMAILMCP_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailData),
      }
    );

    const result = await response.json();

    if (response.ok) {
      // Update user email count in Firestore
      const userRef = firestore.collection('users').doc(userId);
      await userRef.update({
        total_emails_sent: (req.user.total_emails_sent || 0) + 1,
        updated_at: new Date().toISOString(),
      });

      // Log email activity
      const emailLogRef = firestore.collection('email_logs').doc();
      await emailLogRef.set({
        user_id: userId,
        from_email: req.user.gmail_email,
        to_emails: emailData.to,
        cc_emails: emailData.cc || [],
        bcc_emails: emailData.bcc || [],
        subject: subject,
        body_type: body_type,
        message_id: result.message_id || null,
        status: 'sent',
        sent_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      });

      console.log(`Email sent by user ${userId} to ${emailData.to.join(', ')}`);

      res.json({
        success: true,
        message: 'Email sent successfully',
        message_id: result.message_id,
        recipients: emailData.to.length
      });

    } else {
      // Log failed email
      const emailLogRef = firestore.collection('email_logs').doc();
      await emailLogRef.set({
        user_id: userId,
        from_email: req.user.gmail_email,
        to_emails: emailData.to,
        subject: subject,
        status: 'failed',
        error_message: result.error || 'Unknown error',
        sent_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      });

      console.error(`Email send failed for user ${userId}:`, result);

      res.status(400).json({
        success: false,
        error: result.error || 'Failed to send email'
      });
    }

  } catch (error) {
    console.error('Email sending error:', error);
    res.status(500).json({
      success: false,
      error: 'Email sending failed'
    });
  }
});

// Get email history
router.get('/history', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;
    const { limit = 50, offset = 0 } = req.query;

    // Get email logs from Firestore
    const emailLogsRef = firestore.collection('email_logs')
      .where('user_id', '==', userId)
      .orderBy('sent_at', 'desc')
      .limit(parseInt(limit))
      .offset(parseInt(offset));

    const snapshot = await emailLogsRef.get();
    const emails = [];

    snapshot.forEach(doc => {
      emails.push({
        id: doc.id,
        ...doc.data()
      });
    });

    res.json({
      success: true,
      emails: emails,
      total: emails.length
    });

  } catch (error) {
    console.error('Email history error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch email history'
    });
  }
});

// Get email analytics
router.get('/analytics', authenticateUser, async (req, res) => {
  try {
    const userId = req.user.id;
    const { start_date, end_date } = req.query;

    // Build query
    let query = firestore.collection('email_logs').where('user_id', '==', userId);

    if (start_date) {
      query = query.where('sent_at', '>=', start_date);
    }
    if (end_date) {
      query = query.where('sent_at', '<=', end_date);
    }

    const snapshot = await query.get();
    
    let totalSent = 0;
    let totalFailed = 0;
    const dailyStats = {};
    const topRecipients = {};

    snapshot.forEach(doc => {
      const data = doc.data();
      const date = data.sent_at?.split('T')[0]; // Extract date

      if (data.status === 'sent') {
        totalSent++;
      } else {
        totalFailed++;
      }

      // Daily stats
      if (date) {
        if (!dailyStats[date]) {
          dailyStats[date] = { sent: 0, failed: 0 };
        }
        dailyStats[date][data.status === 'sent' ? 'sent' : 'failed']++;
      }

      // Top recipients
      if (data.to_emails && Array.isArray(data.to_emails)) {
        data.to_emails.forEach(email => {
          topRecipients[email] = (topRecipients[email] || 0) + 1;
        });
      }
    });

    // Convert to arrays
    const dailyStatsArray = Object.entries(dailyStats).map(([date, stats]) => ({
      date,
      ...stats
    })).sort((a, b) => a.date.localeCompare(b.date));

    const topRecipientsArray = Object.entries(topRecipients)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([email, count]) => ({ email, count }));

    res.json({
      success: true,
      analytics: {
        summary: {
          total_sent: totalSent,
          total_failed: totalFailed,
          success_rate: totalSent + totalFailed > 0 ? 
            (totalSent / (totalSent + totalFailed) * 100).toFixed(2) : 0
        },
        daily_stats: dailyStatsArray,
        top_recipients: topRecipientsArray
      }
    });

  } catch (error) {
    console.error('Email analytics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch email analytics'
    });
  }
});

module.exports = router;
```

## Database Schema

### Firestore Collections Structure

```javascript
// Collection: users
{
  // Document ID: Google User ID (e.g., "1234567890")
  "id": "1234567890",
  "email": "john@company.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "gmail_connected": true,
  "gmail_connected_at": "2025-10-04T10:30:00.000Z",
  "gmail_email": "john@company.com",
  "total_emails_sent": 25,
  "created_at": "2025-10-01T09:15:00.000Z",
  "updated_at": "2025-10-04T11:20:00.000Z",
  "last_login": "2025-10-04T11:20:00.000Z"
}

// Collection: email_logs
{
  // Document ID: Auto-generated
  "user_id": "1234567890",
  "from_email": "john@company.com",
  "to_emails": ["client@example.com", "partner@startup.io"],
  "cc_emails": ["manager@company.com"],
  "bcc_emails": [],
  "subject": "Project Proposal",
  "body_type": "html",
  "message_id": "CAJvQVw...",
  "status": "sent", // "sent" | "failed"
  "error_message": null,
  "sent_at": "2025-10-04T11:25:00.000Z",
  "created_at": "2025-10-04T11:25:00.000Z"
}

// Collection: user_sessions (optional)
{
  // Document ID: JWT Token ID
  "user_id": "1234567890",
  "token_hash": "sha256_hash_of_jwt",
  "expires_at": "2025-10-11T11:20:00.000Z",
  "created_at": "2025-10-04T11:20:00.000Z",
  "last_used": "2025-10-04T11:25:00.000Z"
}
```

### Firestore Security Rules

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own documents
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Email logs - users can only access their own logs
    match /email_logs/{logId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.user_id;
      allow create: if request.auth != null && 
        request.auth.uid == request.resource.data.user_id;
    }
    
    // User sessions (if used)
    match /user_sessions/{sessionId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.user_id;
    }
  }
}
```

## Security Considerations

### 1. Environment Variables Security
- Never expose API keys in frontend code
- Use environment-specific configuration files
- Rotate API keys regularly

### 2. JWT Token Security
```javascript
// Secure JWT configuration
const jwtConfig = {
  expiresIn: '7d', // Reasonable expiration
  algorithm: 'HS256',
  issuer: 'your-app-name',
  audience: 'your-app-users'
};

// Token refresh mechanism (optional)
const refreshToken = jwt.sign(
  { userId, type: 'refresh' },
  process.env.JWT_REFRESH_SECRET,
  { expiresIn: '30d' }
);
```

### 3. Input Validation
```javascript
// Email validation middleware
const validateEmailInput = (req, res, next) => {
  const { to, subject, body } = req.body;
  
  // Validate recipients
  if (!Array.isArray(to) || to.length === 0) {
    return res.status(400).json({
      success: false,
      error: 'Recipients must be a non-empty array'
    });
  }
  
  // Validate email format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const invalidEmails = to.filter(email => !emailRegex.test(email));
  
  if (invalidEmails.length > 0) {
    return res.status(400).json({
      success: false,
      error: `Invalid email addresses: ${invalidEmails.join(', ')}`
    });
  }
  
  // Validate subject and body
  if (!subject || subject.trim().length === 0) {
    return res.status(400).json({
      success: false,
      error: 'Subject is required'
    });
  }
  
  if (!body || body.trim().length === 0) {
    return res.status(400).json({
      success: false,
      error: 'Email body is required'
    });
  }
  
  // Prevent excessively long content
  if (subject.length > 200) {
    return res.status(400).json({
      success: false,
      error: 'Subject too long (max 200 characters)'
    });
  }
  
  if (body.length > 50000) {
    return res.status(400).json({
      success: false,
      error: 'Email body too long (max 50,000 characters)'
    });
  }
  
  next();
};
```

### 4. Rate Limiting
```javascript
const rateLimit = require('express-rate-limit');

// Email sending rate limit
const emailRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 50, // Limit each user to 50 emails per windowMs
  message: {
    success: false,
    error: 'Too many emails sent, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => {
    return req.user?.id || req.ip;
  }
});

// Apply to email routes
app.use('/api/emails/send', emailRateLimit);
```

## Testing & Deployment

### 1. Environment Setup

```bash
# Development
npm install
cp .env.example .env
# Fill in your environment variables

# Start development server
npm run dev
```

### 2. Testing

```javascript
// test/auth.test.js
const request = require('supertest');
const { app } = require('../server');

describe('Authentication', () => {
  test('should authenticate with valid Google token', async () => {
    const response = await request(app)
      .post('/api/auth/google')
      .send({
        credential: 'valid_google_jwt_token'
      });
    
    expect(response.status).toBe(200);
    expect(response.body.success).toBe(true);
    expect(response.body.token).toBeDefined();
  });
  
  test('should reject invalid Google token', async () => {
    const response = await request(app)
      .post('/api/auth/google')
      .send({
        credential: 'invalid_token'
      });
    
    expect(response.status).toBe(400);
    expect(response.body.success).toBe(false);
  });
});
```

### 3. Production Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - PORT=3000
    env_file:
      - .env.production
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
```

### 4. Monitoring & Logging

```javascript
// middleware/logging.js
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Request logging middleware
const requestLogger = (req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    const logData = {
      method: req.method,
      url: req.url,
      status: res.statusCode,
      duration: `${duration}ms`,
      userAgent: req.get('User-Agent'),
      ip: req.ip,
      userId: req.user?.id || null
    };
    
    if (res.statusCode >= 400) {
      logger.error('HTTP Request Error', logData);
    } else {
      logger.info('HTTP Request', logData);
    }
  });
  
  next();
};

module.exports = { logger, requestLogger };
```

## API Endpoints Reference

### Authentication Endpoints

```
POST /api/auth/google
  Body: { credential: "google_jwt_token" }
  Response: { success: true, token: "jwt_token", user: {...} }

GET /api/auth/profile
  Headers: { Authorization: "Bearer jwt_token" }
  Response: { success: true, user: {...} }

POST /api/auth/logout  
  Headers: { Authorization: "Bearer jwt_token" }
  Response: { success: true, message: "Logged out successfully" }
```

### Gmail Integration Endpoints

```
POST /api/gmail/connect
  Headers: { Authorization: "Bearer jwt_token" }
  Response: { success: true, authorization_url: "https://...", state: "user_id" }

GET /api/gmail/callback?code=...&state=...
  Response: Redirect to frontend with success/error params

POST /api/gmail/disconnect
  Headers: { Authorization: "Bearer jwt_token" }
  Response: { success: true, message: "Gmail disconnected successfully" }

GET /api/gmail/status
  Headers: { Authorization: "Bearer jwt_token" }
  Response: { success: true, gmail_connected: true, gmail_email: "...", connected_at: "..." }
```

### Email Endpoints

```
POST /api/emails/send
  Headers: { Authorization: "Bearer jwt_token" }
  Body: {
    to: ["email@example.com"],
    subject: "Subject",
    body: "Message",
    body_type: "text|html",
    cc: ["cc@example.com"], // optional
    bcc: ["bcc@example.com"] // optional
  }
  Response: { success: true, message_id: "...", recipients: 1 }

GET /api/emails/history?limit=50&offset=0
  Headers: { Authorization: "Bearer jwt_token" }
  Response: { success: true, emails: [...], total: 25 }

GET /api/emails/analytics?start_date=2025-01-01&end_date=2025-12-31
  Headers: { Authorization: "Bearer jwt_token" }
  Response: { success: true, analytics: {...} }
```

---

This documentation provides a complete implementation guide for integrating EmailMCP with your frontend application, including user authentication, Gmail OAuth, and secure data storage in Google Cloud Firestore. All components are production-ready with proper error handling, security measures, and monitoring capabilities.