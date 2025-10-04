# Sample Frontend Integration Testing Guide

Complete testing guide for the EmailMCP sample frontend application.

## Pre-Testing Checklist

- [ ] EmailMCP service is running: https://emailmcp-hcnqp547xa-uc.a.run.app/health
- [ ] Google OAuth credentials are configured
- [ ] Frontend is being served (not opened as file://)
- [ ] Browser has JavaScript enabled
- [ ] Browser console is open for debugging

## Test Scenarios

### 1. Initial Setup Tests

#### 1.1 Test Frontend Loads
**Steps:**
1. Navigate to http://localhost:8000
2. Verify page loads without errors

**Expected Result:**
- Page displays "EmailMCP Sample Integration" header
- Google Sign-In button is visible
- No console errors

#### 1.2 Test Configuration
**Steps:**
1. Open browser console
2. Type: `CONFIG`
3. Verify configuration values

**Expected Result:**
```javascript
{
    EMAILMCP_SERVICE_URL: "https://emailmcp-hcnqp547xa-uc.a.run.app",
    EMAILMCP_API_KEY: "emailmcp-...",
    GOOGLE_CLIENT_ID: "480969272523-...",
    ...
}
```

### 2. Authentication Tests

#### 2.1 Google Sign-In
**Steps:**
1. Click "Sign in with Google" button
2. Select a Google account
3. Grant permissions if prompted

**Expected Result:**
- User profile appears with avatar, name, and email
- Main content section becomes visible
- "Logout" button appears

#### 2.2 Session Persistence
**Steps:**
1. Sign in with Google
2. Refresh the page

**Expected Result:**
- User remains signed in
- Profile information persists
- Main content still visible

#### 2.3 Logout
**Steps:**
1. Sign in with Google
2. Click "Logout" button

**Expected Result:**
- User profile disappears
- Main content is hidden
- Google Sign-In button reappears
- Success notification shows "Logged out successfully"

### 3. Connection Tests

#### 3.1 Auto Connection Check
**Steps:**
1. Sign in with Google
2. Wait for connection checks to complete

**Expected Result:**
- EmailMCP Status: 🟢 Connected
- Gmail Status: Shows connection state
- All status indicators update

#### 3.2 Manual Connection Test
**Steps:**
1. Sign in with Google
2. Click "Test All Connections"

**Expected Result:**
- All three status indicators update
- EmailMCP service shows connected
- Notifications appear for each check

### 4. Gmail OAuth Flow Tests

#### 4.1 Initiate Gmail Connection
**Steps:**
1. Sign in with Google
2. Gmail status shows "Not Connected"
3. Click "Connect Gmail Account"

**Expected Result:**
- Redirected to Google OAuth consent screen
- Shows permissions requested:
  - Send emails on your behalf
  - View email messages
  - etc.

#### 4.2 Complete OAuth Flow
**Steps:**
1. Initiate Gmail connection
2. On consent screen, click "Continue" or "Allow"
3. Wait for redirect

**Expected Result:**
- Redirected to /callback.html
- Shows "Processing Gmail Connection..."
- Success message appears
- Redirected back to main app
- Gmail status updates to "🟢 Connected"
- Shows connected email address

#### 4.3 OAuth Callback Error Handling
**Steps:**
1. Manually navigate to /callback.html?error=access_denied

**Expected Result:**
- Error message displayed
- Redirected to main app after 3 seconds

#### 4.4 Disconnect Gmail
**Steps:**
1. With Gmail connected
2. Click "Disconnect Gmail"
3. Confirm in dialog

**Expected Result:**
- Success notification
- Gmail status updates to "Not Connected"
- "Connect Gmail Account" button reappears

### 5. Email Sending Tests

#### 5.1 Send Simple Text Email
**Steps:**
1. Ensure Gmail is connected
2. Fill in email form:
   - To: your-email@example.com
   - Subject: Test Email from EmailMCP
   - Message: This is a test email
3. Click "Send Email"

**Expected Result:**
- "Sending email..." notification appears
- Success notification with message ID
- Green success box shows below form
- Analytics refresh after 2 seconds
- Form remains filled (not reset on success in current implementation)

#### 5.2 Send Email with CC and BCC
**Steps:**
1. Fill in email form with:
   - To: recipient1@example.com
   - CC: cc@example.com
   - BCC: bcc@example.com
   - Subject: Test with CC/BCC
   - Message: Testing carbon copies
2. Click "Send Email"

**Expected Result:**
- Email sends successfully
- All recipients receive email
- BCC recipient not visible to others

#### 5.3 Send HTML Email
**Steps:**
1. Fill in email form:
   - To: your-email@example.com
   - Subject: HTML Test
   - Message: `<h1>Hello</h1><p>This is <strong>HTML</strong></p>`
   - Check "Send as HTML"
2. Click "Send Email"

**Expected Result:**
- Email sends successfully
- Email received shows formatted HTML

#### 5.4 Send to Multiple Recipients
**Steps:**
1. Fill in email form:
   - To: email1@example.com, email2@example.com, email3@example.com
   - Subject: Multiple Recipients
   - Message: Testing multiple recipients
2. Click "Send Email"

**Expected Result:**
- Email sends to all recipients
- Success notification shows

#### 5.5 Send Email Without Gmail Connected
**Steps:**
1. Ensure Gmail is NOT connected (disconnect if needed)
2. Try to send an email

**Expected Result:**
- Error notification: "User has not connected Gmail"
- Red error box appears
- Email not sent

#### 5.6 Form Validation
**Steps:**
1. Try to submit form without filling required fields
2. Try each combination:
   - No recipient
   - No subject
   - No message

**Expected Result:**
- Browser validation prevents submission
- Required fields highlighted
- Form not submitted

### 6. Analytics Tests

#### 6.1 View Analytics After Sending
**Steps:**
1. Send 2-3 emails
2. Wait for analytics to load

**Expected Result:**
- Total Emails count updates
- Success Rate shows percentage
- Chart displays data points
- Recent Emails list shows sent emails

#### 6.2 Refresh Analytics
**Steps:**
1. Click "Refresh Analytics"

**Expected Result:**
- Analytics update
- Loading state (if implemented)
- Latest data displayed

#### 6.3 Chart Interaction
**Steps:**
1. Hover over chart points
2. Check chart legend

**Expected Result:**
- Tooltips show data values
- Legend shows Successful/Failed
- Chart is responsive

#### 6.4 Recent Emails Display
**Steps:**
1. Send emails and view recent list
2. Check email details shown

**Expected Result:**
- Shows recipient(s)
- Shows subject
- Shows timestamp
- Shows status (Sent/Failed)
- List scrollable if many emails

### 7. Error Handling Tests

#### 7.1 Network Error Handling
**Steps:**
1. Disconnect internet
2. Try to send email

**Expected Result:**
- Error notification appears
- User-friendly error message
- Form not reset

#### 7.2 Invalid API Key
**Steps:**
1. Edit config.js with invalid API key
2. Refresh page
3. Try any action

**Expected Result:**
- Error notifications show
- Status indicators show errors
- App remains usable

#### 7.3 Service Unavailable
**Steps:**
1. Temporarily stop EmailMCP service (if testing)
2. Test connections

**Expected Result:**
- Status shows service offline
- Clear error messages
- App doesn't crash

### 8. UI/UX Tests

#### 8.1 Responsive Design - Mobile
**Steps:**
1. Open browser DevTools
2. Switch to mobile viewport (iPhone/Android)
3. Test all features

**Expected Result:**
- Layout adjusts to mobile
- All features accessible
- Buttons tap-friendly
- No horizontal scroll

#### 8.2 Responsive Design - Tablet
**Steps:**
1. Switch to tablet viewport (iPad)
2. Test all features

**Expected Result:**
- Layout appropriate for tablet
- Two-column layouts where appropriate
- All features work

#### 8.3 Notifications
**Steps:**
1. Perform various actions
2. Observe notifications

**Expected Result:**
- Notifications appear top-right
- Auto-dismiss after 5 seconds
- Stackable (multiple visible)
- Appropriate icons and colors

#### 8.4 Loading States
**Steps:**
1. Send email
2. Observe button state

**Expected Result:**
- Button shows "Sending..."
- Spinner appears
- Button disabled during send
- Re-enables after completion

### 9. Browser Compatibility Tests

Test in multiple browsers:

#### 9.1 Chrome/Edge (Chromium)
- [ ] All features work
- [ ] Styles render correctly
- [ ] No console errors

#### 9.2 Firefox
- [ ] All features work
- [ ] Styles render correctly
- [ ] No console errors

#### 9.3 Safari
- [ ] All features work
- [ ] Styles render correctly
- [ ] OAuth flow works

### 10. Connection Testing Utility

#### 10.1 Use Test Page
**Steps:**
1. Navigate to /test-connection.html
2. Click "Run All Tests"

**Expected Result:**
- All 6 tests run sequentially
- Results displayed for each test
- Summary shows pass/fail count
- Detailed JSON responses available

#### 10.2 Individual Endpoint Tests
**Steps:**
1. Review each test result
2. Expand details for JSON responses

**Expected Result:**
- Health Check: Pass
- API Documentation: Pass
- User Profile: Pass or Warn (if new user)
- OAuth Initiation: Pass
- Email Sending: Warn (Gmail not connected)
- Analytics: Warn (no data yet)

## Common Issues and Solutions

### Issue: OAuth Redirect URI Mismatch
**Solution:**
1. Go to Google Cloud Console
2. Update Authorized redirect URIs
3. Add: http://localhost:8000/callback.html

### Issue: CORS Errors
**Solution:**
1. Don't open file:// directly
2. Use HTTP server (Python/Node.js)
3. Check browser console for specific error

### Issue: Gmail Won't Connect
**Solution:**
1. Check EmailMCP service is running
2. Verify API key in config.js
3. Clear browser cache/cookies
4. Try incognito mode

### Issue: Emails Not Sending
**Solution:**
1. Verify Gmail is connected (green status)
2. Check all required fields filled
3. View browser console for errors
4. Test with test-connection.html

## Performance Tests

### Load Time
- [ ] Initial page load < 2 seconds
- [ ] Sign in < 1 second
- [ ] OAuth redirect < 3 seconds
- [ ] Email send < 3 seconds

### Stress Testing
- [ ] Send 10 emails in quick succession
- [ ] Switch between multiple accounts
- [ ] Rapid sign in/out cycles

## Security Tests

- [ ] API key not exposed in network tab (if using proxy)
- [ ] OAuth tokens not visible to frontend
- [ ] Session data cleared on logout
- [ ] No sensitive data in localStorage

## Accessibility Tests

- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Color contrast sufficient
- [ ] Screen reader compatible (basic)

## Test Results Template

```
Test Date: __________
Tester: __________
Environment: __________

Summary:
- Total Tests: __
- Passed: __
- Failed: __
- Skipped: __

Critical Issues:
1. 
2.

Minor Issues:
1.
2.

Notes:
```

## Automated Testing (Future)

Consider adding:
- Jest for unit tests
- Cypress for E2E tests
- Playwright for browser automation
- Lighthouse for performance

## Continuous Testing

For ongoing development:
1. Test after each code change
2. Re-run all tests before deployment
3. Monitor real user feedback
4. Check analytics for errors
