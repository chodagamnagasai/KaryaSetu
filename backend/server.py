from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import os, re, uuid, logging, math, json, asyncio

import bcrypt
import jwt


ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

MONGO_URL = os.getenv("MONGO_URL", "")
if not MONGO_URL:
    raise RuntimeError("backend/.env is missing MONGO_URL")

DB_NAME = os.getenv("DB_NAME", "karyasetu")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-2")


client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=10000
)

db = client[DB_NAME]

app = FastAPI(
    title="KaryaSetu",
    version="4.0.0",
    description="AI planning-to-execution bridge"
)

api = APIRouter(prefix="/api")

logger = logging.getLogger("karyasetu")


# ============================================================
# COMMON
# ============================================================

def now():
    return datetime.now(timezone.utc).isoformat()


def clean(doc):
    if not doc:
        return None

    d = dict(doc)
    d.pop("_id", None)
    return d


def hash_password(value):
    return bcrypt.hashpw(
        value.encode(),
        bcrypt.gensalt()
    ).decode()


def verify_password(value, hashed):
    return bcrypt.checkpw(
        value.encode(),
        hashed.encode()
    )


def make_token(user):
    return jwt.encode(
        {
            "sub": user["id"],
            "role": user["role"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=12)
        },
        JWT_SECRET,
        algorithm="HS256"
    )


# ============================================================
# AUTH
# ============================================================

async def current_user(
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            401,
            "Please sign in to continue"
        )

    try:
        payload = jwt.decode(
            authorization[7:],
            JWT_SECRET,
            algorithms=["HS256"]
        )
    except jwt.PyJWTError:
        raise HTTPException(
            401,
            "Your session has expired"
        )

    user = await db.users.find_one(
        {"id": payload.get("sub")},
        {"_id": 0, "password_hash": 0}
    )

    if not user:
        raise HTTPException(
            401,
            "User not found"
        )

    return user


async def manager(user=Depends(current_user)):
    if user["role"] not in [
        "ADMIN",
        "PROJECT MANAGER"
    ]:
        raise HTTPException(
            403,
            "Manager access required"
        )

    return user


# ============================================================
# MODELS
# ============================================================

class Login(BaseModel):
    email: str
    password: str


class ProjectCreate(BaseModel):
    name: str
    location: str = ""
    description: str = ""


class ActivityCreate(BaseModel):
    project_id: str
    activity_code: str
    activity_name: str
    level: str = "L6"
    parent_activity: str = ""
    planned_start: str = ""
    planned_end: str = ""
    planned_progress: float = Field(
        0,
        ge=0,
        le=100
    )


class ActivityEdit(BaseModel):
    actual_progress: Optional[float] = Field(
        None,
        ge=0,
        le=100
    )

    status: Optional[str] = None


# Voice / AI update
class UpdateCreate(BaseModel):
    project_id: str

    transcript: str = Field(
        min_length=3
    )

    activity_id: Optional[str] = None

    progress: Optional[float] = Field(
        None,
        ge=0,
        le=100
    )

    language: str = "en-IN"


# Manual update
class ManualUpdateCreate(BaseModel):
    project_id: str

    activity_id: str

    progress: float = Field(
        0,
        ge=0,
        le=100
    )

    delay_days: int = Field(
        0,
        ge=0
    )

    delay_reason: str = ""

    remarks: str = ""


# ============================================================
# DEFAULT DATA
# ============================================================

SEED = [
    ("L5", "Site Preparation", "L5-01"),
    ("L6", "Site Clearing", "L6-01"),
    ("L6", "Surveying", "L6-02"),
    ("L6", "Excavation", "L6-03"),

    ("L5", "Foundation", "L5-02"),
    ("L6", "Foundation Excavation", "L6-04"),
    ("L6", "Reinforcement", "L6-05"),
    ("L6", "Formwork", "L6-06"),
    ("L6", "Concrete Pouring", "L6-07"),

    ("L5", "Structural Work", "L5-03"),
    ("L6", "Column Construction", "L6-08"),
    ("L6", "Beam Construction", "L6-09"),
    ("L6", "Slab Work", "L6-10"),

    ("L5", "MEP", "L5-04"),
    ("L6", "Electrical Installation", "L6-11"),
    ("L6", "Plumbing", "L6-12"),

    ("L5", "Finishing", "L5-05"),
    ("L6", "Plastering", "L6-13"),
    ("L6", "Painting", "L6-14"),
    ("L6", "Final Finishing", "L6-15")
]


STOP = set(
    """
    the a an and or of to for in on at with from
    is are was were work completed complete percent
    today yesterday this that site project activity
    block area has have by due behind delay delayed
    because very our we did done construction
    installation progress reporting update
    """.split()
)


