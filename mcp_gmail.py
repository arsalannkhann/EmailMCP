import os
import json
import base64
import pickle
import psycopg2
import psycopg2.pool
from dotenv import load_dotenv
from flask import Flask, request, jsonify, redirect # Import Flask
from flask_cors import CORS
# from fastmcp import FastMCP # REMOVE THIS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ==============================================================================
# --- CONFIGURATION & INITIALIZATION ---
# ==============================================================================
load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__) # USE FLASK
CORS(app, resources={r"/*": {"origins": "*"}}) # Configure CORS with Flask

# --- Database Configuration ---
DB_NAME = os.getenv("DB_NAME", "user_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1269")
DB_HOST = os.getenv("DB_HOST", "localhost")

# --- Google OAuth Configuration ---


SCOPES = [
    'openid',
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
INTEGRATION_KEY = 'gmail_credentials'
REDIRECT_URI = os.getenv("MCP_REDIRECT_URI", "https://salesos.orionac.in/settings/oauth2callback")

# ==============================================================================
# --- DATABASE CONNECTION POOL ---
# ==============================================================================
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1, maxconn=10,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
    )
    print("MCP Server: Database connection pool created.")
except psycopg2.OperationalError as e:
    print(f"MCP Server: FATAL - Could not create database pool. Error: {e}")
    db_pool = None

def execute_db_query(query, params=(), fetch_one=False, is_write=False):
    """
    Executes a database query using a connection from the pool.
    Uses the connection as a context manager for robust transaction handling.
    """
    if not db_pool:
        raise ConnectionError("Database pool is not available.")
    conn = None
    try:
        conn = db_pool.getconn()
        # Use the connection as a context manager to automatically handle
        # commit on success or rollback on error.
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if is_write:
                    # The 'with conn:' block handles the commit.
                    return cur.rowcount
                if fetch_one:
                    return cur.fetchone()
                return cur.fetchall()
    except psycopg2.Error as e:
        print(f"MCP Server: Database query failed: {e}")
        # Re-raise the exception so the calling route can handle the HTTP response
        raise e
    finally:
        if conn:
            db_pool.putconn(conn)

# ==============================================================================
# --- OAUTH2 WEB FLOW ENDPOINTS ---
# ==============================================================================

@app.route("/connect/gmail", methods=['GET']) # USE STANDARD FLASK DECORATOR
def connect_gmail():
    """
    STEP 1 of OAuth Flow: Generate and return the Google authorization URL.
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline', prompt='consent', state=user_id
        )
        return jsonify({"status": "ok", "authorization_url": authorization_url})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": f"'{CREDENTIALS_FILE}' not found."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/oauth2callback", methods=['GET']) # USE STANDARD FLASK DECORATOR
def oauth2callback():
    """
    STEP 2 of OAuth Flow: Handle the callback from Google after user consent.
    """
    user_id = request.args.get('state')
    code = request.args.get('code')

    if not all([user_id, code]):
        return "<html><body><h1>Error: Missing required parameters.</h1></body></html>"

    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        service_email = user_info.get('email')

        if not service_email:
            return "<html><body><h1>Error: Could not retrieve email.</h1></body></html>"
            
        serialized_creds = pickle.dumps(creds)
        base64_encoded_creds = base64.b64encode(serialized_creds).decode('utf-8')

        query = """
            INSERT INTO crm_schema.user_integrations
            (user_id, integration_key, credentials, integration_email)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, integration_key)
            DO UPDATE SET credentials = EXCLUDED.credentials,
                          integration_email = EXCLUDED.integration_email,
                          updated_at = NOW();
        """
        execute_db_query(query, (int(user_id), INTEGRATION_KEY, base64_encoded_creds, service_email), is_write=True)
        
        return """
            <html><body style='font-family: sans-serif; text-align: center; padding: 40px;'>
                <h1>✅ Success!</h1>
                <p>Your Google account is connected. You can close this window.</p>
                <script>setTimeout(() => window.close(), 2000);</script>
            </body></html>
        """
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return f"<html><body><h1>Error: {e}</h1></body></html>"

@app.route("/disconnect/gmail", methods=['POST'])
def disconnect_gmail():
    """
    Deletes a user's Gmail integration credentials from the database.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400
        
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required in the request body"}), 400

    try:
        query = """
            DELETE FROM crm_schema.user_integrations
            WHERE user_id = %s AND integration_key = %s;
        """
        rows_deleted = execute_db_query(query, (int(user_id), INTEGRATION_KEY), is_write=True)
        
        if rows_deleted > 0:
            print(f"MCP Server: Disconnected Gmail for user_id: {user_id}")
            return jsonify({"status": "ok", "message": "Gmail integration successfully disconnected."})
        else:
            print(f"MCP Server: No Gmail integration to disconnect for user_id: {user_id}")
            return jsonify({"status": "ok", "message": "No active Gmail integration found to disconnect."})

    except Exception as e:
        print(f"MCP Server: Disconnect Gmail error for user {user_id}: {e}")
        return jsonify({"status": "error", "message": "An internal error occurred while trying to disconnect."}), 500

# ==============================================================================
# --- RUN APPLICATION ---
# ==============================================================================
if __name__ == "__main__":
    if not db_pool:
        print("MCP Host cannot start - database pool failed.")
    else:
        port = int(os.getenv("MCP_PORT", 5005))
        app.run(host="0.0.0.0", port=port) # USE STANDARD FLASK RUN
