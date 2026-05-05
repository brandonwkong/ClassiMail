# #This is for future, kind of like a second layer if non embededings does not work well or billing gets too high

# def embed(text):
#     resp = client.embeddings.create(
#         model="text-embedding-3-small",
#         input=text
#     )
#     return np.array(resp.data[0].embedding)

# def cosine_similarity(a, b):
#     return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# EXAMPLES = {
#     "Interview Invitation / Next step": ["We would like to schedule an interview.", "Please sign up for a time slot", "Next steps for you", "Complete this online assessment", 
#     ], 
#     "Job Offer": "We are pleased to offer you the position.",
#     "Rejection": ["Thank you for applying, but we’ve gone with another candidate.", "Unfortunately, we will not be moving forward with your application, but we appreciate your time and interest", "We will be moving forward with another candidate"
#     ],
#     "General Update": "Here’s an update regarding your application or status.",
#     "Spam or Promo": [
#         "Get 50% off or join our promo today.", "Unlock premium features now!",
#     ],
#     "Other": "This is a miscellaneous message not related to jobs."
# }

# EXAMPLE_EMBEDDINGS = {}
# for label, examples in EXAMPLES.items():
#     if isinstance(examples, str):
#         examples = [examples]
#     vecs = [embed(ex) for ex in examples]
#     avg_vec = np.mean(vecs, axis=0)
#     EXAMPLE_EMBEDDINGS[label] = avg_vec

# def classify_email(subject, body):
#     trimmed_body = body[:3000]
#     text = f"{subject}\n{trimmed_body}"

#     # 1. GPT Classification
#     gpt_prompt = f"""
#     You are an AI email classifier. Classify the following email into one of:
#     - Interview Invitation
#     - Job Offer
#     - Rejection
#     - General Update
#     - Spam or Promo
#     - Other

#     If the subject contains phrases like "Your update for", it often indicates a status update (e.g. offer, interview, or rejection).

#     Subject: {subject}
#     Body: {trimmed_body}

#     Respond with just the label.
#     """

#     gpt_response = client.chat.completions.create(
#         model="gpt-3.5-turbo-0125",
#         messages=[{"role": "user", "content": gpt_prompt}],
#         temperature=0.2,
#     )
#     gpt_label = gpt_response.choices[0].message.content.strip()

#     # 2. Embedding Classification
#     email_vec = embed(text)
#     best_label = None
#     best_score = -1

#     for label, example_vec in EXAMPLE_EMBEDDINGS.items():
#         if label == "Other":
#             continue  # only use "Other" as fallback

#         score = cosine_similarity(email_vec, example_vec)
#         print(f"[Embedding Match] {label}: {score:.3f}")  # 🔍 logs
#         if score > best_score:
#             best_label = label
#             best_score = score

#     # Fallback to "Other" if nothing matched well
#     embed_label = best_label if best_score >= 0.70 else "Other"


#     # 3. Comparison / flag mismatch
#     if gpt_label != embed_label:
#         print(f"[⚠️  MISMATCH] GPT: {gpt_label} | Embedding: {embed_label}")

#     # Optional: attach both for display or further logic
#     return {
#         "final": gpt_label,
#         "gpt": gpt_label,
#         "embedding": embed_label,
#         "similarity": round(best_score, 3)
#     }



# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# def decode_base64(data):
#     return base64.urlsafe_b64decode(data).decode(errors='ignore')

# def extract_body(payload):
#     # Try plain text
#     if payload.get('body', {}).get('data'):
#         return decode_base64(payload['body']['data'])

#     parts = payload.get('parts', [])
#     for part in parts:
#         if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
#             return decode_base64(part['body']['data'])
#         elif part.get('parts'):
#             for subpart in part['parts']:
#                 if subpart.get('mimeType') == 'text/plain' and subpart['body'].get('data'):
#                     return decode_base64(subpart['body']['data'])

#     # Fallback to HTML
#     for part in parts:
#         if part.get('mimeType') == 'text/html' and part['body'].get('data'):
#             html = decode_base64(part['body']['data'])
#             h = html2text.HTML2Text()
#             h.ignore_links = True
#             h.ignore_images = True
#             h.body_width = 0
#             return h.handle(html)

#     return ''
