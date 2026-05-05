  # 📬 ClassiMail – Email Classifier for Job Applications

  ## 🚀 Update: Smart Ranking & Recommendation Engine

  Building an ML-powered ranking system that learns which emails matter most to you.

  | Feature | Description | Status |
  |---------|-------------|--------|
  | **Feature Engineering** | Extracts 25+ signals per email (recency, sender frequency, keywords, category) | ✅ |
  | **Ranking System** | Scores and sorts emails by predicted importance | ✅ |
  | **Interaction Tracking** | Logs clicks, opens, skips with time spent for CTR training | ✅ |
  | **ML Ranker** | Train a model on your interaction data | 🔄 Soon |

  **Try it:** Click the **✨ Recommended** tab to see emails ranked by importance score.

  ---

  Tired of digging through dozens of "Thank you for applying" or "We've moved forward with other candidates" emails? Same here.

  **ClassiMail** is a smart email classifier I built to automatically organize job application emails from Gmail — so I can quickly spot interviews, offers, rejections, and spam without wasting time.

  ---

  ## 💡 Why I Made This

  As someone actively applying to internships and full-time roles, I noticed my Gmail was flooded with:

  - Job alerts
  - "Thanks for applying" auto-responses
  - Rejections disguised as updates
  - Actual interviews or offers hidden in the noise (very rare)

  ClassiMail helps **automatically parse and classify** those emails using OpenAI and presents them in a clean dashboard, with categories tailored towards job applications.

  ---

  ## ⚙️ How It Works

  ### ✨ Features

  - 🔐 **Google login** via OAuth
  - 📬 **Fetches Gmail inbox** using the Gmail API
  - 🤖 **Classifies each email** with GPT (e.g., Offer, Rejection, Interview, Promo)
  - 📊 **Ranks emails** by importance using feature extraction + scoring
  - 📈 **Tracks interactions** (clicks, time spent) for ML training
  - 🧠 Saves seen emails to prevent duplicates
  - 🎨 **Dark-mode dashboard** built with Next.js + Tailwind
  - 📌 Shows **subject, sender name, category, and rank score** at a glance
  - 🔄 Refresh, filter by category, or view **Recommended** tab

  ### 🧱 Stack

  | Layer       | Tech                     |
  |-------------|--------------------------|
  | Frontend    | Next.js, TypeScript, TailwindCSS |
  | Backend     | Python Flask             |
  | Auth        | Google OAuth             |
  | Classification | OpenAI GPT-3.5-turbo  |
  | Ranking     | Custom feature engineering + scoring |
  | Storage     | SQLite                   |
  | Monitoring  | Prometheus + Grafana     |

  ---

  ## 🛠️ Local Setup

  ### 1. Clone the repo

  ```bash
  git clone https://github.com/YOUR_USERNAME/ClassiMail.git
  cd ClassiMail
  ```
  2. Setup Python Backend

  python -m venv venv

  # macOS/Linux:
  source venv/bin/activate
  # Windows:
  venv\Scripts\activate

  pip install -r requirements.txt

  Place your credentials.json in the project root (download from Google Cloud Console).

  3. Set up the frontend

  cd gmail_ui
  npm install
  npm run dev
  Frontend runs at http://localhost:3000

  4. Run the backend

  python app.py
  Backend runs at http://localhost:5000

  5. (Optional) Run monitoring stack

  docker compose up -d
  - Prometheus → http://localhost:9090
  - Grafana → http://localhost:3030

  ---
## API Endpoints

| Endpoint         | Method | Description |
|-----------------|--------|------------|
| /emails         | GET    | Fetch and classify emails with rank scores |
| /interact       | POST   | Log user interaction (click, open, skip) |
| /stats          | GET    | Basic interaction counts |
| /stats/detailed | GET    | Full stats: CTR by position, time spent, etc. |
| /metrics        | GET    | Prometheus metrics |
  ---
  Built because I wanted my email to work for me, not waste my time.