SYN = {
    "concrete": [
        "pour",
        "poured",
        "pouring",
        "concreting"
    ],

    "column": [
        "columns",
        "column construction"
    ],

    "beam": [
        "beams",
        "beam construction"
    ],

    "slab": [
        "slabs",
        "slab work"
    ],

    "steel": [
        "reinforcement",
        "rebar"
    ],

    "reinforcement": [
        "steel",
        "rebar"
    ],

    "excavate": [
        "excavation",
        "excavated"
    ],

    "paint": [
        "painting"
    ],

    "plaster": [
        "plastering"
    ],

    "electrical": [
        "electric"
    ],

    "labour": [
        "labor",
        "manpower",
        "workers"
    ],

    "material": [
        "cement",
        "steel",
        "delivery",
        "shortage"
    ]
}


def words(text):
    return [
        w
        for w in re.findall(
            r"[a-z0-9]+",
            text.lower()
        )
        if w not in STOP and len(w) > 2
    ]


def lexical_score(query, target):

    q = set(words(query))
    t = set(words(target))

    for word, synonyms in SYN.items():

        if word in q:
            q.update(synonyms)

    if not q or not t:
        return 0.0

    return len(q & t) / math.sqrt(
        len(q) * len(t)
    )


# ============================================================
# GEMINI
# ============================================================

async def gemini_client():

    if not GEMINI_API_KEY:
        raise HTTPException(
            503,
            "Gemini API is not configured. "
            "Add GEMINI_API_KEY to backend/.env"
        )

    from google import genai

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


async def gemini_generate_json(prompt: str):

    client_ai = await gemini_client()

    from google.genai import types

    def call():

        response = client_ai.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,

            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json"
            )
        )

        return response.text

    last_error = None

    for attempt in range(3):

        try:

            raw = await asyncio.to_thread(
                call
            )

            try:
                return json.loads(raw)

            except json.JSONDecodeError:

                match = re.search(
                    r"\{.*\}",
                    raw,
                    re.S
                )

                if not match:
                    raise HTTPException(
                        502,
                        "Gemini returned invalid JSON"
                    )

                return json.loads(
                    match.group(0)
                )

        except HTTPException:
            raise

        except Exception as e:

            last_error = e

            message = str(e).lower()

            temporary = any(
                x in message
                for x in [
                    "503",
                    "unavailable",
                    "high demand",
                    "429",
                    "resource exhausted",
                    "rate limit"
                ]
            )

            if temporary and attempt < 2:

                await asyncio.sleep(
                    1.5 * (attempt + 1)
                )

                continue

            logger.exception(
                "Gemini generation failed"
            )

            raise HTTPException(
                503 if temporary else 502,
                f"Gemini AI is temporarily unavailable: {e}"
            )

    raise HTTPException(
        503,
        f"Gemini AI is temporarily unavailable: {last_error}"
    )


async def embedding(text):

    client_ai = await gemini_client()

    def call():

        result = client_ai.models.embed_content(
            model=GEMINI_EMBED_MODEL,
            contents=text
        )

        return (
            result.embeddings[0].values
            if result.embeddings
            else None
        )

    last_error = None

    for attempt in range(3):

        try:

            return await asyncio.to_thread(
                call
            )

        except Exception as e:

            last_error = e

            message = str(e).lower()

            temporary = any(
                x in message
                for x in [
                    "503",
                    "unavailable",
                    "high demand",
                    "429",
                    "resource exhausted",
                    "rate limit"
                ]
            )

            if temporary and attempt < 2:

                await asyncio.sleep(
                    1.5 * (attempt + 1)
                )

                continue

            logger.exception(
                "Gemini embedding failed"
            )

            raise HTTPException(
                503 if temporary else 502,
                f"Gemini embedding is temporarily unavailable: {e}"
            )

    raise HTTPException(
        503,
        f"Gemini embedding is temporarily unavailable: {last_error}"
    )


# ============================================================
# GEMINI UNDERSTANDS VOICE / TEXT
# ============================================================

