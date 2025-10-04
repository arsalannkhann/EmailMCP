// Configuration for EmailMCP Integration
const CONFIG = {
    // EmailMCP Service Configuration (Production)
    EMAILMCP_SERVICE_URL: 'https://emailmcp-hcnqp547xa-uc.a.run.app',
    EMAILMCP_API_KEY: 'emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw',
    
    // Google OAuth Configuration
    GOOGLE_CLIENT_ID: '480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com',
    
    // Backend Server Configuration (if using proxy)
    // Set to null if connecting directly to EmailMCP
    BACKEND_URL: null, // e.g., 'http://localhost:3000/api'
    
    // OAuth Callback Configuration
    OAUTH_REDIRECT_URI: window.location.origin + '/callback.html',
    
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
