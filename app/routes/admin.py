from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer
try:
    import models
    from database import SessionLocal
    from auth import verify_password, create_access_token, decode_access_token
except ImportError:
    from app import models
    from app.database import SessionLocal
    from app.auth import verify_password, create_access_token, decode_access_token
from jose import JWTError
import re, csv, io

from pathlib import Path
router = APIRouter(prefix="/admin") 
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# DB DEPENDENCY
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT AUTH DEPENDENCY
def admin_required(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        request.state.admin_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Admin login
@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin_login.html")

# LOGIN ACTION (JWT)
@router.post("/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = db.query(models.AdminUser).filter(
        models.AdminUser.username == username
    ).first()

    if not admin or not verify_password(password, admin.password):
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={"error": "Invalid username or password"},
            status_code=401
        )

    token = create_access_token({"sub": str(admin.admin_id)})

    response = RedirectResponse(
        url="/admin/dashboard",
        status_code=status.HTTP_302_FOUND
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,     # True in production (HTTPS)
        samesite="lax"
    )

    return response

@router.get("/logout")
async def admin_logout():
    response = RedirectResponse("/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token", path="/")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# DASHBOARD
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    stakeholder_id: int | None = None,
    stream: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(admin_required)
):
    settings = db.query(models.SystemSettings).first()
    form_active = settings.is_active if settings else True

    # -----------------------------
    # SIDEBAR STAKEHOLDERS
    # -----------------------------
    stakeholders = db.query(models.Stakeholder).order_by(
        models.Stakeholder.stakeholder_type
    ).all()

    # -----------------------------
    # TOTAL UNIQUE RESPONDENTS
    # -----------------------------
    total_query = (
        db.query(func.count(func.distinct(models.FeedbackAnswer.person_id)))
        .join(
            models.StakeholderPersonalInfo,
            models.FeedbackAnswer.person_id == models.StakeholderPersonalInfo.person_id
        )
    )

    if stakeholder_id:
        total_query = total_query.filter(
            models.StakeholderPersonalInfo.stakeholder_id == stakeholder_id
        )

    total_feedback = total_query.scalar() or 0

    # =========================================================
    # CASE 1: ALL STAKEHOLDERS (CUMULATIVE BAR CHART)
    # =========================================================

    if stakeholder_id is None:
        raw_results = (
            db.query(
                models.Stakeholder.stakeholder_type.label("stakeholder"),
                func.avg(
                    cast(models.FeedbackAnswer.answer_text, Integer)
                ).label("average_score")
            )
            .select_from(models.Stakeholder)
            .join(
                models.StakeholderPersonalInfo,
                models.Stakeholder.stakeholder_id == models.StakeholderPersonalInfo.stakeholder_id
            )
            .join(
                models.FeedbackAnswer,
                models.StakeholderPersonalInfo.person_id == models.FeedbackAnswer.person_id
            )
            .join(
                models.SyllabusQuestion,
                models.FeedbackAnswer.question_id == models.SyllabusQuestion.id
            )
            .filter(models.SyllabusQuestion.category == "SYLLABUS")
            .group_by(models.Stakeholder.stakeholder_id)
            .order_by(models.Stakeholder.stakeholder_type)
            .all()
        )

        results = [
            {
                "label": r.stakeholder,  # ← FIX HERE
                "average_score": round(float(r.average_score), 2)
            }
            for r in raw_results
        ]


        response = templates.TemplateResponse(
            request=request,
            name="admin_dashboard.html",
            context={
                "mode": "ALL",
                "results": results,
                "total_feedback": total_feedback,
                "stakeholders": stakeholders,
                "selected_stakeholder": None,
                "form_active": form_active,
            }
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # =========================================================
    # CASE 2: SINGLE STAKEHOLDER
    # =========================================================

    stakeholder = db.query(models.Stakeholder).filter(
        models.Stakeholder.stakeholder_id == stakeholder_id
    ).first()

    # -----------------------------
    # SYLLABUS QUESTIONS (ORDERED)
    # -----------------------------
    syllabus_questions = (
        db.query(models.SyllabusQuestion)
        .filter(
            models.SyllabusQuestion.category == "SYLLABUS",
            models.SyllabusQuestion.stakeholder_type == stakeholder.stakeholder_type
        )
        .order_by(models.SyllabusQuestion.id)
        .all()
    )

    qid_to_qnum = {
        q.id: f"q{i+1}"
        for i, q in enumerate(syllabus_questions)
    }

    question_numbers = list(qid_to_qnum.values())

    # -----------------------------
    # BAR CHART DATA
    # -----------------------------
    raw_results = (
        db.query(
            models.FeedbackAnswer.question_id,
            func.count(models.FeedbackAnswer.answer_id).label("responses"),
            func.avg(cast(models.FeedbackAnswer.answer_text, Integer)).label("average_score")
        )
        .join(models.StakeholderPersonalInfo)
        .join(models.SyllabusQuestion)
        .filter(
            models.StakeholderPersonalInfo.stakeholder_id == stakeholder_id,
            models.SyllabusQuestion.category == "SYLLABUS"
        )
        .group_by(models.FeedbackAnswer.question_id)
        .order_by(models.FeedbackAnswer.question_id)
        .all()
    )

    results = [
        {
            "question": qid_to_qnum.get(r.question_id),
            "responses": int(r.responses),
            "average_score": round(float(r.average_score), 2)
        }
        for r in raw_results
        if r.question_id in qid_to_qnum
    ]

    # -----------------------------
    # DEMOGRAPHIC QUESTIONS
    # -----------------------------
    demographic_questions = (
        db.query(models.SyllabusQuestion)
        .filter(
            models.SyllabusQuestion.category == "DEMOGRAPHIC",
            models.SyllabusQuestion.stakeholder_type == stakeholder.stakeholder_type
        )
        .order_by(models.SyllabusQuestion.id)
        .all()
    )

    demographic_headers = []

    demo_qid_to_key = {}

    for q in demographic_questions:
        # Remove tags like [STUDENT][DEMOGRAPHIC]
        clean_label = re.sub(r"\[.*?\]", "", q.text).strip()

        # Normalize key (safe dict key)
        key = (
            clean_label
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
        )

        demographic_headers.append({
            "label": clean_label,
            "key": key,
            "question_id": q.id
        })

        demo_qid_to_key[q.id] = key

    # SUGGESTIONS

    suggestion_questions = (
        db.query(models.SyllabusQuestion)
        .filter(
            models.SyllabusQuestion.category == "SUGGESTION",
            models.SyllabusQuestion.stakeholder_type == stakeholder.stakeholder_type
        )
        .all()
    )

    suggestion_qids = [q.id for q in suggestion_questions]

    # -----------------------------
    # STREAM OPTIONS (FIXED)
    # -----------------------------
    stream_qids = [
        q.id for q in demographic_questions
        if any(x in q.text.lower() for x in ["course", "program", "stream"])
    ]

    # -----------------------------
    # STREAM OPTIONS
    # -----------------------------
    stream_options = (
        db.query(models.FeedbackAnswer.answer_text)
        .join(models.StakeholderPersonalInfo)
        .filter(
            models.FeedbackAnswer.question_id.in_(stream_qids),
            models.StakeholderPersonalInfo.stakeholder_id == stakeholder_id
        )
        .distinct()
        .all()
    )

    stream_options = sorted([s[0] for s in stream_options if s[0]])

    # -----------------------------
    # FETCH ANSWERS
    # -----------------------------
    answers = (
        db.query(
            models.StakeholderPersonalInfo.person_id,
            models.StakeholderPersonalInfo.name,
            models.FeedbackAnswer.question_id,
            models.FeedbackAnswer.answer_text
        )
        .join(models.FeedbackAnswer)
        .filter(models.StakeholderPersonalInfo.stakeholder_id == stakeholder_id)
        .all()
    )

    # -----------------------------
    # PIVOT TABLE
    # -----------------------------
    row_map = {}
    person_stream_map = {}

    for r in answers:
        row = row_map.setdefault(r.person_id, {
            "person_id": r.person_id,
            "name": r.name
        })

        if r.question_id in demo_qid_to_key:
            key = demo_qid_to_key[r.question_id]
            row[key] = r.answer_text

            if r.question_id in stream_qids:
                person_stream_map[r.person_id] = r.answer_text

        if r.question_id in qid_to_qnum:
            row[qid_to_qnum[r.question_id]] = r.answer_text

        if r.question_id in suggestion_qids:
            row["suggestion"] = r.answer_text

    responses_table = list(row_map.values())

    # -----------------------------
    # FIND STREAM QUESTION IDS
    # -----------------------------
    stream_question_ids = [
        q.id for q in demographic_questions
        if any(word in q.text.lower() for word in ["course", "program", "stream"])
    ]

    person_stream_map = {}

    stream_answers = (
        db.query(
            models.FeedbackAnswer.person_id,
            models.FeedbackAnswer.answer_text,
            models.FeedbackAnswer.question_id
        )
        .filter(models.FeedbackAnswer.question_id.in_(stream_question_ids))
        .all()
    )

    for s in stream_answers:
        person_stream_map[s.person_id] = s.answer_text

    if stream and stream.strip():
        target_stream = stream.strip()
        responses_table = [
            r for r in responses_table
            if person_stream_map.get(r["person_id"], "").strip() == target_stream
        ]
        total_feedback = len(responses_table)

    response = templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "mode": "SINGLE",
            "results": results,
            "questions": syllabus_questions,
            "question_numbers": question_numbers,
            "responses_table": responses_table,
            "stream_options": stream_options,
            "selected_stream": stream.strip() if stream else None,
            "total_feedback": total_feedback,
            "stakeholders": stakeholders,
            "selected_stakeholder": stakeholder_id,
            "demographic_headers": demographic_headers,
            "form_active": form_active,
        }
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.post("/update-responses")
async def update_demographic_responses(
    updates: list[dict],
    db: Session = Depends(get_db),
    _: None = Depends(admin_required)
):
    for item in updates:
        person_id = item["person_id"]
        question_id = item["question_id"]
        value = item["value"]

        # Ensure question is DEMOGRAPHIC
        question = db.query(models.SyllabusQuestion).filter(
            models.SyllabusQuestion.id == question_id,
            models.SyllabusQuestion.category == "DEMOGRAPHIC"
        ).first()

        if not question:
            continue  # ❌ silently ignore non-demographic edits

        answer = db.query(models.FeedbackAnswer).filter(
            models.FeedbackAnswer.person_id == person_id,
            models.FeedbackAnswer.question_id == question_id
        ).first()

        if answer:
            answer.answer_text = value

    db.commit()
    return {"status": "ok"}



