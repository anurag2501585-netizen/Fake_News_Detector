# 🕵️‍♂️ Fake News Detector

An AI-powered **Fake News Detection** web application with a stunning **Glassmorphism** UI, powered by the **OPENROUTER API KEY** and a secure **Python (Flask)** backend.

## ✨ Features

- 🧊 **Glassmorphism UI** — Frosted glass card with `backdrop-filter`, glowing borders, and soft layered shadows
- 🌈 **Animated mesh-gradient background** — Deep purples, blues, and magenta that float and pulse
- 🤖 **OPEN AI integration** — Uses `OPENAI free model` for fast, free fact-checking
- 🔐 **Secure API key** — Key lives on the server (`.env`), never exposed to the frontend or Git
- 📊 **Rich results** — Color-coded verdict badge, animated confidence score bar, and detailed explanation
- ⚡ **Smooth UX** — Loading spinner with glowing pulse, fade-in results, graceful error handling

## 🚀 Quick Start

### 1. Get a free OPENAI API Key
Go to [OPENROUTER WEBSITE](https://openrouter.ai) → Create API key (free tier: 15 req/min).

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your API key
```bash
cp .env.example .env
```
Then open `.env` and replace `YOUR_API_KEY_HERE` with your actual key:
```
OPENROUTER_API_KEY=your-actual-key-here
```

### 4. Run the server
```bash
python app.py
```
Open [http://localhost:3000](http://localhost:3000) in your browser. 🎉

---

## 🔒 Git Safety (API Key Protection)

Your API key is **never committed** to Git thanks to the `.gitignore` file:

```
# .gitignore excludes these
.env
.env.local
```

- ✅ `.env` → contains your **real** secret key (gitignored)
- ✅ `.env.example` → template you **can** commit (placeholder key only)
- ✅ `app.py` reads the key at runtime via `dotenv`

**What gets uploaded to GitHub:** All code + `.env.example` (safe template).
**What stays local:** Your `.env` with the real key. 🔐

---

## 🗂️ Project Structure

```
├── app.py              # Flask backend (holds API key, proxies OPENAI)
├── public/
│   └── index.html      # Frontend (glassmorphism UI + JS)
├── requirements.txt    # Python dependencies
├── .env                # 🔒 Your secret API key (gitignored)
├── .env.example        # Safe template for Git
└── .gitignore          # Protects .env from being uploaded
```

## 🧠 How It Works

1. User pastes news text in the browser
2. Frontend sends it to `POST /api/analyze` on our backend
3. Backend adds the **prompt** + API key, calls **OPENAI API**
4. OPENAI returns strict JSON: `{verdict, confidence_score, explanation}`
5. Backend validates & forwards to frontend
6. Frontend renders the color-coded result with animated score bar

## 📝 Verdict Colors

| Verdict       | Color           |
|---------------|-----------------|
| ✅ Real       | Green           |
| ❌ Fake       | Red             |
| ⚠️ Misleading | Yellow/Orange   |
| ⚪ Unverified | Gray            |

---

## 🛡️ Deployment Tips

**Heroku / Render / Railway:** Set `OPENAI_API_KEY` as an environment variable in the platform's dashboard — no `.env` file needed.

**Vercel/Netlify (static only):** Not recommended — you'd need a serverless function to keep the key secret.

If you want to deploy, just push the repo (`.env` auto-excluded) and configure the env var on the host.

---

## 📄 License
MIT — free to use and modify. For educational purposes only.