// EmailMCP Sample Frontend Application

class EmailMCPApp {
    constructor() {
        this.currentUser = null;
        this.googleUser = null;
        this.chart = null;
        this.init();
    }

    init() {
        console.log('Initializing EmailMCP Sample App...');
        this.initGoogleSignIn();
        this.attachEventListeners();
        this.checkExistingSession();
    }

    // ========== GOOGLE AUTHENTICATION ==========
    
    initGoogleSignIn() {
        window.onload = () => {
            google.accounts.id.initialize({
                client_id: CONFIG.GOOGLE_CLIENT_ID,
                callback: this.handleGoogleCallback.bind(this)
            });

            google.accounts.id.renderButton(
                document.getElementById('google-signin-button'),
                { 
                    theme: 'outline', 
                    size: 'large',
                    text: 'signin_with',
                    width: 250
                }
            );

            // Try to sign in automatically if previously signed in
            google.accounts.id.prompt();
        };
    }

    async handleGoogleCallback(response) {
        try {
            // Decode JWT token to get user info
            const userInfo = this.parseJwt(response.credential);
            
            this.currentUser = {
                id: `user_${userInfo.sub}`,
                email: userInfo.email,
                name: userInfo.name,
                picture: userInfo.picture,
                googleToken: response.credential
            };

            // Store in session
            sessionStorage.setItem('emailmcp_user', JSON.stringify(this.currentUser));

            this.showNotification('Successfully signed in with Google!', 'success');
            this.updateUIAfterLogin();
            
            // Check all connections
            await this.checkAllConnections();
            
        } catch (error) {
            console.error('Google sign-in error:', error);
            this.showNotification('Failed to sign in with Google', 'error');
        }
    }

    parseJwt(token) {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    }

    logout() {
        google.accounts.id.disableAutoSelect();
        sessionStorage.removeItem('emailmcp_user');
        this.currentUser = null;
        this.updateUIAfterLogout();
        this.showNotification('Logged out successfully', 'info');
    }

    checkExistingSession() {
        const storedUser = sessionStorage.getItem('emailmcp_user');
        if (storedUser) {
            this.currentUser = JSON.parse(storedUser);
            this.updateUIAfterLogin();
            this.checkAllConnections();
        }
    }

    updateUIAfterLogin() {
        // Hide auth section content
        document.getElementById('google-signin-button').classList.add('hidden');
        
        // Show user info
        const userInfo = document.getElementById('user-info');
        userInfo.classList.remove('hidden');
        document.getElementById('user-avatar').src = this.currentUser.picture;
        document.getElementById('user-name').textContent = this.currentUser.name;
        document.getElementById('user-email').textContent = this.currentUser.email;

        // Show main content
        document.getElementById('main-content').classList.remove('hidden');
    }

    updateUIAfterLogout() {
        // Show auth section
        document.getElementById('google-signin-button').classList.remove('hidden');
        
        // Hide user info
        document.getElementById('user-info').classList.add('hidden');
        
        // Hide main content
        document.getElementById('main-content').classList.add('hidden');
    }

    // ========== CONNECTION TESTING ==========

    async checkAllConnections() {
        console.log('Testing all connections...');
        
        // Test EmailMCP Service
        await this.testEmailMCPConnection();
        
        // Check Gmail connection status
        await this.checkGmailConnectionStatus();
        
        // Load user analytics
        await this.loadAnalytics();
    }

    async testEmailMCPConnection() {
        try {
            const response = await fetch(`${CONFIG.EMAILMCP_SERVICE_URL}/health`, {
                method: 'GET'
            });

            if (response.ok) {
                this.updateStatusIndicator('emailmcp-status', '🟢 Connected', 'success');
            } else {
                this.updateStatusIndicator('emailmcp-status', '🔴 Error', 'error');
            }
        } catch (error) {
            console.error('EmailMCP connection test failed:', error);
            this.updateStatusIndicator('emailmcp-status', '🔴 Offline', 'error');
        }
    }

    async checkGmailConnectionStatus() {
        try {
            const response = await fetch(
                `${CONFIG.EMAILMCP_SERVICE_URL}/v1/users/${this.currentUser.id}/profile`,
                {
                    method: 'GET',
                    headers: getAuthHeaders()
                }
            );

            if (response.ok) {
                const profile = await response.json();
                this.updateGmailStatus(profile);
                
                if (profile.gmail_connected) {
                    this.updateStatusIndicator('gmail-status', '🟢 Connected', 'success');
                } else {
                    this.updateStatusIndicator('gmail-status', '🔴 Not Connected', 'warning');
                }
            } else {
                // User not yet registered with EmailMCP
                this.updateStatusIndicator('gmail-status', '⚪ Not Registered', 'info');
                this.updateGmailStatus({ gmail_connected: false });
            }
        } catch (error) {
            console.error('Gmail status check failed:', error);
            this.updateStatusIndicator('gmail-status', '🔴 Error', 'error');
            this.updateGmailStatus({ gmail_connected: false });
        }
    }

