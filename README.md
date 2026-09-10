# KaryaSetu — Gemini Final

KaryaSetu is an AI-powered planning-to-execution bridge for infrastructure projects.

## Stack
- Frontend: React + Vite
- Backend: FastAPI
- Database: MongoDB Atlas
- AI: Google Gemini API
- Semantic matching: Gemini Embedding 2
- Schedule import: Pandas + OpenPyXL
- Voice input: browser speech recognition (Chrome/Edge)

## AI models
- Generation: `gemini-3.7-flash`
- Embeddings: `gemini-embedding-2`

Google currently lists both as stable Gemini API models. Gemini 3.7 Flash supports structured outputs, and Gemini Embedding 2 is intended for semantic search and similarity matching. Keep the model names in `backend/.env` configurable.

## Requirements
Python 3.14 is supported by this package. The requirements use versions with Python 3.14 wheels where native packages are involved; Visual Studio/Rust should not be needed for the normal install.

## 1. Configure MongoDB and Gemini
Create `backend/.env` from `backend/.env.example`:

```env
MONGO_URL=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
DB_NAME=karyasetu
JWT_SECRET=change-this-secret
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.7-flash
GEMINI_EMBED_MODEL=gemini-embedding-2
```

Do not commit or share `backend/.env`.

## 2. Start backend

```bat
start_backend.bat
```

Backend: http://127.0.0.1:8000

## 3. Start frontend

```bat
start_frontend.bat
```

Frontend: http://localhost:5173

## Demo accounts
- Admin: `admin@karyasetu.demo` / `Admin@123`
- Project Manager: `manager@karyasetu.demo` / `Manager@123`
- Site Supervisor: `supervisor@karyasetu.demo` / `Supervisor@123`

## Main workflow
1. Create/select a project.
2. Import an Excel/CSV schedule containing `activity_code`, `activity_name`, `level`, `planned_start`, `planned_end`, and `planned_progress`.
3. Open Voice Update and speak or paste a site report.
4. Gemini extracts progress, delay and reason.
5. Gemini Embedding 2 semantically matches the report to the correct L6 schedule activity.
6. KaryaSetu updates actual progress, calculates the plan-vs-actual gap, generates a risk when needed, and asks Gemini for a corrective recommendation.
7. Dashboard, risks, recommendations, and update history reflect the stored data.

No Ollama installation is required.
