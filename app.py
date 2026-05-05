from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
from helpers import extract_body, get_gmail_service, classify_email, get_category
from database import (
    is_seen, mark_seen, get_saved_info, log_interaction,
    save_email_full, get_interaction_stats, get_detailed_stats, update_email_features, get_email_ctr
)
from features import extract_features
from ranker import compute_rank_score, rank_emails
from flask import redirect
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
from prometheus_client import Counter, Histogram, generate_latest
from flask import Response



app = Flask(__name__)
CORS(app)

REQUEST_COUNT = Counter('flask_requests_total', 'Total number of HTTP requests', ['endpoint'])
REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Request latency in seconds', ['endpoint'])
EMAILS_PROCESSED = Counter('emails_processed_total', 'Total emails processed')

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


@app.route('/auth')
def auth():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=8081)  # opens Google login in browser
    with open('token.pkl', 'wb') as token:
        pickle.dump(creds, token)
    return redirect('http://localhost:3000?logged_in=true')


@app.route('/emails')
def get_emails():

    import time
    start = time.time()
    REQUEST_COUNT.labels('/emails').inc()

    service = get_gmail_service()
    result = service.users().messages().list(userId='me', maxResults=15, labelIds=['INBOX']).execute()
    messages = result.get('messages', [])

    email_list = []

    for msg in messages:
        EMAILS_PROCESSED.inc()
        msg_id = msg["id"]

        if is_seen(msg_id):
            # Get cached data including features and body
            subject, sender_name, category, old_rank_score, features, body = get_saved_info(msg_id)
            
            # Add/update CTR from interactions
            features['ctr'] = get_email_ctr(msg_id)
            
            # Recompute rank_score with current ranking logic
            rank_score = compute_rank_score(features)
            
            print(f"[DEBUG] Recomputing rank for {msg_id}: Old={old_rank_score}, New={rank_score}")
            
            # Update DB if rank changed (to keep it fresh)
            if abs(rank_score - (old_rank_score or 0)) > 0.001:  # small threshold for floating point
                update_email_features(msg_id, rank_score, features)
            
            email_list.append({
                "id": msg_id,
                "sender_name": sender_name,
                "subject": subject,
                "body": body,
                "category": category,
                "rank_score": rank_score,
                "features": features,
            })
            continue
        else:
            # Fetch full email data
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = msg_data['payload'].get('headers', [])
            sender_name = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown Sender)')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            snippet = msg_data.get('snippet', '')
            body = extract_body(msg_data['payload'])
            internal_date = msg_data.get('internalDate')

            # Check for attachments
            parts = msg_data['payload'].get('parts', [])
            has_attachment = any(
                p.get('filename') and p.get('body', {}).get('attachmentId')
                for p in parts
            )

            # Classify with GPT
            category = classify_email(subject, body)

            # Extract features
            features = extract_features(
                subject=subject,
                body=body,
                sender=sender_name,
                category=category,
                internal_date_ms=internal_date,
                has_attachment=has_attachment
            )
            
            # Add CTR from interactions
            features['ctr'] = get_email_ctr(msg_id)

            # Compute rank score
            rank_score = compute_rank_score(features)

            print(f"[DEBUG] ID: {msg_id}, Subject: {subject[:50]}, Category: {category}, Rank: {rank_score}")
            sys.stdout.flush()

            # Save to database with features and body
            save_email_full(msg_id, sender_name, subject, category, rank_score, features, body)

        email_list.append({
            "id": msg_id,
            "sender_name": sender_name,
            "subject": subject,
            "snippet": snippet,
            "body": body,
            "category": category,
            "rank_score": rank_score,
            "features": features,
        })

    # Add position for CTR tracking (original Gmail order)
    for i, email in enumerate(email_list):
        email['position'] = i + 1

    REQUEST_LATENCY.labels('/emails').observe(time.time() - start)
    return jsonify(email_list)

@app.route('/interact', methods=['POST'])
def record_interaction():
    """
    Log user interaction with an email (for CTR training).

    Expected JSON body:
    {
        "email_id": "abc123",
        "action": "click" | "open" | "skip" | "ignore",
        "position": 1,
        "time_spent_ms": 5000
    }
    """
    REQUEST_COUNT.labels('/interact').inc()

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    email_id = data.get('email_id')
    action = data.get('action')

    if not email_id or not action:
        return jsonify({"error": "email_id and action required"}), 400

    position = data.get('position')
    time_spent = data.get('time_spent_ms')

    log_interaction(email_id, action, position, time_spent)

    return jsonify({"status": "ok"})


@app.route('/stats')
def get_stats():
    """Get interaction statistics (for debugging/monitoring)."""
    stats = get_interaction_stats()
    return jsonify(stats)


@app.route('/stats/detailed')
def get_stats_detailed():
    """
    Get detailed interaction stats including time spent.

    Returns:
        - counts: click/open/skip counts
        - time_spent: avg/min/max time spent on emails
        - top_by_time: emails with longest view time
        - recent: last 15 interactions
        - ctr_by_position: click-through rate by position (for position bias)
        - ctr_by_category: click-through rate by email category
    """
    stats = get_detailed_stats()
    return jsonify(stats)


if __name__ == '__main__':
    app.run(port=5000, debug=True)


