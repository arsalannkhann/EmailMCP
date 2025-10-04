#!/bin/bash

# OAuth Flow Test Script
echo "🔧 Testing OAuth Flow Fixes"
echo "=========================="

echo "1. Testing EmailMCP Service Health..."
HEALTH=$(curl -s https://emailmcp-hcnqp547xa-uc.a.run.app/health | jq -r .status)
if [ "$HEALTH" = "healthy" ]; then
    echo "✅ EmailMCP Service: $HEALTH"
else
    echo "❌ EmailMCP Service: Down"
    exit 1
fi

echo ""
echo "2. Testing OAuth Authorization..."
OAUTH_RESPONSE=$(curl -s -X POST "https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/authorize" \
  -H "Authorization: Bearer emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_oauth_fix",
    "redirect_uri": "http://localhost:8080/callback.html"
  }')

if echo "$OAUTH_RESPONSE" | grep -q "authorization_url"; then
    echo "✅ OAuth Authorization: Working"
    AUTH_URL=$(echo "$OAUTH_RESPONSE" | jq -r .authorization_url)
    echo "   🔗 Authorization URL generated successfully"
else
    echo "❌ OAuth Authorization: Failed"
    echo "   Response: $OAUTH_RESPONSE"
    exit 1
fi

echo ""
echo "3. Testing OAuth Callback Format..."
# Simulate callback with test parameters
CALLBACK_RESPONSE=$(curl -s -X POST "https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback" \
  -H "Authorization: Bearer emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "code=test_code&state=test_user_oauth_fix")

if echo "$CALLBACK_RESPONSE" | grep -q "error\|detail"; then
    echo "⚠️  OAuth Callback: Expected error (invalid code)"
    echo "   This is normal - real OAuth code needed"
else
    echo "✅ OAuth Callback: Endpoint accessible"
fi

echo ""
echo "4. Frontend Configuration:"
echo "   📍 Service URL: https://emailmcp-hcnqp547xa-uc.a.run.app"
echo "   🔑 API Key: emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw"
echo "   🔄 Redirect URI: http://localhost:8080/callback.html"
echo "   🌐 Google Client ID: 480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com"

echo ""
echo "🚀 Starting Frontend Server on http://localhost:8080"
echo "   Press Ctrl+C to stop"

cd /Users/arsalankhan/Documents/GitHub/EmailMCP/sample-frontend
python3 -m http.server 8080