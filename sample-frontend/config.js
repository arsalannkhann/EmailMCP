// Configuration for EmailMCP Integration
const CONFIG = {
    // EmailMCP Service Configuration (Production)
    EMAILMCP_SERVICE_URL: 'https://emailmcp-hcnqp547xa-uc.a.run.app',
    EMAILMCP_API_KEY: 'api',
    
    // Google OAuth Configuration
    GOOGLE_CLIENT_ID: 'client_id',
    
    // Backend Server Configuration (if using proxy)
    // Set to null if connecting directly to EmailMCP
    BACKEND_URL: null, // e.g., 'http://localhost:3000/api'
    
    // OAuth Callback Configuration
    OAUTH_REDIRECT_URI: 'http://localhost:8080/callback.html',
    
    // Feature Flags
    USE_BACKEND_PROXY: false, // Set to true if using your own backend
};

// Helper to get auth headers
function getAuthHeaders() {
    return {
        'Authorization': `Bearer ${CONFIG.EMAILMCP_API_KEY}`,
        'Content-Type': 'application/json'
    };
}

// Helper to get API base URL
function getApiBaseUrl() {
    return CONFIG.USE_BACKEND_PROXY && CONFIG.BACKEND_URL 
        ? CONFIG.BACKEND_URL 
        : CONFIG.EMAILMCP_SERVICE_URL;
}