async def extract_update(text):

    prompt = """
You are KaryaSetu, an expert construction
project controls AI.

Analyze this site progress report.

Return JSON only.

Required fields:

activity_description:
Concise description of the actual construction
work reported.

progress:
Numeric percentage from 0 to 100.

delay_days:
Integer number of delay days explicitly stated.
Use 0 when not stated.

delay_reason:
Concise delay reason.
Empty string if none.

remarks:
Concise factual summary.

risk:
HIGH, MEDIUM, LOW or empty string.

Rules:

1. Never invent activities.
2. Never invent percentages.
3. Never invent delay days.
4. Never invent delay reasons.
5. Preserve the user's meaning.
6. Understand natural spoken construction language.

Site report:
""" + text

    ai = await gemini_generate_json(
        prompt
    )

    try:

        ai["progress"] = float(
            ai.get("progress") or 0
        )

        ai["delay_days"] = int(
            ai.get("delay_days") or 0
        )

        ai["activity_description"] = str(
            ai.get("activity_description")
            or text
        )

        ai["delay_reason"] = str(
            ai.get("delay_reason") or ""
        )

        ai["remarks"] = str(
            ai.get("remarks") or text
        )

        ai["risk"] = str(
            ai.get("risk") or ""
        )

        ai["ai_engine"] = "gemini"

        return ai

    except Exception as e:

        raise HTTPException(
            502,
            f"Gemini extraction returned invalid fields: {e}"
        )


# ============================================================
# ACTIVITY MATCHING
# ============================================================

def cosine(a, b):

    if not a or not b:
        return 0.0

    n = min(
        len(a),
        len(b)
    )

    a = a[:n]
    b = b[:n]

    da = math.sqrt(
        sum(x * x for x in a)
    )

    db = math.sqrt(
        sum(x * x for x in b)
    )

    if not da or not db:
        return 0.0

    return sum(
        x * y
        for x, y in zip(a, b)
    ) / (da * db)


async def match_activity(
    project_id,
    description
):

    activities = [
        clean(x)
        async for x in db.activities.find(
            {
                "project_id": project_id,
                "level": "L6"
            },
            {"_id": 0}
        )
    ]

    if not activities:
        return []

    # Try Gemini semantic matching.
    # If embeddings temporarily fail,
    # use lexical matching instead.
    try:
        query_embedding = await embedding(
            description
        )
    except HTTPException:
        query_embedding = None

    ranked = []

    for activity in activities:

        activity_text = (
            f"{activity.get('activity_code', '')} "
            f"{activity.get('activity_name', '')} "
            f"{activity.get('parent_activity', '')}"
        )

        semantic_score = 0.0

        if query_embedding:

            try:

                activity_embedding = await embedding(
                    activity_text
                )

                semantic_score = cosine(
                    query_embedding,
                    activity_embedding
                )

            except HTTPException:
                semantic_score = 0.0

        lexical = lexical_score(
            description,
            activity_text
        )

        if query_embedding:
            score = (
                0.80 * semantic_score
                +
                0.20 * lexical
            )
        else:
            score = lexical

        ranked.append(
            (
                score,
                activity
            )
        )

    return sorted(
        ranked,
        key=lambda x: x[0],
        reverse=True
    )


# ============================================================
# AI RECOMMENDATION
# ============================================================

async def recommendation(
    reason,
    gap,
    days,
    activity_name
):

    prompt = f"""
You are a construction project controls expert.

Generate one concise and actionable corrective
recommendation.

Activity:
{activity_name}

Delay reason:
{reason or "Not specified"}

Progress gap:
{gap}% behind planned

Delay days:
{days}

Return JSON only:

{{
    "action": "..."
}}

Do not invent project facts.
"""

    result = await gemini_generate_json(
        prompt
    )

    action = str(
        result.get("action") or ""
    ).strip()

    if not action:

        raise HTTPException(
            502,
            "Gemini did not return a corrective recommendation"
        )

    return action


# ============================================================
# RISK + RECOMMENDATION
# ============================================================

async def create_risk_and_recommendation(
    project_id,
    activity,
    gap,
    days,
    reason,
    forced_risk=False
):

    status = (
        "DELAYED"
        if days > 0 or gap >= 10
        else
        (
            "AT RISK"
            if gap > 0
            else "ON TRACK"
        )
    )

    if status == "ON TRACK" and not forced_risk:
        return None, None

    severity = (
        "CRITICAL"
        if days >= 3 or gap >= 20
        else
        (
            "HIGH"
            if days >= 2 or gap >= 10
            else "MEDIUM"
        )
    )

    description = (
        reason
        or
        f"Actual progress is {gap}% behind planned progress."
    )

    risk = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "activity_id": activity["id"],
        "title": f"{activity['activity_name']} needs attention",
        "description": description,
        "severity": severity,
        "source": "KaryaSetu AI engine",
        "created_at": now()
    }

    await db.risks.insert_one(
        risk
    )

    # Do not allow a temporary Gemini failure
    # to undo the actual progress update.
    try:

        action = await recommendation(
            description,
            gap,
            days,
            activity["activity_name"]
        )

    except HTTPException:

        action = (
            f"Review {activity['activity_name']} "
            f"and take corrective action to recover "
            f"the {max(gap, 0)}% progress gap."
        )

    rec = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "activity_id": activity["id"],
        "problem": description,
        "action": action,
        "priority": severity,
        "created_at": now()
    }

    await db.recommendations.insert_one(
        rec
    )

    return risk, action


