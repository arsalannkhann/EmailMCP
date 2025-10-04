# Backend Proxy Server for EmailMCP

A simple Express.js proxy server that sits between your frontend and EmailMCP service. This hides your API key from the frontend and allows you to add additional authentication, rate limiting, or logging.

## Why Use a Backend Proxy?

### Security Benefits
- **API Key Protection**: Keeps your EmailMCP API key server-side
- **Authentication**: Add your own user authentication layer
- **Rate Limiting**: Control API usage per user
- **Request Validation**: Validate requests before forwarding to EmailMCP

### Additional Features
- Request/response logging
- Custom error handling
- Data transformation
- Caching (if needed)

## Quick Start

### 1. Install Dependencies

```bash
cd backend-proxy
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
EMAILMCP_SERVICE_URL=https://emailmcp-hcnqp547xa-uc.a.run.app
EMAILMCP_API_KEY=your-api-key-here
PORT=3000
FRONTEND_URL=http://localhost:8000
```

### 3. Start Server

**Development:**
```bash
npm run dev
```

**Production:**
```bash
npm start
```

Server will start on `http://localhost:3000`

## API Endpoints

All endpoints are prefixed with `/api`.

### Health Check
```
GET /api/health
```

### OAuth
```
POST /api/oauth/authorize
POST /api/oauth/callback?code=xxx&state=xxx
```

### User Management
```
GET /api/users/:userId/profile
DELETE /api/users/:userId/gmail
```

### Email Operations
```
POST /api/users/:userId/messages
```

### Analytics
```
GET /api/reports/users/:userId
GET /api/reports/summary
```

## Frontend Configuration

Update your frontend `config.js`:

```javascript
const CONFIG = {
    // Use backend proxy instead of direct EmailMCP
    BACKEND_URL: 'http://localhost:3000/api',
    USE_BACKEND_PROXY: true,
    
    // Google OAuth (still needed for frontend)
    GOOGLE_CLIENT_ID: 'your-google-client-id',
    
    // OAuth callback
    OAUTH_REDIRECT_URI: window.location.origin + '/callback.html',
};
```

## Deployment

### Deploy to Heroku

```bash
heroku create your-app-name
heroku config:set EMAILMCP_API_KEY=your-key
heroku config:set FRONTEND_URL=https://your-frontend.com
git push heroku main
```

### Deploy to Google Cloud Run

```bash
# Build image
gcloud builds submit --tag gcr.io/YOUR-PROJECT/emailmcp-proxy

# Deploy
gcloud run deploy emailmcp-proxy \
  --image gcr.io/YOUR-PROJECT/emailmcp-proxy \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars EMAILMCP_API_KEY=your-key
```

### Deploy to AWS Elastic Beanstalk

```bash
# Initialize
eb init -p node.js emailmcp-proxy

# Create environment and deploy
eb create emailmcp-proxy-env
eb deploy
```

### Deploy with Docker

```bash
# Build
docker build -t emailmcp-proxy .

# Run
docker run -p 3000:3000 \
  -e EMAILMCP_API_KEY=your-key \
  -e FRONTEND_URL=http://localhost:8000 \
  emailmcp-proxy
```

## Adding Authentication

To add JWT authentication to protect your endpoints:

```javascript
const jwt = require('jsonwebtoken');

// Middleware
function authenticateJWT(req, res, next) {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }
    
    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ error: 'Invalid token' });
        }
        req.user = user;
        next();
    });
}

// Apply to routes
app.post('/api/users/:userId/messages', authenticateJWT, async (req, res) => {
    // ... existing code
});
```

## Adding Rate Limiting

```bash
npm install express-rate-limit
```

```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100 // limit each IP to 100 requests per windowMs
});

app.use('/api/', limiter);
```

## Logging

Request logs are automatically printed to console. For production, consider:

```bash
npm install winston
```

```javascript
const winston = require('winston');

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.json(),
    transports: [
        new winston.transports.File({ filename: 'error.log', level: 'error' }),
        new winston.transports.File({ filename: 'combined.log' })
    ]
});

// Use in middleware
app.use((req, res, next) => {
    logger.info(`${req.method} ${req.path}`);
    next();
});
```

## Testing

Test the backend independently:

```bash
# Health check
curl http://localhost:3000/api/health

# OAuth authorize
curl -X POST http://localhost:3000/api/oauth/authorize \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test123","redirect_uri":"http://localhost:8000/callback.html"}'

# Get user profile
curl http://localhost:3000/api/users/test123/profile
```

## Troubleshooting

### CORS Issues

Make sure `FRONTEND_URL` is set correctly in `.env`:

```env
FRONTEND_URL=http://localhost:8000
```

For multiple origins:

```javascript
const allowedOrigins = [
    'http://localhost:8000',
    'https://your-production-domain.com'
];

app.use(cors({
    origin: function(origin, callback) {
        if (!origin || allowedOrigins.indexOf(origin) !== -1) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    credentials: true
}));
```

### Connection Refused

Check that:
1. Server is running (`npm start`)
2. Port is correct (default 3000)
3. No firewall blocking the port

### EmailMCP Service Unreachable

Verify:
1. EmailMCP service URL is correct
2. API key is valid
3. Your server can reach the EmailMCP service

## License

MIT
