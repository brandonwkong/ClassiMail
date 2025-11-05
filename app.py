from flask import Flask, jsonify
from flask_cors import CORS
import sys
from helpers import extract_body, get_gmail_service, classify_email, get_category
from database import is_seen, mark_seen, get_saved_info
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
            subject, sender_name, category = get_saved_info(msg_id)
            email_list.append({
                "id": msg_id,
                 "sender_name": sender_name,
                "subject": subject,
                "category": category
            })
            continue
        else:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = msg_data['payload'].get('headers', [])
            sender_name = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown Sender)')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            snippet = msg_data.get('snippet', '')
            body = extract_body(msg_data['payload'])
            label_data = classify_email(subject, body)
            category = label_data
            print(f"[DEBUG SAVE] ID: {msg_id}, Subject: {subject}, Category: {category}")
            sys.stdout.flush()
            mark_seen(msg_id, sender_name, subject, category)

        email_list.append({
            "id": msg_id,
            "sender_name": sender_name,
            "subject": subject,
            "snippet": snippet,
            "body": body,
            "category": category,
        })
    REQUEST_LATENCY.labels('/emails').observe(time.time() - start)
    return jsonify(email_list)

if __name__ == '__main__':
    app.run(port=5000, debug=True)