    updateStatusIndicator(elementId, text, status) {
        const element = document.getElementById(elementId);
        element.textContent = text;
        element.className = 'status-indicator status-' + status;
    }

    updateGmailStatus(profile) {
        const container = document.getElementById('gmail-connection-status');
        
        if (profile.gmail_connected) {
            container.innerHTML = `
                <div class="gmail-connected">
                    <h3>✅ Gmail Connected</h3>
                    <p><strong>Email:</strong> ${profile.email_address || 'N/A'}</p>
                    <p><strong>Total Emails Sent:</strong> ${profile.total_emails_sent || 0}</p>
                    <p><strong>Connected At:</strong> ${profile.gmail_connected_at ? new Date(profile.gmail_connected_at).toLocaleString() : 'N/A'}</p>
                    <button onclick="app.disconnectGmail()" class="btn btn-danger mt-20">Disconnect Gmail</button>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="gmail-disconnected">
                    <h3>❌ Gmail Not Connected</h3>
                    <p>Connect your Gmail account to send emails through EmailMCP.</p>
                    <button onclick="app.connectGmail()" class="btn btn-success mt-20">Connect Gmail Account</button>
                </div>
            `;
        }
    }

    // ========== GMAIL OAUTH FLOW ==========

    async connectGmail() {
        try {
            this.showNotification('Initiating Gmail OAuth...', 'info');
            
            const response = await fetch(
                `${CONFIG.EMAILMCP_SERVICE_URL}/v1/oauth/authorize`,
                {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        user_id: this.currentUser.id,
                        redirect_uri: CONFIG.OAUTH_REDIRECT_URI
                    })
                }
            );

