# Live Hosting Strategy: "Unlimited" Free Deployment

To live-host this system for free without the aggressive "sleeping" found on Render, we recommend a dual-hosting strategy using **Koyeb** for the API and **Hugging Face** for the UI.

---

## 🏗️ 1. API Hosting: Koyeb (Back-end)
Koyeb's free tier is significantly more persistent than Render for Python-based Docker apps.

### Quick Launch on Koyeb:
1. Go to **[Koyeb.com](https://www.koyeb.com/)** and sign up.
2. Click **"Create Service"** → **"GitHub"**.
3. Select this repository.
4. **Build Config**: Select **"Docker"**.
   - Koyeb will automatically detect the **`Dockerfile`**.
5. **Environment Variables**: Add:
   - `GEMINI_API_KEY`: Paste your actual key.
6. **Deployment**: Koyeb will build and host your API at a public `.koyeb.app` URL.

---

## 🏛️ 2. UI Hosting: Hugging Face Spaces (Front-end)
Hugging Face is the premier "unlimited" free hosting for AI/Streamlit apps. It is very stable and provides a professional `.hf.space` URL.

### Quick Launch on Hugging Face:
1. Go to **[Hugging Face](https://huggingface.co/spaces)**.
2. Click **"Create new Space"**.
3. **Space Name**: `shl-recommender-ui`.
4. **SDK**: Choose **"Streamlit"**.
5. **License**: Choose **"Apache 2.0"**.
6. **Files**: Upload the contents of your `shl-project` or connect via GitHub.
   - *Ensure `requirements.txt` and `frontend/app.py` are in the main file structure.*
7. **Secrets**: Go to **Settings** → **Variables and Secrets** and add:
   - `API_URL`: Set to your public Koyeb API URL (e.g., `https://shl-recommender-api-u7...koyeb.app`).
8. **App File**: If Hugging Face asks for the app file, point it to `frontend/app.py`.

---

## 🛠️ 3. Optimization for Free Tiers
- **Dockerized Base**: The `Dockerfile` pre-downloads the `BGE-small-en` embedding model during the build stage. This ensures your "Live" application starts instantly instead of spending 20 seconds downloading models on every launch.
- **Stateless Logic**: The system uses a local FAISS index (`vector.index`) and SQLite DB, keeping your deployment completely free from paid database requirements.

---
*By following this strategy, your SHL Recommender will have a 24/7 presence (with minimal hibernating compared to other free services).* 🚀🎯