@router.get("/export/stakeholder")
def export_stakeholder_csv(
    stakeholder_id: int,
    stream: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(admin_required)
):
    stakeholder = db.query(models.Stakeholder).filter(
        models.Stakeholder.stakeholder_id == stakeholder_id
    ).first()

    if not stakeholder:
        return {"error": "Invalid stakeholder"}

    # -----------------------------
    # DEMOGRAPHIC QUESTIONS
    # -----------------------------
    demographic_questions = (
        db.query(models.SyllabusQuestion)
        .filter(
            models.SyllabusQuestion.category == "DEMOGRAPHIC",
            models.SyllabusQuestion.stakeholder_type == stakeholder.stakeholder_type
        )
        .order_by(models.SyllabusQuestion.id)
        .all()
    )

    demo_qid_to_key = {}
    demo_headers = []

    for q in demographic_questions:
        label = re.sub(r"\[.*?\]", "", q.text).strip()
        key = label.lower().replace(" ", "_").replace("/", "_")
        demo_qid_to_key[q.id] = key
        demo_headers.append(label)

    # -----------------------------
    # SYLLABUS QUESTIONS
    # -----------------------------
    syllabus_questions = (
        db.query(models.SyllabusQuestion)
        .filter(
            models.SyllabusQuestion.category == "SYLLABUS",
            models.SyllabusQuestion.stakeholder_type == stakeholder.stakeholder_type
        )
        .order_by(models.SyllabusQuestion.id)
        .all()
    )

    qid_to_qnum = {q.id: f"q{i+1}" for i, q in enumerate(syllabus_questions)}
    syllabus_headers = list(qid_to_qnum.values())

    # -----------------------------
    # SUGGESTION QUESTIONS
    # -----------------------------
    suggestion_questions = (
        db.query(models.SyllabusQuestion)
        .filter(
            models.SyllabusQuestion.category == "SUGGESTION",
            models.SyllabusQuestion.stakeholder_type == stakeholder.stakeholder_type
        )
        .all()
    )
    suggestion_qids = [q.id for q in suggestion_questions]

    # -----------------------------
    # STREAM QUESTION IDS
    # -----------------------------
    stream_qids = [
        q.id for q in demographic_questions
        if any(x in q.text.lower() for x in ["course", "program", "stream"])
    ]

    # -----------------------------
    # FETCH ANSWERS
    # -----------------------------
    answers = (
        db.query(
            models.StakeholderPersonalInfo.person_id,
            models.StakeholderPersonalInfo.name,
            models.FeedbackAnswer.question_id,
            models.FeedbackAnswer.answer_text
        )
        .join(models.FeedbackAnswer)
        .filter(models.StakeholderPersonalInfo.stakeholder_id == stakeholder_id)
        .order_by(
            models.StakeholderPersonalInfo.person_id,
            models.FeedbackAnswer.question_id
        )
        .all()
    )

    rows = {}
    person_stream_map = {}

    for a in answers:
        row = rows.setdefault(a.person_id, {
            "person_id": a.person_id,
            "name": a.name,
        })

        if a.question_id in demo_qid_to_key:
            row[demo_qid_to_key[a.question_id]] = a.answer_text
            if a.question_id in stream_qids:
                person_stream_map[a.person_id] = a.answer_text

        if a.question_id in qid_to_qnum:
            row[qid_to_qnum[a.question_id]] = a.answer_text

        if a.question_id in suggestion_qids:
            row["suggestion"] = a.answer_text

    data = list(rows.values())

    # -----------------------------
    # STREAM FILTER
    # -----------------------------
    if stream and stream.strip():
        target_stream = stream.strip()
        data = [
            r for r in data
            if person_stream_map.get(r["person_id"], "").strip() == target_stream
        ]
        safe_stream = re.sub(r'[^a-zA-Z0-9_-]', '_', target_stream)
        filename = f"{stakeholder.stakeholder_type}_{safe_stream}_responses.csv"
    else:
        filename = f"{stakeholder.stakeholder_type}_responses.csv"

    # -----------------------------
    # CSV BUILD
    # -----------------------------
    output = io.StringIO()
    writer = csv.writer(output)

    header = ["Person ID", "Name"] + demo_headers + syllabus_headers + ["Suggestions"]
    writer.writerow(header)

    for r in data:
        row = [
            r.get("person_id"),
            r.get("name")
        ]
        for q in demo_qid_to_key.values():
            row.append(r.get(q, ""))
        for q in syllabus_headers:
            row.append(r.get(q, ""))
        row.append(r.get("suggestion", ""))
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-store, no-cache, must-revalidate",
        }
    )


