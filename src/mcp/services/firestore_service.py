"""
Firestore service for EmailMCP application data management
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ..core.config import settings
from ..core.logging import log


class FirestoreService:
    """Service for managing application data in Firestore"""
    
    def __init__(self):
        """Initialize Firestore client"""
        self.project_id = settings.gcp_project_id or os.getenv('GOOGLE_PROJECT_ID', 'mcporionac')
        self.database_name = settings.firestore_database if hasattr(settings, 'firestore_database') else "(default)"
        
        try:
            if settings.use_firestore if hasattr(settings, 'use_firestore') else True:
                self.db = firestore.Client(project=self.project_id, database=self.database_name)
                log.info(f"Firestore client initialized for project: {self.project_id}, database: {self.database_name}")
            else:
                log.warning("Firestore disabled by configuration")
                self.db = None
        except Exception as e:
            log.error(f"Failed to initialize Firestore client: {e}")
            self.db = None
    
    async def create_user_profile(self, user_data: Dict[str, Any]) -> bool:
        """
        Create or update user profile in Firestore
        
        Args:
            user_data: User profile data
            
        Returns:
            True if successful
        """
        if not self.db:
            log.warning("Firestore client not available")
            return False
            
        try:
            user_id = user_data.get('id') or user_data.get('user_id')
            if not user_id:
                log.error("User ID is required for profile creation")
                return False
            
            # Add metadata and timestamps
            current_time = datetime.now(timezone.utc).isoformat()
            profile_data = {
                **user_data,
                'updated_at': current_time,
                '_metadata': {
                    'collection': 'users',
                    'document_id': user_id,
                    'updated_at': current_time,
                    'version': 1
                }
            }
            
            # Set created_at only for new users
            user_ref = self.db.collection('users').document(user_id)
            doc = user_ref.get()
            
            if not doc.exists:
                profile_data['created_at'] = current_time
                profile_data['_metadata']['created_at'] = current_time
                log.info(f"Creating new user profile: {user_id}")
            else:
                # Preserve original created_at
                existing_data = doc.to_dict()
                profile_data['created_at'] = existing_data.get('created_at', current_time)
                log.info(f"Updating existing user profile: {user_id}")
            
            user_ref.set(profile_data, merge=True)
            return True
            
        except Exception as e:
            log.error(f"Failed to create/update user profile: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from Firestore
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile data or None if not found
        """
        if not self.db:
            log.warning("Firestore client not available")
            return None
            
        try:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            log.error(f"Failed to get user profile {user_id}: {e}")
            return None
    
    async def update_user_stats(self, user_id: str, email_count_delta: int = 1) -> bool:
        """
        Update user email statistics
        
        Args:
            user_id: User identifier
            email_count_delta: Number to add to email count (default: 1)
            
        Returns:
            True if successful
        """
        if not self.db:
            log.warning("Firestore client not available")
            return False
            
        try:
            user_ref = self.db.collection('users').document(user_id)
            current_time = datetime.now(timezone.utc)
            current_month = current_time.strftime('%Y-%m')
            
            # Use Firestore transaction to ensure consistency
            @firestore.transactional
            def update_stats(transaction):
                doc = user_ref.get(transaction=transaction)
                if doc.exists:
                    data = doc.to_dict()
                    
                    # Update total count
                    new_total = data.get('total_emails_sent', 0) + email_count_delta
                    
                    # Update monthly count
                    monthly_counts = data.get('monthly_email_count', {})
                    monthly_counts[current_month] = monthly_counts.get(current_month, 0) + email_count_delta
                    
                    # Update fields
                    updates = {
                        'total_emails_sent': new_total,
                        'monthly_email_count': monthly_counts,
                        'last_email_sent_at': current_time.isoformat(),
                        'updated_at': current_time.isoformat()
                    }
                    
                    transaction.update(user_ref, updates)
                    return True
                return False
            
            transaction = self.db.transaction()
            result = update_stats(transaction)
            
            if result:
                log.info(f"Updated email stats for user {user_id}: +{email_count_delta}")
            return result
            
        except Exception as e:
            log.error(f"Failed to update user stats for {user_id}: {e}")
            return False
    
    async def log_email_transaction(
        self, 
        user_id: str, 
        email_data: Dict[str, Any], 
        result: Dict[str, Any]
    ) -> bool:
        """
        Log email transaction to Firestore
        
        Args:
            user_id: User identifier
            email_data: Email request data
            result: Email send result
            
        Returns:
            True if successful
        """
        if not self.db:
            log.warning("Firestore client not available")
            return False
            
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            
            # Create email log entry
            log_entry = {
                # User Reference
                'user_id': user_id,
                'user_email': email_data.get('from_email', ''),
                
                # Email Details
                'from_email': email_data.get('from_email', ''),
                'to_emails': email_data.get('to_emails', []),
                'cc_emails': email_data.get('cc_emails', []),
                'bcc_emails': email_data.get('bcc_emails', []),
                'subject': email_data.get('subject', ''),
                'body_preview': (email_data.get('body', '') or email_data.get('html_body', ''))[:100],
                'body_type': 'html' if email_data.get('html_body') else 'text',
                'body_length': len(email_data.get('body', '') or email_data.get('html_body', '')),
                
                # Message Tracking
                'message_id': result.get('message_id', ''),
                'gmail_thread_id': result.get('thread_id', ''),
                'gmail_message_id': result.get('message_id', ''),
                
                # Status Tracking
                'status': result.get('status', 'unknown'),
                'error_message': result.get('error', None),
                'error_code': None,
                'retry_count': 0,
                'max_retries': 3,
                
                # Metadata
                'email_size_bytes': len(str(email_data)),
                'attachments_count': len(email_data.get('attachments', [])),
                'priority': 'normal',
                'delivery_method': 'gmail_api',
                
                # Timestamps
                'sent_at': current_time,
                'created_at': current_time,
                
                # Metadata
                '_metadata': {
                    'collection': 'email_logs',
                    'created_at': current_time,
                    'indexed_fields': ['user_id', 'sent_at', 'status'],
                    'auto_generated': True
                }
            }
            
            # Add delivered_at if successful
            if result.get('status') == 'sent':
                log_entry['delivered_at'] = current_time
            
            # Store in Firestore
            self.db.collection('email_logs').add(log_entry)
            
            log.info(f"Logged email transaction for user {user_id}: {result.get('status')}")
            return True
            
        except Exception as e:
            log.error(f"Failed to log email transaction for {user_id}: {e}")
            return False
    
    async def get_user_email_logs(
        self, 
        user_id: str, 
        limit: int = 50, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get email logs for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of logs to return
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of email log entries
        """
        if not self.db:
            log.warning("Firestore client not available")
            return []
            
        try:
            query = self.db.collection('email_logs').where(
                filter=FieldFilter('user_id', '==', user_id)
            ).order_by('sent_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            # Add date filters if provided
            if start_date:
                query = query.where(filter=FieldFilter('sent_at', '>=', start_date.isoformat()))
            if end_date:
                query = query.where(filter=FieldFilter('sent_at', '<=', end_date.isoformat()))
            
            docs = query.stream()
            logs = []
            
            for doc in docs:
                log_data = doc.to_dict()
                log_data['id'] = doc.id
                logs.append(log_data)
            
            log.info(f"Retrieved {len(logs)} email logs for user {user_id}")
            return logs
            
        except Exception as e:
            log.error(f"Failed to get email logs for {user_id}: {e}")
            return []
    
    async def get_user_analytics(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get email analytics for a user
        
        Args:
            user_id: User identifier
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            Analytics data
        """
        if not self.db:
            log.warning("Firestore client not available")
            return {
                'total_emails': 0,
                'successful_emails': 0,
                'failed_emails': 0,
                'success_rate': 0.0,
                'emails_by_day': [],
                'top_recipients': []
            }
            
        try:
            # Query email logs in date range
            query = self.db.collection('email_logs').where(
                filter=FieldFilter('user_id', '==', user_id)
            ).where(
                filter=FieldFilter('sent_at', '>=', start_date.isoformat())
            ).where(
                filter=FieldFilter('sent_at', '<=', end_date.isoformat())
            )
            
            docs = query.stream()
            logs = [doc.to_dict() for doc in docs]
            
            # Calculate analytics
            total_emails = len(logs)
            successful_emails = len([log for log in logs if log.get('status') == 'sent'])
            failed_emails = total_emails - successful_emails
            success_rate = (successful_emails / total_emails * 100) if total_emails > 0 else 0.0
            
            # Group by day
            emails_by_day = {}
            recipient_counts = {}
            
            for log_entry in logs:
                # Group by day
                sent_date = log_entry.get('sent_at', '')[:10]  # YYYY-MM-DD
                if sent_date not in emails_by_day:
                    emails_by_day[sent_date] = {'date': sent_date, 'count': 0}
                emails_by_day[sent_date]['count'] += 1
                
                # Count recipients
                for recipient in log_entry.get('to_emails', []):
                    recipient_counts[recipient] = recipient_counts.get(recipient, 0) + 1
            
            # Top recipients
            top_recipients = [
                {'email': email, 'count': count}
                for email, count in sorted(recipient_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            analytics = {
                'total_emails': total_emails,
                'successful_emails': successful_emails,
                'failed_emails': failed_emails,
                'success_rate': round(success_rate, 2),
                'emails_by_day': list(emails_by_day.values()),
                'top_recipients': top_recipients
            }
            
            log.info(f"Generated analytics for user {user_id}: {total_emails} emails")
            return analytics
            
        except Exception as e:
            log.error(f"Failed to get analytics for {user_id}: {e}")
            return {
                'total_emails': 0,
                'successful_emails': 0,
                'failed_emails': 0,
                'success_rate': 0.0,
                'emails_by_day': [],
                'top_recipients': []
            }
    
    async def get_platform_metrics(self, date: datetime) -> Dict[str, Any]:
        """
        Get platform-wide metrics for a specific date
        
        Args:
            date: Date for metrics
            
        Returns:
            Platform metrics
        """
        if not self.db:
            log.warning("Firestore client not available")
            return {}
            
        try:
            date_str = date.strftime('%Y-%m-%d')
            
            # Get or create daily metrics document
            metrics_ref = self.db.collection('system_metrics').document(date_str)
            doc = metrics_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                # Calculate metrics for the day
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Count emails sent on this day
                emails_query = self.db.collection('email_logs').where(
                    filter=FieldFilter('sent_at', '>=', start_of_day.isoformat())
                ).where(
                    filter=FieldFilter('sent_at', '<=', end_of_day.isoformat())
                )
                
                email_docs = list(emails_query.stream())
                emails_sent = len(email_docs)
                emails_failed = len([doc for doc in email_docs if doc.to_dict().get('status') != 'sent'])
                success_rate = ((emails_sent - emails_failed) / emails_sent * 100) if emails_sent > 0 else 0.0
                
                # Count active users (users who sent emails)
                active_users = len(set(doc.to_dict().get('user_id') for doc in email_docs))
                
                # Get total users count
                users_query = self.db.collection('users')
                total_users = len(list(users_query.stream()))
                
                metrics = {
                    'date': date_str,
                    'total_users': total_users,
                    'active_users': active_users,
                    'new_users': 0,  # Would need user creation tracking
                    'emails_sent': emails_sent,
                    'emails_failed': emails_failed,
                    'success_rate': round(success_rate, 2),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    '_metadata': {
                        'collection': 'system_metrics',
                        'document_id': date_str,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                }
                
                # Store calculated metrics
                metrics_ref.set(metrics)
                return metrics
                
        except Exception as e:
            log.error(f"Failed to get platform metrics for {date}: {e}")
            return {}