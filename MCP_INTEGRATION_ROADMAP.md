# MCP Integration Roadmap & Recommendations

## 🎯 PHASE 1: IMMEDIATE FIXES (Week 1-2)

### 1. Standardize OAuth Scopes
**Problem**: Scope mismatch between Flask and FastAPI MCP
**Solution**: Align scopes across both systems

```python
# Recommended unified scopes:
UNIFIED_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly', 
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
```

### 2. Migrate Flask MCP to FastAPI Architecture
**Current**: Flask app with PostgreSQL
**Target**: FastAPI endpoint within existing MCP service

```python
# Add to src/mcp/api/v1/legacy_bridge.py
@router.post("/legacy/connect/gmail")
async def legacy_connect_gmail(user_id: str):
    """Bridge endpoint for legacy OAuth flow"""
    # Redirect to modern OAuth flow
    service = MultiTenantEmailService()
    oauth_url = await service.generate_oauth_url(user_id, redirect_uri)
    return {"authorization_url": oauth_url}
```

### 3. Credential Migration Strategy
**Current**: Pickled credentials in PostgreSQL
**Target**: JSON credentials in GCP Secret Manager

```python
# Migration script needed:
async def migrate_credentials():
    # 1. Read from PostgreSQL user_integrations
    # 2. Unpickle and convert to JSON
    # 3. Store in GCP Secret Manager
    # 4. Update Firestore user profiles
```

## 🏗️ PHASE 2: ARCHITECTURE CONSOLIDATION (Week 3-4)

### 1. Unified MCP Service
**Strategy**: Single FastAPI service handling all MCP functionality

```python
# Proposed structure:
src/mcp/
├── api/v1/
│   ├── oauth.py          # OAuth flows (modern + legacy bridge)
│   ├── messages.py       # Email operations
│   ├── multi_tenant.py   # Multi-tenant features
│   └── integrations.py   # External system bridges
├── services/
│   ├── oauth_service.py  # Unified OAuth handling
│   ├── email_service.py  # Email operations
│   └── bridge_service.py # Legacy system bridges
```

### 2. Database Consolidation
**Strategy**: Firestore as primary, PostgreSQL bridge for legacy

```python
# Firestore collections:
- users/              # User profiles
- oauth_tokens/       # OAuth credentials
- email_logs/         # Email transaction logs  
- integrations/       # External system configs
- migration_status/   # Migration tracking
```

### 3. API Versioning Strategy
```python
# URL structure:
/v1/oauth/authorize     # Modern OAuth
/v1/oauth/callback      # Modern callback
/v1/legacy/connect      # Legacy bridge
/v1/legacy/callback     # Legacy bridge callback
```

## 🔧 PHASE 3: ADVANCED FEATURES (Week 5-8)

### 1. Multi-Provider Support
**Beyond Gmail**: Support Outlook, Yahoo, custom SMTP

```python
# Provider abstraction:
class OAuthProviderFactory:
    @staticmethod
    def get_provider(provider_type: str, user_id: str):
        if provider_type == "gmail":
            return GmailOAuthProvider(user_id)
        elif provider_type == "outlook":
            return OutlookOAuthProvider(user_id)
        # etc.
```

### 2. Advanced OAuth Features
- **Refresh token rotation**
- **Scope-based permissions**
- **Multi-account support per user**
- **OAuth token health monitoring**

### 3. Enhanced Security
```python
# Security improvements:
- JWT-based API authentication
- OAuth state parameter validation
- PKCE (Proof Key for Code Exchange)
- Rate limiting per user/IP
- Audit logging for all OAuth operations
```

## 📊 PHASE 4: MONITORING & OPTIMIZATION (Week 9-12)

### 1. Analytics Dashboard
- **OAuth success/failure rates**
- **Token refresh patterns**
- **Email sending statistics**
- **User engagement metrics**

### 2. Performance Optimization
- **Connection pooling**
- **Credential caching**
- **Async batch operations**
- **CDN for static assets**

### 3. Disaster Recovery
- **Credential backup/restore**
- **Database replication**
- **Health checks and alerting**
- **Graceful degradation**

## 🎯 KEY MIGRATION PRIORITIES

### HIGH PRIORITY (Do First):
1. ✅ Fix OAuth scope alignment
2. ✅ Migrate Flask endpoints to FastAPI
3. ✅ Secure credential storage migration
4. ✅ Database consolidation planning

### MEDIUM PRIORITY (Do Next):
1. 🔄 Legacy system bridges
2. 🔄 API versioning implementation
3. 🔄 Enhanced security features
4. 🔄 Multi-provider support

### LOW PRIORITY (Future):
1. 📊 Advanced analytics
2. 📊 Performance optimization
3. 📊 Disaster recovery
4. 📊 Third-party integrations

## 🚨 IMMEDIATE ACTION ITEMS

### This Week:
1. **Standardize OAuth scopes** across both systems
2. **Create migration script** for credential transfer
3. **Add legacy bridge endpoints** to FastAPI MCP
4. **Test OAuth flow compatibility**

### Next Week:
1. **Deploy unified MCP service**
2. **Migrate existing users gradually**
3. **Monitor OAuth success rates**
4. **Update documentation**

## 📋 COMPATIBILITY MATRIX

| Feature | Flask MCP | FastAPI MCP | Unified Target |
|---------|-----------|-------------|----------------|
| OAuth Flow | ✅ Working | ✅ Working | ✅ Consolidated |
| Credentials | ⚠️ Pickled | ✅ JSON | ✅ JSON + Encrypted |
| Database | PostgreSQL | Firestore | Firestore Primary |
| Authentication | None | Bearer Token | JWT + Bearer |
| Multi-tenant | ❌ No | ✅ Yes | ✅ Enhanced |
| Analytics | ❌ No | ✅ Yes | ✅ Advanced |
| Monitoring | ❌ No | ✅ Basic | ✅ Comprehensive |

## 🔍 TECHNICAL DEBT RESOLUTION

### Security Issues:
- Replace pickled credentials with encrypted JSON
- Add proper authentication to Flask endpoints
- Implement OAuth state validation
- Add rate limiting and abuse protection

### Architecture Issues:
- Consolidate database systems
- Standardize API patterns
- Implement proper error handling
- Add comprehensive logging

### Operational Issues:
- Add health checks and monitoring
- Implement graceful shutdown
- Add backup and recovery procedures
- Document deployment processes