# ============================================================
# COMMON UPDATE SAVE PIPELINE
# ============================================================

async def save_update(
    project_id,
    activity,
    progress,
    days,
    reason,
    remarks,
    transcript,
    language,
    user,
    similarity=1.0,
    ai_engine="manual",
    forced_risk=False
):

    planned = float(
        activity.get(
            "planned_progress",
            0
        )
    )

    gap = round(
        planned - progress,
        1
    )

    status = (
        "DELAYED"
        if days > 0 or gap >= 10
        else
        (
            "AT RISK"
            if gap > 0
            else "ON TRACK"
        )
    )

    # --------------------------------------------------------
    # UPDATE L6 ACTIVITY
    # --------------------------------------------------------

    await db.activities.update_one(
        {"id": activity["id"]},
        {
            "$set": {
                "actual_progress": progress,
                "status": status,
                "last_update_at": now()
            }
        }
    )

    # --------------------------------------------------------
    # STORE UPDATE HISTORY
    # --------------------------------------------------------

    upd = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "activity_id": activity["id"],

        "supervisor_id": user["id"],
        "supervisor_name": user["name"],

        "transcript": transcript,
        "language": language,

        "extracted_description":
            activity["activity_name"],

        "progress": progress,
        "planned_progress": planned,
        "progress_gap": gap,

        "delay_days": days,
        "delay_reason": reason,

        "remarks":
            remarks or transcript,

        "confidence":
            round(similarity, 3),

        "ai_engine":
            ai_engine,

        "created_at":
            now()
    }

    await db.updates.insert_one(
        upd
    )

    # --------------------------------------------------------
    # RISK + RECOMMENDATION
    # --------------------------------------------------------

    risk, rec = await create_risk_and_recommendation(
        project_id,
        activity,
        gap,
        days,
        reason,
        forced_risk
    )

    return {
        "update": clean(upd),
        "matched_activity": activity,
        "similarity": round(
            similarity,
            3
        ),
        "status": status,
        "progress_gap": gap,
        "risk": risk,
        "recommendation": rec
    }


# ============================================================
# DATABASE SEED
# ============================================================

async def seed():

    accounts = [
        (
            "Admin",
            "admin@karyasetu.demo",
            "Admin@123",
            "ADMIN"
        ),

        (
            "Project Manager",
            "manager@karyasetu.demo",
            "Manager@123",
            "PROJECT MANAGER"
        ),

        (
            "Site Supervisor",
            "supervisor@karyasetu.demo",
            "Supervisor@123",
            "SITE SUPERVISOR"
        )
    ]

    for name, email, password, role in accounts:

        if not await db.users.find_one(
            {"email": email}
        ):

            await db.users.insert_one(
                {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "email": email,
                    "password_hash":
                        hash_password(password),
                    "role": role,
                    "created_at": now()
                }
            )

    if await db.projects.count_documents({}) == 0:

        projects = [
            (
                "Hyderabad Metro Infrastructure Project",
                "Hyderabad, Telangana"
            ),

            (
                "Highway Construction Project",
                "Bengaluru–Mysuru Corridor"
            )
        ]

        for index, (name, location) in enumerate(
            projects
        ):

            project_id = str(
                uuid.uuid4()
            )

            await db.projects.insert_one(
                {
                    "id": project_id,
                    "name": name,
                    "location": location,
                    "description":
                        "Infrastructure delivery programme",
                    "created_at": now()
                }
            )

            parent = ""

            for i, (
                level,
                activity_name,
                code
            ) in enumerate(SEED):

                if level == "L5":
                    parent = code

                await db.activities.insert_one(
                    {
                        "id": str(uuid.uuid4()),
                        "project_id": project_id,

                        "activity_code": code,
                        "activity_name":
                            activity_name,

                        "level": level,

                        "parent_activity":
                            ""
                            if level == "L5"
                            else parent,

                        "planned_start":
                            f"2026-{(i % 9) + 1:02d}-05",

                        "planned_end":
                            f"2026-{(i % 9) + 2:02d}-25",

                        "planned_progress":
                            min(
                                95,
                                10 + i * 4 + index * 3
                            ),

                        "actual_progress":
                            min(
                                90,
                                8 + i * 3 + index * 2
                            ),

                        "status":
                            "ON TRACK",

                        "created_at":
                            now()
                    }
                )


@app.on_event("startup")
async def startup():

    await db.command("ping")

    await seed()

    await db.users.create_index(
        "email",
        unique=True
    )


# ============================================================
# AUTH ROUTES
# ============================================================

