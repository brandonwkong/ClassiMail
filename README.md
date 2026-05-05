# 📬 ClassiMail – Email Classifier for Job Applications

Tired of digging through dozens of "Thank you for applying" or "We’ve moved forward with other candidates" emails? Same here.

**ClassiMail** is a smart email classifier I built to automatically organize job application emails from Gmail — so I can quickly spot interviews, offers, rejections, and spam without wasting time.

---

## 💡 Why I Made This

As someone actively applying to internships and full-time roles, I noticed my Gmail was flooded with:

- Job alerts
- "Thanks for applying" auto-responses
- Rejections disguised as updates
- Actual interviews or offers hidden in the noise (very rare)

This is where ClassiMail comes in. ClassiMail helps **automatically parse and classify** those emails using OpenAI and cleanly presents classifies them in a dashboard, with categories tailored towards job applications.

---

## ⚙️ How It Works

### ✨ Features

- 🔐 **Google login** via OAuth
- 📬 **Fetches Gmail inbox** using the Gmail API
- 🤖 **Classifies each email** with GPT (e.g., Offer, Rejection, Interview, Promo)
- 🧠 Saves seen emails to prevent duplicates
- 🎨 **Dark-mode dashboard** built with Next.js + Tailwind
- 📌 Shows **subject, sender name, and category** at a glance
- 🔄 Refresh and filter by category

### 🧱 Stack

| Layer       | Tech                     |
|-------------|--------------------------|
| Frontend    | Next.js, TypeScript, TailwindCSS |
| Backend     | Python Flask             |
| Auth        | Google OAuth             |
| NLP         | OpenAI (GPT-3.5-turbo)   |
| Storage     | SQLite (local)           |

---

## 🛠️ Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/ClassiMail.git
cd ClassiMail
```

### 2. Setup Python Backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
Place your credentials.json in the root (get it from Google Cloud Console)

### 3. Setup frontend
cd gmail_ui
npm install
npm run dev

### 4. Run the backend
cd ..
python app.py


Built because I wanted my email to work for me, not waste my time.
