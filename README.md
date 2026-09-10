# KaryaSetu — Gemini AI Full Application

KaryaSetu connects infrastructure project schedules with real-time site progress. The application uses **Google Gemini API** for structured progress extraction, semantic embeddings, activity matching, and corrective recommendations. It does **not** require Ollama.

## Architecture

React/Vite → FastAPI → MongoDB Atlas

AI flow:

Site voice/text update → browser speech recognition → Gemini extraction → Gemini embeddings → L6 schedule matching → planned-vs-actual analysis → risk detection → Gemini corrective recommendation → MongoDB → dashboard

Google Gemini provides the generation and embedding APIs used by this application.

## 1. Configure backend

Create:

`backend/.env`

from `backend/.env.example`, then set:

```env
MONGO_URL=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
DB_NAME=karyasetu
JWT_SECRET=use-a-long-random-secret
CORS_ORIGINS=http://localhost:5173
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.7-flash
GEMINI_EMBED_MODEL=gemini-embedding-2
```

Never commit or share `backend/.env`.

## 2. Install and run backend

```bat
cd backend
python -m pip install -r requirements.txt
cd ..
start_backend.bat
```

Backend: `http://127.0.0.1:8000`

## 3. Run frontend

Open another terminal:

```bat
start_frontend.bat
```

Frontend: `http://localhost:5173`

## Demo accounts

- Admin: `admin@karyasetu.demo` / `Admin@123`
- Project Manager: `manager@karyasetu.demo` / `Manager@123`
- Site Supervisor: `supervisor@karyasetu.demo` / `Supervisor@123`

## Main workflow

1. Sign in.
2. Select/create a project.
3. Import an L5/L6 Excel or CSV schedule, or use the seeded schedule.
4. Open Voice Update.
5. Speak a site report or enter the transcript.
6. Gemini extracts activity, progress, delay and reason.
7. Gemini embeddings semantically match the report to an L6 schedule activity.
8. KaryaSetu updates actual progress and calculates the planned-vs-actual gap.
9. Delay/risk status is persisted in MongoDB.
10. Gemini generates a corrective recommendation when attention is required.
11. Dashboard, updates, risks and recommendations refresh from the database.

## Schedule import columns

Required:

`activity_code, activity_name, level, planned_start, planned_end, planned_progress`

Optional:

`parent_activity`

`level` must be `L5` or `L6`. Voice matching targets L6 activities.

## AI health

After login, open:

`http://127.0.0.1:8000/api/ai/health`

The endpoint verifies Gemini generation and embedding access.

## Important

The Gemini API key is required for AI extraction, semantic matching, and recommendations. Browser speech recognition supplies the spoken transcript; the AI intelligence layer is Gemini. Google documents Gemini content generation and embedding APIs in its official developer documentation.