@api.post("/auth/login")
async def login(body: Login):

    user = await db.users.find_one(
        {
            "email":
                body.email.strip().lower()
        }
    )

    if (
        not user
        or not verify_password(
            body.password,
            user["password_hash"]
        )
    ):

        raise HTTPException(
            401,
            "Incorrect email or password"
        )

    data = clean(user)

    data.pop(
        "password_hash",
        None
    )

    data["token"] = make_token(
        data
    )

    return data


@api.get("/auth/me")
async def me(
    user=Depends(current_user)
):
    return user


# ============================================================
# HEALTH
# ============================================================

@api.get("/health")
async def health():

    await db.command("ping")

    return {
        "status": "ok",
        "database": "connected",
        "ai_provider": "Gemini",
        "ai_model": GEMINI_MODEL,
        "embedding_model":
            GEMINI_EMBED_MODEL
    }


@api.get("/ai/health")
async def ai_health(
    user=Depends(current_user)
):

    generated = await gemini_generate_json(
        'Return {"ok": true} only.'
    )

    embedded = await embedding(
        "construction progress"
    )

    return {
        "gemini": bool(generated),
        "embeddings": bool(embedded),
        "model": GEMINI_MODEL,
        "embedding_model":
            GEMINI_EMBED_MODEL
    }


# ============================================================
# PROJECTS
# ============================================================

@api.get("/projects")
async def projects(
    user=Depends(current_user)
):

    output = []

    async for project in db.projects.find(
        {},
        {"_id": 0}
    ).sort(
        "created_at",
        -1
    ):

        project = clean(
            project
        )

        activities = await db.activities.find(
            {
                "project_id":
                    project["id"]
            },
            {"_id": 0}
        ).to_list(5000)

        project["activity_count"] = len(
            activities
        )

        project["overall_progress"] = (
            round(
                sum(
                    float(
                        a.get(
                            "actual_progress",
                            0
                        )
                    )
                    for a in activities
                )
                / len(activities),
                1
            )
            if activities
            else 0
        )

        output.append(
            project
        )

    return output


@api.post("/projects")
async def create_project(
    body: ProjectCreate,
    user=Depends(manager)
):

    if not body.name.strip():
        raise HTTPException(
            400,
            "Project name is required"
        )

    data = {
        "id": str(uuid.uuid4()),
        "name": body.name.strip(),
        "location":
            body.location.strip(),
        "description":
            body.description.strip(),
        "created_at": now()
    }

    await db.projects.insert_one(
        data
    )

    return clean(data)


@api.get("/projects/{pid}")
async def get_project(
    pid: str,
    user=Depends(current_user)
):

    project = clean(
        await db.projects.find_one(
            {
                "id": pid
            },
            {"_id": 0}
        )
    )

    if not project:
        raise HTTPException(
            404,
            "Project not found"
        )

    project["activities"] = [
        clean(x)
        async for x in db.activities.find(
            {
                "project_id": pid
            },
            {"_id": 0}
        ).sort(
            "activity_code",
            1
        )
    ]

    return project


# ============================================================
# USERS
# ============================================================

@api.get("/users")
async def users(
    user=Depends(manager)
):

    return [
        clean(x)
        async for x in db.users.find(
            {},
            {
                "_id": 0,
                "password_hash": 0
            }
        )
    ]


# ============================================================
# ACTIVITIES
# ============================================================

@api.get("/activities")
async def activities(
    project_id: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    user=Depends(current_user)
):

    query = {}

    if project_id:
        query["project_id"] = project_id

    if level:
        query["level"] = level

    if status:
        query["status"] = status

    return [
        clean(x)
        async for x in db.activities.find(
            query,
            {"_id": 0}
        ).sort(
            "activity_code",
            1
        )
    ]


@api.post("/activities")
async def create_activity(
    body: ActivityCreate,
    user=Depends(manager)
):

    if body.level not in [
        "L5",
        "L6"
    ]:
        raise HTTPException(
            400,
            "Level must be L5 or L6"
        )

    if not await db.projects.find_one(
        {
            "id":
                body.project_id
        }
    ):

        raise HTTPException(
            404,
            "Project not found"
        )

    data = body.model_dump() | {
        "id": str(uuid.uuid4()),
        "actual_progress": 0.0,
        "status": "ON TRACK",
        "created_at": now()
    }

    await db.activities.insert_one(
        data
    )

    return clean(data)


