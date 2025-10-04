"""
Migrate any existing users to the new enhanced schema
"""

import os
from datetime import datetime, timezone
from google.cloud import firestore

def migrate_users():
    """Migrate existing users to new schema"""
    
    project_id = os.getenv('GOOGLE_PROJECT_ID', 'mcporionac')
    db = firestore.Client(project=project_id)
    
    print("Starting user migration...")
    
    users_ref = db.collection('users')
    users = users_ref.stream()
    
    migrated_count = 0
    
    for user_doc in users:
        user_data = user_doc.to_dict()
        user_id = user_doc.id
        
        # Skip sample documents
        if user_id.startswith('_sample'):
            continue
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Add missing fields with defaults
        updates = {}
        
        # Check and add missing fields
        if 'gmail_refresh_token_stored' not in user_data:
            updates['gmail_refresh_token_stored'] = user_data.get('gmail_connected', False)
        
        if 'monthly_email_count' not in user_data:
            updates['monthly_email_count'] = {}
        
        if 'account_status' not in user_data:
            updates['account_status'] = 'active'
        
        if 'subscription_tier' not in user_data:
            updates['subscription_tier'] = 'free'
        
        if 'rate_limit_quota' not in user_data:
            updates['rate_limit_quota'] = 100
        
        if 'rate_limit_used' not in user_data:
            updates['rate_limit_used'] = 0
        
        if 'rate_limit_reset_at' not in user_data:
            updates['rate_limit_reset_at'] = current_time
        
        # Add/update metadata
        if '_metadata' not in user_data:
            updates['_metadata'] = {
                'collection': 'users',
                'document_id': user_id,
                'created_at': user_data.get('created_at', current_time),
                'updated_at': current_time,
                'version': 1
            }
        else:
            updates['_metadata.updated_at'] = current_time
            updates['_metadata.version'] = user_data.get('_metadata', {}).get('version', 0) + 1
        
        # Update timestamp
        updates['updated_at'] = current_time
        
        if updates:
            users_ref.document(user_id).update(updates)
            print(f"✓ Migrated user: {user_id} - {user_data.get('email', 'No email')}")
            migrated_count += 1
        else:
            print(f"• User already up to date: {user_id}")
    
    print(f"\n🎉 Migration completed! Migrated {migrated_count} users.")

if __name__ == "__main__":
    migrate_users()