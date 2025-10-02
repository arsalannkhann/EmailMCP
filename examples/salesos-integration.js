// SalesOS Frontend Integration with EmailMCP Multi-Tenant Service

class EmailMCPIntegration {
    constructor(apiUrl, apiKey) {
        this.apiUrl = apiUrl;
        this.apiKey = apiKey;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    // OAuth Flow Management
    async initiateGmailConnection(userId, redirectUri) {
        try {
            const response = await fetch(`${this.apiUrl}/v1/oauth/authorize`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    user_id: userId,
                    redirect_uri: redirectUri
                })
            });

            const result = await response.json();
            
            if (result.authorization_url) {
                // Redirect user to Gmail OAuth
                window.location.href = result.authorization_url;
                return true;
            }
            
            throw new Error('Failed to generate OAuth URL');
        } catch (error) {
            console.error('Gmail connection failed:', error);
            return false;
        }
    }

    // Handle OAuth callback (call this from your callback page)
    async handleOAuthCallback(code, state) {
        try {
            const response = await fetch(`${this.apiUrl}/v1/oauth/callback?code=${code}&state=${state}`, {
                method: 'POST',
                headers: this.headers
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                // Show success message
                this.showNotification(`Gmail connected successfully: ${result.email_address}`, 'success');
                // Refresh user profile
                await this.loadUserProfile(result.user_id);
                return true;
            }
            
            throw new Error(result.detail || 'OAuth callback failed');
        } catch (error) {
            console.error('OAuth callback error:', error);
            this.showNotification('Failed to connect Gmail account', 'error');
            return false;
        }
    }

    // User Profile Management
    async loadUserProfile(userId) {
        try {
            const response = await fetch(`${this.apiUrl}/v1/users/${userId}/profile`, {
                headers: this.headers
            });

            const profile = await response.json();
            this.updateUIWithProfile(profile);
            return profile;
        } catch (error) {
            console.error('Failed to load user profile:', error);
            return null;
        }
    }

    // Send Email
    async sendEmail(userId, emailData) {
        try {
            const response = await fetch(`${this.apiUrl}/v1/users/${userId}/messages`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    to: emailData.recipients,
                    subject: emailData.subject,
                    body: emailData.message,
                    body_type: emailData.isHtml ? 'html' : 'text',
                    cc: emailData.cc || [],
                    bcc: emailData.bcc || []
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification(`Email sent successfully! ID: ${result.message_id}`, 'success');
                // Refresh analytics
                this.refreshEmailStats(userId);
                return result;
            } else {
                throw new Error(result.error || 'Failed to send email');
            }
        } catch (error) {
            console.error('Email send failed:', error);
            this.showNotification(`Failed to send email: ${error.message}`, 'error');
            return null;
        }
    }

    // Email Analytics
    async getEmailAnalytics(userId, startDate = null, endDate = null) {
        try {
            let url = `${this.apiUrl}/v1/reports/users/${userId}`;
            const params = new URLSearchParams();
            
            if (startDate) params.append('start_date', startDate.toISOString());
            if (endDate) params.append('end_date', endDate.toISOString());
            
            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            const response = await fetch(url, { headers: this.headers });
            const analytics = await response.json();
            
            this.updateAnalyticsDashboard(analytics);
            return analytics;
        } catch (error) {
            console.error('Failed to load analytics:', error);
            return null;
        }
    }

    // Platform Summary (for admins)
    async getPlatformSummary() {
        try {
            const response = await fetch(`${this.apiUrl}/v1/reports/summary`, {
                headers: this.headers
            });

            const summary = await response.json();
            this.updatePlatformDashboard(summary);
            return summary;
        } catch (error) {
            console.error('Failed to load platform summary:', error);
            return null;
        }
    }

    // UI Update Methods
    updateUIWithProfile(profile) {
        const gmailStatus = document.getElementById('gmail-status');
        
        if (profile.gmail_connected) {
            gmailStatus.innerHTML = `
                <div class="connected-status">
                    <span class="status-icon">✅</span>
                    <span>Connected: ${profile.email_address}</span>
                    <button onclick="emailMCP.disconnectGmail('${profile.user_id}')" class="btn-disconnect">
                        Disconnect
                    </button>
                </div>
                <div class="stats">
                    <small>Total emails sent: ${profile.total_emails_sent}</small>
                    <small>Last used: ${profile.last_used ? new Date(profile.last_used).toLocaleDateString() : 'Never'}</small>
                </div>
            `;
        } else {
            gmailStatus.innerHTML = `
                <div class="disconnected-status">
                    <span class="status-icon">❌</span>
                    <span>Gmail not connected</span>
                    <button onclick="emailMCP.connectGmail()" class="btn-connect">
                        Connect Gmail
                    </button>
                </div>
            `;
        }
    }

    updateAnalyticsDashboard(analytics) {
        // Update email stats cards
        document.getElementById('total-emails').textContent = analytics.total_emails;
        document.getElementById('success-rate').textContent = `${analytics.success_rate.toFixed(1)}%`;
        document.getElementById('failed-emails').textContent = analytics.failed_emails;

        // Update charts (using Chart.js example)
        this.updateEmailChart(analytics.emails_by_day);
        this.updateRecipientsTable(analytics.top_recipients);
        this.updateRecentEmailsList(analytics.recent_emails);
    }

    updateEmailChart(dailyStats) {
        const ctx = document.getElementById('email-chart').getContext('2d');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dailyStats.map(stat => stat.date),
                datasets: [
                    {
                        label: 'Successful',
                        data: dailyStats.map(stat => stat.successful),
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    },
                    {
                        label: 'Failed',
                        data: dailyStats.map(stat => stat.failed),
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Email Activity Over Time'
                    }
                }
            }
        });
    }

    // Utility Methods
    async connectGmail() {
        const currentUser = this.getCurrentUser();
        const redirectUri = `${window.location.origin}/gmail-callback`;
        await this.initiateGmailConnection(currentUser.id, redirectUri);
    }

    async disconnectGmail(userId) {
        try {
            const response = await fetch(`${this.apiUrl}/v1/users/${userId}/gmail`, {
                method: 'DELETE',
                headers: this.headers
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('Gmail account disconnected', 'success');
                await this.loadUserProfile(userId);
            }
        } catch (error) {
            console.error('Failed to disconnect Gmail:', error);
            this.showNotification('Failed to disconnect Gmail', 'error');
        }
    }

    async refreshEmailStats(userId) {
        // Refresh analytics after sending email
        setTimeout(() => {
            this.getEmailAnalytics(userId);
        }, 2000);
    }

    showNotification(message, type = 'info') {
        // Create notification UI
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getCurrentUser() {
        // This should return the current SalesOS user
        // Implementation depends on your authentication system
        return {
            id: window.currentUserId || 'user-123',
            email: window.currentUserEmail || 'user@example.com'
        };
    }
}

// Initialize EmailMCP integration
const emailMCP = new EmailMCPIntegration(
    'http://emailmcp-alb-156343542.us-east-1.elb.amazonaws.com',
    'emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw'
);

// Example usage in SalesOS
document.addEventListener('DOMContentLoaded', function() {
    // Load user profile on page load
    const currentUser = emailMCP.getCurrentUser();
    emailMCP.loadUserProfile(currentUser.id);
    
    // Load email analytics
    emailMCP.getEmailAnalytics(currentUser.id);
});

// Email compose form handler
document.getElementById('email-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const currentUser = emailMCP.getCurrentUser();
    
    const emailData = {
        recipients: formData.get('recipients').split(',').map(email => email.trim()),
        subject: formData.get('subject'),
        message: formData.get('message'),
        isHtml: formData.get('body_type') === 'html',
        cc: formData.get('cc') ? formData.get('cc').split(',').map(email => email.trim()) : [],
        bcc: formData.get('bcc') ? formData.get('bcc').split(',').map(email => email.trim()) : []
    };
    
    const result = await emailMCP.sendEmail(currentUser.id, emailData);
    
    if (result) {
        // Reset form on success
        e.target.reset();
    }
});