@api.patch("/activities/{aid}")
async def edit_activity(
    aid: str,
    body: ActivityEdit,
    user=Depends(manager)
):

    activity = await db.activities.find_one(
        {
            "id": aid
        }
    )

    if not activity:
        raise HTTPException(
            404,
            "Activity not found"
        )

    data = {
        k: v
        for k, v in body.model_dump().items()
        if v is not None
    }

    if (
        "actual_progress" in data
        and "status" not in data
    ):

        gap = (
            float(
                activity.get(
                    "planned_progress",
                    0
                )
            )
            -
            data["actual_progress"]
        )

        data["status"] = (
            "DELAYED"
            if gap >= 10
            else
            (
                "AT RISK"
                if gap > 0
                else "ON TRACK"
            )
        )

    data["updated_at"] = now()

    await db.activities.update_one(
        {
            "id": aid
        },
        {
            "$set": data
        }
    )

    return clean(
        await db.activities.find_one(
            {
                "id": aid
            },
            {"_id": 0}
        )
    )


# ============================================================
# VOICE / AI UPDATE
# ============================================================

@api.post("/updates")
async def create_update(
    body: UpdateCreate,
    user=Depends(current_user)
):

    if not await db.projects.find_one(
        {
            "id":
                body.project_id
        }
    ):

        raise HTTPException(
            404,
            "Project not found"
        )

    # Gemini understands the spoken text
    analysis = await extract_update(
        body.transcript
    )

    # Find the correct L6 activity
    ranked = await match_activity(
        body.project_id,
        analysis["activity_description"]
    )

    if body.activity_id:

        activity = clean(
            await db.activities.find_one(
                {
                    "id":
                        body.activity_id,

                    "project_id":
                        body.project_id,

                    "level":
                        "L6"
                },
                {"_id": 0}
            )
        )

        similarity = 1.0

    else:

        similarity, activity = (
            ranked[0]
            if ranked
            else
            (0, None)
        )

    if not activity:

        raise HTTPException(
            400,
            "No L6 activities found for this project"
        )

    progress = float(
        body.progress
        if body.progress is not None
        else analysis.get(
            "progress",
            0
        )
    )

    if (
        progress == 0
        and body.progress is None
    ):

        raise HTTPException(
            400,
            "No progress percentage was detected. "
            "Say or enter a value such as 70 percent."
        )

    result = await save_update(
        project_id=body.project_id,
        activity=activity,
        progress=progress,
        days=int(
            analysis.get(
                "delay_days",
                0
            )
        ),
        reason=analysis.get(
            "delay_reason",
            ""
        ),
        remarks=analysis.get(
            "remarks",
            body.transcript
        ),
        transcript=body.transcript,
        language=body.language,
        user=user,
        similarity=similarity,
        ai_engine="gemini",
        forced_risk=bool(
            analysis.get("risk")
        )
    )

    result["analysis"] = analysis

    return result


# ============================================================
# MANUAL UPDATE
# ============================================================

@api.post("/updates/manual")
async def create_manual_update(
    body: ManualUpdateCreate,
    user=Depends(current_user)
):

    if not await db.projects.find_one(
        {
            "id":
                body.project_id
        }
    ):

        raise HTTPException(
            404,
            "Project not found"
        )

    activity = clean(
        await db.activities.find_one(
            {
                "id":
                    body.activity_id,

                "project_id":
                    body.project_id,

                "level":
                    "L6"
            },
            {"_id": 0}
        )
    )

    if not activity:

        raise HTTPException(
            404,
            "L6 activity not found"
        )

    transcript = (
        body.remarks.strip()
        or
        f"Manual update: "
        f"{activity['activity_name']} "
        f"is {body.progress}% complete."
    )

    return await save_update(
        project_id=body.project_id,
        activity=activity,
        progress=float(
            body.progress
        ),
        days=int(
            body.delay_days
        ),
        reason=body.delay_reason.strip(),
        remarks=body.remarks.strip(),
        transcript=transcript,
        language="manual",
        user=user,
        similarity=1.0,
        ai_engine="manual",
        forced_risk=False
    )


# ============================================================
# EXCEL WORK-UPDATE IMPORT
# ============================================================