@router.get("/export/all")
def export_all_csv(
    db: Session = Depends(get_db),
    _: None = Depends(admin_required)
):
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "Stakeholder",
        "Person ID",
        "Name",
        "Question",
        "Answer"
    ])

    rows = (
        db.query(
            models.Stakeholder.stakeholder_type.label("stakeholder"),
            models.StakeholderPersonalInfo.person_id,
            models.StakeholderPersonalInfo.name,
            models.SyllabusQuestion.text,
            models.FeedbackAnswer.answer_text
        )
        .select_from(models.Stakeholder)   # ✅ EXPLICIT ROOT
        .join(
            models.StakeholderPersonalInfo,
            models.Stakeholder.stakeholder_id == models.StakeholderPersonalInfo.stakeholder_id
        )
        .join(
            models.FeedbackAnswer,
            models.StakeholderPersonalInfo.person_id == models.FeedbackAnswer.person_id
        )
        .join(
            models.SyllabusQuestion,
            models.FeedbackAnswer.question_id == models.SyllabusQuestion.id
        )
        .order_by(
            models.Stakeholder.stakeholder_type,
            models.StakeholderPersonalInfo.person_id,
            models.SyllabusQuestion.id
        )
        .all()
    )

    for r in rows:
        clean_question = re.sub(r"\[.*?\]", "", r.text).strip()
        writer.writerow([
            r.stakeholder,
            r.person_id,
            r.name,
            clean_question,
            r.answer_text
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=all_stakeholders_responses.csv",
            "Cache-Control": "no-store, no-cache, must-revalidate",
        }
    )

@router.post("/toggle-forms")
def toggle_forms(
    db: Session = Depends(get_db),
    _: None = Depends(admin_required)
):
    settings = db.query(models.SystemSettings).first()

    if not settings:
        settings = models.SystemSettings(id=1, is_active=False)
        db.add(settings)
    else:
        settings.is_active = not settings.is_active

    db.commit()

    return {"status": settings.is_active}