            if (response.ok) {
                const result = await response.json();
                console.log('OAuth URL generated:', result);
                
                // Store current user ID for callback
                sessionStorage.setItem('oauth_user_id', this.currentUser.id);
                
                // Redirect to Google OAuth
                window.location.href = result.authorization_url;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to initiate OAuth');
            }
        } catch (error) {
            console.error('Gmail connection error:', error);
            this.showNotification(`Failed to connect Gmail: ${error.message}`, 'error');
        }
    }

    async disconnectGmail() {
        if (!confirm('Are you sure you want to disconnect your Gmail account?')) {
            return;
        }

        try {
            const response = await fetch(
                `${CONFIG.EMAILMCP_SERVICE_URL}/v1/users/${this.currentUser.id}/gmail`,
                {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                }
            );

            if (response.ok) {
                this.showNotification('Gmail disconnected successfully', 'success');
                await this.checkGmailConnectionStatus();
            } else {
                throw new Error('Failed to disconnect Gmail');
            }
        } catch (error) {
            console.error('Gmail disconnection error:', error);
            this.showNotification('Failed to disconnect Gmail', 'error');
        }
    }

    // ========== EMAIL SENDING ==========

    async sendEmail(emailData) {
        try {
            this.showNotification('Sending email...', 'info');
            
            const response = await fetch(
                `${CONFIG.EMAILMCP_SERVICE_URL}/v1/users/${this.currentUser.id}/messages`,
                {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        to: emailData.to,
                        subject: emailData.subject,
                        body: emailData.body,
                        body_type: emailData.bodyType,
                        cc: emailData.cc || [],
                        bcc: emailData.bcc || []
                    })
                }
            );

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                this.showNotification(
                    `Email sent successfully! Message ID: ${result.message_id}`,
                    'success'
                );
                
                // Show result in UI
                this.displayEmailResult(result, 'success');
                
                // Refresh analytics after short delay
                setTimeout(() => this.loadAnalytics(), 2000);
                
                return true;
            } else {
                throw new Error(result.error || result.detail || 'Failed to send email');
            }
        } catch (error) {
            console.error('Email send error:', error);
            this.showNotification(`Failed to send email: ${error.message}`, 'error');
            this.displayEmailResult({ error: error.message }, 'error');
            return false;
        }
    }

    displayEmailResult(result, type) {
        const resultDiv = document.getElementById('email-result');
        resultDiv.classList.remove('hidden');
        
        if (type === 'success') {
            resultDiv.innerHTML = `
                <div class="notification-success" style="margin-top: 20px; padding: 15px; border-radius: 8px;">
                    <strong>✅ Email Sent Successfully!</strong><br>
                    <small>Message ID: ${result.message_id}</small><br>
                    <small>Thread ID: ${result.thread_id || 'N/A'}</small>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="notification-error" style="margin-top: 20px; padding: 15px; border-radius: 8px;">
                    <strong>❌ Failed to Send Email</strong><br>
                    <small>${result.error}</small>
                </div>
            `;
        }

        // Auto-hide after 10 seconds
        setTimeout(() => {
            resultDiv.classList.add('hidden');
        }, 10000);
    }

    // ========== ANALYTICS ==========

    async loadAnalytics() {
        try {
            const response = await fetch(
                `${CONFIG.EMAILMCP_SERVICE_URL}/v1/reports/users/${this.currentUser.id}`,
                {
                    method: 'GET',
                    headers: getAuthHeaders()
                }
            );

            if (response.ok) {
                const analytics = await response.json();
                this.displayAnalytics(analytics);
            } else {
                console.log('No analytics data available yet');
                this.displayEmptyAnalytics();
            }
        } catch (error) {
            console.error('Failed to load analytics:', error);
            this.displayEmptyAnalytics();
        }
    }

    displayAnalytics(analytics) {
        // Update stats
        document.getElementById('total-emails').textContent = analytics.total_emails || 0;
        document.getElementById('successful-emails').textContent = analytics.successful_emails || 0;
        document.getElementById('failed-emails').textContent = analytics.failed_emails || 0;
        document.getElementById('success-rate').textContent = 
            (analytics.success_rate !== undefined ? analytics.success_rate.toFixed(1) : '0') + '%';

        // Update chart
        this.updateChart(analytics.emails_by_day || []);

        // Display recent emails
        this.displayRecentEmails(analytics.recent_emails || []);
    }

    displayEmptyAnalytics() {
        document.getElementById('total-emails').textContent = '0';
        document.getElementById('successful-emails').textContent = '0';
        document.getElementById('failed-emails').textContent = '0';
        document.getElementById('success-rate').textContent = '0%';
        
        this.updateChart([]);
        this.displayRecentEmails([]);
    }

    updateChart(emailsByDay) {
        const ctx = document.getElementById('email-chart').getContext('2d');
        
        // Destroy existing chart if any
        if (this.chart) {
            this.chart.destroy();
        }

        // Prepare data
        const labels = emailsByDay.map(day => day.date);
        const successful = emailsByDay.map(day => day.successful || 0);
        const failed = emailsByDay.map(day => day.failed || 0);

        // Create chart
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Successful',
                        data: successful,
                        borderColor: '#34a853',
                        backgroundColor: 'rgba(52, 168, 83, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Failed',
                        data: failed,
                        borderColor: '#ea4335',
                        backgroundColor: 'rgba(234, 67, 53, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Email Activity Over Time',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    displayRecentEmails(emails) {
        const container = document.getElementById('recent-emails-list');
        
        if (emails.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #5f6368;">No emails sent yet</p>';
            return;
        }

        container.innerHTML = emails.map(email => `
            <div class="email-item">
                <div class="email-header">
                    <span class="email-to">To: ${email.to?.join(', ') || 'N/A'}</span>
                    <span class="email-date">${new Date(email.sent_at).toLocaleString()}</span>
                </div>
                <div class="email-subject">${email.subject || '(No Subject)'}</div>
                <span class="email-status ${email.status === 'sent' ? 'status-success' : 'status-failed'}">
                    ${email.status === 'sent' ? '✓ Sent' : '✗ Failed'}
                </span>
            </div>
        `).join('');
    }

    // ========== EVENT LISTENERS ==========

    attachEventListeners() {
        // Logout button
        document.getElementById('logout-btn')?.addEventListener('click', () => {
            this.logout();
        });

        // Test connectivity button
        document.getElementById('test-connectivity-btn')?.addEventListener('click', () => {
            this.checkAllConnections();
        });

        // Email form
        document.getElementById('email-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleEmailFormSubmit(e);
        });

        // Refresh analytics button
        document.getElementById('refresh-analytics-btn')?.addEventListener('click', () => {
            this.loadAnalytics();
        });
    }

    async handleEmailFormSubmit(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector('.btn-text');
        const spinner = submitBtn.querySelector('.spinner');

        // Disable button and show spinner
        submitBtn.disabled = true;
        btnText.textContent = 'Sending...';
        spinner.classList.remove('hidden');

        try {
            // Parse email data
            const emailData = {
                to: document.getElementById('email-to').value.split(',').map(e => e.trim()),
                subject: document.getElementById('email-subject').value,
                body: document.getElementById('email-body').value,
                bodyType: document.getElementById('email-html').checked ? 'html' : 'text',
                cc: document.getElementById('email-cc').value 
                    ? document.getElementById('email-cc').value.split(',').map(e => e.trim()) 
                    : [],
                bcc: document.getElementById('email-bcc').value 
                    ? document.getElementById('email-bcc').value.split(',').map(e => e.trim()) 
                    : []
            };

            // Send email
            const success = await this.sendEmail(emailData);

            if (success) {
                // Reset form
                form.reset();
            }
        } finally {
            // Re-enable button and hide spinner
            submitBtn.disabled = false;
            btnText.textContent = 'Send Email';
            spinner.classList.add('hidden');
        }
    }

    // ========== NOTIFICATIONS ==========

    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications-container');
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Add icon based on type
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        
        notification.innerHTML = `
            <span style="font-weight: bold; font-size: 1.2em;">${icons[type] || 'ℹ'}</span>
            <span>${message}</span>
        `;
        
        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}

// Initialize app
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new EmailMCPApp();
});