@api.post("/updates/import")
async def import_updates(
    project_id: str,
    file: UploadFile = File(...),
    user=Depends(current_user)
):

    import pandas as pd

    if not await db.projects.find_one(
        {
            "id":
                project_id
        }
    ):

        raise HTTPException(
            404,
            "Project not found"
        )

    try:

        if file.filename.lower().endswith(
            ".csv"
        ):

            df = pd.read_csv(
                file.file
            )

        else:

            df = pd.read_excel(
                file.file
            )

    except Exception as e:

        raise HTTPException(
            400,
            f"Could not read update sheet: {e}"
        )

    # Normalize column names
    df.columns = [
        re.sub(
            r"[^a-z0-9]+",
            "_",
            str(column)
            .strip()
            .lower()
        ).strip("_")
        for column in df.columns
    ]

    # Accepted column aliases
    aliases = {

        "code":
            "activity_code",

        "activity":
            "activity_name",

        "name":
            "activity_name",

        "actual":
            "progress",

        "actual_progress":
            "progress",

        "completion":
            "progress",

        "delay":
            "delay_days",

        "reason":
            "delay_reason",

        "comment":
            "remarks",

        "comments":
            "remarks",

        "update":
            "remarks",

        "description":
            "remarks"
    }

    for old, new in aliases.items():

        if (
            old in df.columns
            and new not in df.columns
        ):

            df = df.rename(
                columns={
                    old: new
                }
            )

    if (
        "activity_code" not in df.columns
        and
        "activity_name" not in df.columns
    ):

        raise HTTPException(
            400,
            "Update sheet must contain activity_code or activity_name"
        )

    if "progress" not in df.columns:

        raise HTTPException(
            400,
            "Update sheet must contain progress / actual_progress / completion"
        )

    imported = 0
    errors = []
    results = []

    for index, row in df.iterrows():

        row_number = int(index) + 2

        try:

            code = str(
                row.get(
                    "activity_code",
                    ""
                )
            ).strip()

            name = str(
                row.get(
                    "activity_name",
                    ""
                )
            ).strip()

            query = {
                "project_id":
                    project_id,

                "level":
                    "L6"
            }

            if (
                code
                and
                code.lower() != "nan"
            ):

                query[
                    "activity_code"
                ] = code

            elif (
                name
                and
                name.lower() != "nan"
            ):

                query[
                    "activity_name"
                ] = name

            else:

                raise ValueError(
                    "activity_code or activity_name is required"
                )

            activity = clean(
                await db.activities.find_one(
                    query,
                    {"_id": 0}
                )
            )

            if not activity:

                raise ValueError(
                    f"No matching L6 activity found "
                    f"for {code or name}"
                )

            progress = float(
                row["progress"]
            )

            if not 0 <= progress <= 100:

                raise ValueError(
                    "progress must be between 0 and 100"
                )

            raw_days = row.get(
                "delay_days",
                0
            )

            days = (
                0
                if str(raw_days).lower()
                == "nan"
                else int(
                    float(
                        raw_days or 0
                    )
                )
            )

            reason = str(
                row.get(
                    "delay_reason",
                    ""
                )
                or ""
            ).strip()

            if reason.lower() == "nan":
                reason = ""

            remarks = str(
                row.get(
                    "remarks",
                    ""
                )
                or ""
            ).strip()

            if remarks.lower() == "nan":
                remarks = ""

            result = await save_update(
                project_id=project_id,
                activity=activity,
                progress=progress,
                days=max(
                    0,
                    days
                ),
                reason=reason,
                remarks=remarks,
                transcript=(
                    remarks
                    or
                    f"Excel update: "
                    f"{activity['activity_name']} "
                    f"is {progress}% complete."
                ),
                language="excel",
                user=user,
                similarity=1.0,
                ai_engine="excel",
                forced_risk=False
            )

            imported += 1

            results.append(
                {
                    "row":
                        row_number,

                    "activity":
                        activity["activity_name"],

                    "progress":
                        progress,

                    "status":
                        result["status"]
                }
            )

        except Exception as e:

            errors.append(
                {
                    "row":
                        row_number,

                    "error":
                        str(e)
                }
            )

    return {
        "imported":
            imported,

        "errors":
            errors,

        "results":
            results
    }


# ============================================================
# HISTORY
# ============================================================

async def recent(
    collection_name,
    project_id=None,
    limit=100
):

    query = (
        {
            "project_id":
                project_id
        }
        if project_id
        else {}
    )

    return [
        clean(x)
        async for x in db[
            collection_name
        ].find(
            query,
            {"_id": 0}
        ).sort(
            "created_at",
            -1
        ).limit(
            limit
        )
    ]


@api.get("/updates")
async def updates(
    project_id: Optional[str] = None,
    user=Depends(current_user)
):

    return await recent(
        "updates",
        project_id
    )


@api.get("/risks")
async def risks(
    project_id: Optional[str] = None,
    user=Depends(current_user)
):

    return await recent(
        "risks",
        project_id
    )


@api.get("/recommendations")
async def recommendations(
    project_id: Optional[str] = None,
    user=Depends(current_user)
):

    return await recent(
        "recommendations",
        project_id
    )


# ============================================================
# DASHBOARD
# ============================================================

