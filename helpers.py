from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os, pickle, base64
import html2text
import base64
import os
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_email(subject, body):
    body = body[:3000]
    
    prompt = f"""You are an AI email classifier. Classify the following email into one of these types:
    - Job Interview or Next steps
    - Job Offer
    - Job rejection
    - Job application thank you / notification
    - Spam or Promo
    - Other

    If the subject contains phrases like "Your update for", it often indicates a status update (e.g. offer, interview, or rejection). Use this as a hint.

Subject: {subject}
Body: {body}

Respond with just the label."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def decode_base64(data):
    return base64.urlsafe_b64decode(data).decode(errors='ignore')

def extract_body(payload):
    # Try plain text
    if payload.get('body', {}).get('data'):
        return decode_base64(payload['body']['data'])

    parts = payload.get('parts', [])
    for part in parts:
        if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
            return decode_base64(part['body']['data'])
        elif part.get('parts'):
            for subpart in part['parts']:
                if subpart.get('mimeType') == 'text/plain' and subpart['body'].get('data'):
                    return decode_base64(subpart['body']['data'])

    # Fallback to HTML
    for part in parts:
        if part.get('mimeType') == 'text/html' and part['body'].get('data'):
            html = decode_base64(part['body']['data'])
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            h.body_width = 0
            return h.handle(html)

    return ''

def get_gmail_service():
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def get_category(msg_id):
    conn = sqlite3.connect("emails.db")
    c = conn.cursor()
    c.execute("SELECT category FROM seen_emails WHERE id = ?", (msg_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "Unknown"
