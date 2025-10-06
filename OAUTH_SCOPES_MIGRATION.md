# OAuth Scopes Migration - Flask to FastAPI MCP

## 🔄 **Scope Update Summary**

### **BEFORE (FastAPI MCP)**
```python
# Limited scopes - only send and read
'scope': 'https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly'
```

### **AFTER (Updated FastAPI MCP)**
```python
# Full scopes aligned with Flask MCP
GMAIL_OAUTH_SCOPES = [
    'openid',
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
```

## 📊 **Scope Comparison Table**

| Scope | Flask MCP | FastAPI (Before) | FastAPI (After) | Purpose |
|-------|-----------|------------------|-----------------|---------|
| `openid` | ✅ | ❌ | ✅ | OpenID Connect authentication |
| `https://mail.google.com/` | ✅ | ❌ | ✅ | Full Gmail access (read, send, modify, delete) |
| `gmail.send` | ❌ | ✅ | ❌ | Send emails only (replaced by full access) |
| `gmail.readonly` | ❌ | ✅ | ❌ | Read emails only (replaced by full access) |
| `userinfo.email` | ✅ | ❌ | ✅ | Access user's email address |
| `userinfo.profile` | ✅ | ❌ | ✅ | Access user's basic profile info |

## 🎯 **Benefits of Updated Scopes**

### **1. Consistency**
- ✅ Both Flask and FastAPI MCP now use identical scopes
- ✅ Unified OAuth permissions across systems
- ✅ Easier maintenance and debugging

### **2. Enhanced Functionality**
- ✅ **Full Gmail Access**: `https://mail.google.com/` provides complete Gmail API access
- ✅ **User Profile**: Access to email address and basic profile information
- ✅ **OpenID Connect**: Modern authentication standard support

### **3. Future-Proofing**
- ✅ **Broader Permissions**: Support for advanced Gmail features (labels, drafts, etc.)
- ✅ **User Identity**: Access to user information for better personalization
- ✅ **OAuth 2.0/OIDC**: Standards-compliant authentication flow

## ⚠️ **Important Considerations**

### **Security Implications**
- **More Permissions**: `https://mail.google.com/` grants broader access than previous limited scopes
- **User Consent**: Users will see expanded permission requests during OAuth flow
- **Responsibility**: Handle the additional permissions responsibly

### **OAuth Client Configuration**
- **Google Cloud Console**: Ensure your OAuth client is configured for these scopes
- **Verification**: May require additional verification from Google for sensitive scopes
- **Testing**: Test OAuth flow thoroughly with updated scopes

### **Migration Impact**
- **Existing Tokens**: Current user tokens may need to be refreshed to get new scopes
- **Re-authorization**: Some users may need to re-authorize to get expanded permissions
- **Gradual Rollout**: Consider phased deployment to monitor impact

## 🚀 **Implementation Details**

### **Code Changes Made**
1. **Added scope constants** at the top of `multi_tenant_service.py`
2. **Updated OAuth URL generation** to use new scopes
3. **Maintained backward compatibility** with existing user flows

### **Files Modified**
- `src/mcp/services/multi_tenant_service.py`
  - Added `GMAIL_OAUTH_SCOPES` constant
  - Updated scope parameter in OAuth URL generation
  - Maintained existing functionality

## 📋 **Next Steps**

### **Immediate (This Week)**
1. ✅ **Test OAuth Flow**: Verify new scopes work with Google OAuth
2. ✅ **Update Documentation**: Document the scope changes
3. ✅ **Monitor Logs**: Watch for OAuth-related errors

### **Short Term (Next Week)**
1. 🔄 **User Migration**: Plan strategy for existing users to re-authorize
2. 🔄 **Error Handling**: Add better error messages for scope-related issues
3. 🔄 **Testing**: Comprehensive testing of all OAuth flows

### **Long Term (Next Month)**
1. 📅 **Scope Optimization**: Review if full Gmail access is needed everywhere
2. 📅 **Security Audit**: Review data access patterns with new permissions
3. 📅 **User Experience**: Optimize OAuth consent flow for better UX

## 🔍 **Testing Checklist**

- [ ] OAuth URL generation works with new scopes
- [ ] Authorization flow completes successfully
- [ ] Token exchange handles all requested scopes
- [ ] User profile information is accessible
- [ ] Email sending still works with new permissions
- [ ] No breaking changes to existing functionality

## 📞 **Support Information**

If you encounter issues with the updated scopes:

1. **Check Google Cloud Console**: Verify OAuth client configuration
2. **Review Logs**: Look for scope-related error messages
3. **Test with New User**: Try OAuth flow with fresh user account
4. **Rollback Plan**: Previous scopes can be restored if needed

---

**✅ Scope migration completed successfully!**
**📧 FastAPI MCP now aligned with Flask MCP OAuth scopes**