@api.get("/dashboard")
async def dashboard(
    project_id: Optional[str] = None,
    user=Depends(current_user)
):

    query = (
        {
            "project_id":
                project_id
        }
        if project_id
        else {}
    )

    activities = [
        clean(x)
        async for x in db.activities.find(
            query,
            {"_id": 0}
        )
    ]

    risks_data = await recent(
        "risks",
        project_id,
        20
    )

    updates_data = await recent(
        "updates",
        project_id,
        10
    )

    total = len(
        activities
    )

    average = (
        round(
            sum(
                float(
                    a.get(
                        "actual_progress",
                        0
                    )
                )
                for a in activities
            )
            / total,
            1
        )
        if total
        else 0
    )

    return {
        "kpis": {

            "projects":
                await db.projects.count_documents({}),

            "progress":
                average,

            "activities":
                total,

            "delayed":
                sum(
                    a.get("status")
                    == "DELAYED"
                    for a in activities
                ),

            "at_risk":
                sum(
                    a.get("status")
                    == "AT RISK"
                    for a in activities
                ),

            "risks":
                len(risks_data),

            "critical":
                sum(
                    r.get("severity")
                    in [
                        "CRITICAL",
                        "HIGH"
                    ]
                    for r in risks_data
                )
        },

        "activities":
            activities,

        "risks":
            risks_data,

        "updates":
            updates_data
    }


# ============================================================
# SCHEDULE EXCEL IMPORT
# ============================================================

@api.post("/import/schedule")
async def import_schedule(
    project_id: str,
    file: UploadFile = File(...),
    user=Depends(manager)
):

    import pandas as pd

    if not await db.projects.find_one(
        {
            "id":
                project_id
        }
    ):

        raise HTTPException(
            404,
            "Project not found"
        )

    try:

        if file.filename.lower().endswith(
            ".csv"
        ):

            df = pd.read_csv(
                file.file
            )

        else:

            df = pd.read_excel(
                file.file
            )

    except Exception as e:

        raise HTTPException(
            400,
            f"Could not read schedule: {e}"
        )

    df.columns = [
        re.sub(
            r"[^a-z0-9]+",
            "_",
            str(column)
            .strip()
            .lower()
        ).strip("_")
        for column in df.columns
    ]

    aliases = {
        "code":
            "activity_code",

        "activity":
            "activity_name",

        "name":
            "activity_name",

        "start":
            "planned_start",

        "end":
            "planned_end",

        "planned":
            "planned_progress",

        "progress":
            "planned_progress",

        "parent":
            "parent_activity"
    }

    for old, new in aliases.items():

        if (
            old in df.columns
            and new not in df.columns
        ):

            df = df.rename(
                columns={
                    old: new
                }
            )

    required = {
        "activity_code",
        "activity_name",
        "level",
        "planned_start",
        "planned_end",
        "planned_progress"
    }

    missing = (
        required
        -
        set(df.columns)
    )

    if missing:

        raise HTTPException(
            400,
            "Missing columns: "
            +
            ", ".join(
                sorted(missing)
            )
        )

    documents = []
    errors = []

    for index, row in df.iterrows():

        try:

            level = str(
                row["level"]
            ).upper().strip()

            level = (
                level
                if level in [
                    "L5",
                    "L6"
                ]
                else "L6"
            )

            planned_progress = float(
                row["planned_progress"]
            )

            if not 0 <= planned_progress <= 100:

                raise ValueError(
                    "planned_progress must be 0-100"
                )

            documents.append(
                {
                    "id":
                        str(uuid.uuid4()),

                    "project_id":
                        project_id,

                    "activity_code":
                        str(
                            row["activity_code"]
                        ),

                    "activity_name":
                        str(
                            row["activity_name"]
                        ),

                    "level":
                        level,

                    "parent_activity":
                        str(
                            row.get(
                                "parent_activity",
                                ""
                            )
                        ),

                    "planned_start":
                        str(
                            row["planned_start"]
                        ),

                    "planned_end":
                        str(
                            row["planned_end"]
                        ),

                    "planned_progress":
                        planned_progress,

                    "actual_progress":
                        0.0,

                    "status":
                        "ON TRACK",

                    "created_at":
                        now()
                }
            )

        except Exception as e:

            errors.append(
                {
                    "row":
                        int(index) + 2,

                    "error":
                        str(e)
                }
            )

    if documents:

        await db.activities.insert_many(
            documents
        )

    return {
        "imported":
            len(documents),

        "errors":
            errors
    }


# ============================================================
# APP
# ============================================================

app.include_router(
    api
)

configured_origins = [
    x.strip()
    for x in os.getenv(
        "CORS_ORIGINS",
        ""
    ).split(",")
    if x.strip()
]

origins = sorted(
    set(
        configured_origins
        +
        [
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    )
)

app.add_middleware(
    CORSMiddleware,

    allow_origins=origins,

    allow_origin_regex=
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"]
)


@app.on_event("shutdown")
async def shutdown():

    client.close()