<<<<<<< HEAD
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
=======
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
>>>>>>> f23ae37521d7e6b1487fa61cf3628a3e1d1a29ca

```env
MONGO_URL=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
DB_NAME=karyasetu
<<<<<<< HEAD
JWT_SECRET=change-this-secret
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
=======
JWT_SECRET=use-a-long-random-secret
CORS_ORIGINS=http://localhost:5173
GEMINI_API_KEY=your_gemini_api_key
>>>>>>> f23ae37521d7e6b1487fa61cf3628a3e1d1a29ca
GEMINI_MODEL=gemini-3.7-flash
GEMINI_EMBED_MODEL=gemini-embedding-2
```

<<<<<<< HEAD
Do not commit or share `backend/.env`.

## 2. Start backend

```bat
start_backend.bat
```

Backend: http://127.0.0.1:8000

## 3. Start frontend
=======
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
>>>>>>> f23ae37521d7e6b1487fa61cf3628a3e1d1a29ca

```bat
start_frontend.bat
```

<<<<<<< HEAD
Frontend: http://localhost:5173

## Demo accounts
=======
Frontend: `http://localhost:5173`

## Demo accounts

>>>>>>> f23ae37521d7e6b1487fa61cf3628a3e1d1a29ca
- Admin: `admin@karyasetu.demo` / `Admin@123`
- Project Manager: `manager@karyasetu.demo` / `Manager@123`
- Site Supervisor: `supervisor@karyasetu.demo` / `Supervisor@123`

## Main workflow
<<<<<<< HEAD
1. Create/select a project.
2. Import an Excel/CSV schedule containing `activity_code`, `activity_name`, `level`, `planned_start`, `planned_end`, and `planned_progress`.
3. Open Voice Update and speak or paste a site report.
4. Gemini extracts progress, delay and reason.
5. Gemini Embedding 2 semantically matches the report to the correct L6 schedule activity.
6. KaryaSetu updates actual progress, calculates the plan-vs-actual gap, generates a risk when needed, and asks Gemini for a corrective recommendation.
7. Dashboard, risks, recommendations, and update history reflect the stored data.

No Ollama installation is required.
=======

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
>>>>>>> f23ae37521d7e6b1487fa61cf3628a3e1d1a29ca
