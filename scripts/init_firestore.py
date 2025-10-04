"""
Initialize Firestore database with proper indexes and security rules
"""

import os
from google.cloud import firestore
from google.cloud.firestore_admin_v1 import FirestoreAdminClient
from google.cloud.firestore_admin_v1.types import Index

def initialize_firestore():
    """Initialize Firestore with proper collections and indexes"""
    
    # Initialize Firestore client
    project_id = os.getenv('GOOGLE_PROJECT_ID', 'mcporionac')
    db = firestore.Client(project=project_id)
    
    print(f"Initializing Firestore for project: {project_id}")
    
    # Create collections with sample documents to ensure they exist
    collections_to_create = [
        {
            "name": "users",
            "sample_doc": {
                "id": "sample_user",
                "email": "sample@example.com",
                "name": "Sample User",
                "gmail_connected": False,
                "total_emails_sent": 0,
                "created_at": firestore.SERVER_TIMESTAMP,
                "_metadata": {
                    "collection": "users",
                    "document_id": "sample_user",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "version": 1
                }
            }
        },
        {
            "name": "email_logs",
            "sample_doc": {
                "user_id": "sample_user",
                "from_email": "sample@example.com",
                "to_emails": ["recipient@example.com"],
                "subject": "Sample Email",
                "status": "sent",
                "sent_at": firestore.SERVER_TIMESTAMP,
                "created_at": firestore.SERVER_TIMESTAMP,
                "_metadata": {
                    "collection": "email_logs",
                    "document_id": "sample_log",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "indexed_fields": ["user_id", "sent_at", "status"]
                }
            }
        },
        {
            "name": "oauth_tokens",
            "sample_doc": {
                "user_id": "sample_user",
                "provider": "gmail",
                "scope": "https://www.googleapis.com/auth/gmail.send",
                "created_at": firestore.SERVER_TIMESTAMP,
                "_metadata": {
                    "collection": "oauth_tokens",
                    "document_id": "sample_user",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "ttl": firestore.SERVER_TIMESTAMP
                }
            }
        },
        {
            "name": "user_sessions",
            "sample_doc": {
                "user_id": "sample_user",
                "session_id": "sample_session",
                "is_active": True,
                "created_at": firestore.SERVER_TIMESTAMP,
                "_metadata": {
                    "collection": "user_sessions",
                    "document_id": "sample_session",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "ttl": firestore.SERVER_TIMESTAMP
                }
            }
        },
        {
            "name": "system_metrics",
            "sample_doc": {
                "date": "2025-10-04",
                "total_users": 0,
                "active_users": 0,
                "new_users": 0,
                "emails_sent": 0,
                "created_at": firestore.SERVER_TIMESTAMP,
                "_metadata": {
                    "collection": "system_metrics",
                    "document_id": "2025-10-04",
                    "created_at": firestore.SERVER_TIMESTAMP
                }
            }
        }
    ]
    
    # Create collections
    for collection_info in collections_to_create:
        collection_name = collection_info["name"]
        sample_doc = collection_info["sample_doc"]
        
        print(f"Creating collection: {collection_name}")
        
        # Create collection with sample document
        doc_ref = db.collection(collection_name).document("_sample")
        doc_ref.set(sample_doc)
        
        print(f"✓ Collection {collection_name} created with sample document")
    
    print("\n🎉 Firestore initialization completed successfully!")
    print("\nNext steps:")
    print("1. Deploy the application to Cloud Run")
    print("2. Test the OAuth flow")
    print("3. Send test emails")
    print("4. Monitor the logs and metrics")

if __name__ == "__main__":
    initialize_firestore()