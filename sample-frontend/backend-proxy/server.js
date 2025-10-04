const express = require('express');
const cors = require('cors');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// EmailMCP Configuration
const EMAILMCP_SERVICE_URL = process.env.EMAILMCP_SERVICE_URL || 'https://emailmcp-hcnqp547xa-uc.a.run.app';
const EMAILMCP_API_KEY = process.env.EMAILMCP_API_KEY || 'emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw';

// Middleware
app.use(cors({
    origin: process.env.FRONTEND_URL || '*',
    credentials: true
}));
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Helper function to create EmailMCP headers
function getEmailMCPHeaders() {
    return {
        'Authorization': `Bearer ${EMAILMCP_API_KEY}`,
        'Content-Type': 'application/json'
    };
}

// ========== HEALTH CHECK ==========

app.get('/api/health', async (req, res) => {
    try {
        const response = await axios.get(`${EMAILMCP_SERVICE_URL}/health`);
        res.json({
            status: 'healthy',
            backend: 'ok',
            emailmcp: response.data
        });
    } catch (error) {
        res.status(503).json({
            status: 'unhealthy',
            backend: 'ok',
            emailmcp: 'unreachable',
            error: error.message
        });
    }
});

// ========== OAUTH ENDPOINTS ==========

app.post('/api/oauth/authorize', async (req, res) => {
    try {
        const { user_id, redirect_uri } = req.body;
        
        if (!user_id || !redirect_uri) {
            return res.status(400).json({ error: 'user_id and redirect_uri are required' });
        }

        const response = await axios.post(
            `${EMAILMCP_SERVICE_URL}/v1/oauth/authorize`,
            { user_id, redirect_uri },
            { headers: getEmailMCPHeaders() }
        );

        res.json(response.data);
    } catch (error) {
        console.error('OAuth authorize error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.detail || error.message
        });
    }
});

app.post('/api/oauth/callback', async (req, res) => {
    try {
        const { code, state } = req.query;
        
        if (!code || !state) {
            return res.status(400).json({ error: 'code and state are required' });
        }

        const response = await axios.post(
            `${EMAILMCP_SERVICE_URL}/v1/oauth/callback?code=${code}&state=${state}`,
            {},
            { headers: getEmailMCPHeaders() }
        );

        res.json(response.data);
    } catch (error) {
        console.error('OAuth callback error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.detail || error.message
        });
    }
});

// ========== USER ENDPOINTS ==========

app.get('/api/users/:userId/profile', async (req, res) => {
    try {
        const { userId } = req.params;

        const response = await axios.get(
            `${EMAILMCP_SERVICE_URL}/v1/users/${userId}/profile`,
            { headers: getEmailMCPHeaders() }
        );

        res.json(response.data);
    } catch (error) {
        console.error('Get profile error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.detail || error.message
        });
    }
});

app.delete('/api/users/:userId/gmail', async (req, res) => {
    try {
        const { userId } = req.params;

        const response = await axios.delete(
            `${EMAILMCP_SERVICE_URL}/v1/users/${userId}/gmail`,
            { headers: getEmailMCPHeaders() }
        );

        res.json(response.data);
    } catch (error) {
        console.error('Disconnect Gmail error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.detail || error.message
        });
    }
});

// ========== EMAIL ENDPOINTS ==========

app.post('/api/users/:userId/messages', async (req, res) => {
    try {
        const { userId } = req.params;
        const emailData = req.body;

        // Validate required fields
        if (!emailData.to || !emailData.subject || !emailData.body) {
            return res.status(400).json({ 
                error: 'to, subject, and body are required' 
            });
        }

        const response = await axios.post(
            `${EMAILMCP_SERVICE_URL}/v1/users/${userId}/messages`,
            emailData,
            { headers: getEmailMCPHeaders() }
        );

        res.json(response.data);
    } catch (error) {
        console.error('Send email error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.detail || error.message
        });
    }
});

// ========== ANALYTICS ENDPOINTS ==========

app.get('/api/reports/users/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const { start_date, end_date } = req.query;

        let url = `${EMAILMCP_SERVICE_URL}/v1/reports/users/${userId}`;
        const params = new URLSearchParams();
        
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        const response = await axios.get(url, { headers: getEmailMCPHeaders() });

        res.json(response.data);
    } catch (error) {
        console.error('Get analytics error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.detail || error.message
        });
    }
});

app.get('/api/reports/summary', async (req, res) => {
    try {
        const response = await axios.get(
            `${EMAILMCP_SERVICE_URL}/v1/reports/summary`,
            { headers: getEmailMCPHeaders() }
        );

        res.json(response.data);
    } catch (error) {
        console.error('Get summary error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.detail || error.message
        });
    }
});

// ========== ERROR HANDLING ==========

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Endpoint not found' });
});

// Global error handler
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// ========== START SERVER ==========

app.listen(PORT, () => {
    console.log('='.repeat(60));
    console.log('EmailMCP Backend Proxy Server');
    console.log('='.repeat(60));
    console.log(`Server running on port ${PORT}`);
    console.log(`EmailMCP Service: ${EMAILMCP_SERVICE_URL}`);
    console.log(`API Key: ${EMAILMCP_API_KEY.substring(0, 20)}...`);
    console.log('='.repeat(60));
});
