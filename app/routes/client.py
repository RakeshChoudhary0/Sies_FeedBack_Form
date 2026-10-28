from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
try:
    import models
    from database import SessionLocal
except ImportError:
    from app import models
    from app.database import SessionLocal
from datetime import datetime

from pathlib import Path
router = APIRouter()
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["now"] = datetime.now

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # This serves your landing page as the home page
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/select-category", response_class=HTMLResponse)
async def select_category(request: Request):
    return templates.TemplateResponse(request=request, name="categoryselection.html")

def forms_closed_response():
    return HTMLResponse(
        content="""
        <html>
        <head>
            <title>Forms Closed</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 flex items-center justify-center h-screen">
            <div class="bg-white p-8 rounded-xl shadow-md text-center max-w-md">
                <h1 class="text-2xl font-bold text-red-600 mb-4">
                    Feedback Forms Closed
                </h1>
                <p class="text-gray-600 mb-6">
                    Submissions are currently disabled by the administrator.
                    Please try again later.
                </p>
                <a href="/" 
                   class="inline-block bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition">
                    Go Back
                </a>
            </div>
        </body>
        </html>
        """,
        status_code=403
    )

@router.get("/feedback/{form_name}", response_class=HTMLResponse)
async def get_form(
    request: Request,
    form_name: str,
    db: Session = Depends(get_db)
):
    settings = db.query(models.SystemSettings).first()
    if settings and not settings.is_active:
        return forms_closed_response()

    # Map form names to stakeholder_type values
    stakeholder_map = {
        "studentfeedback": "STUDENT",
        "parentfeedback": "PARENT",
        "alumnifeedback": "ALUMNI",
        "internalfaculty": "TEACHER",
        "externalfaculty": "OUTSIDE_TEACHER",
        "industryrep": "EMPLOYER"
    }

    stakeholder = stakeholder_map.get(form_name)

    if stakeholder is None:
        raise HTTPException(status_code=404, detail="Invalid feedback form")

    # Fetch questions directly using normalized columns
    questions = (
        db.query(models.SyllabusQuestion)
        .filter(models.SyllabusQuestion.stakeholder_type == stakeholder)
        .order_by(models.SyllabusQuestion.id)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name=f"feedbackForms/{form_name}.html",
        context={
            "questions": questions,
            "form_name": form_name
        }
    )

@router.post("/submit-feedback")
async def submit_feedback(
    request: Request,
    db: Session = Depends(get_db)
):
    settings = db.query(models.SystemSettings).first()

    if settings and not settings.is_active:
        return forms_closed_response()


    form = await request.form()

    # 1️⃣ Get or create feedback session
    feedback_session = (
        db.query(models.FeedbackSession)
        .filter(models.FeedbackSession.session_name == "Default Session")
        .first()
    )

    if not feedback_session:
        feedback_session = models.FeedbackSession(session_name="Default Session")
        db.add(feedback_session)
        db.commit()
        db.refresh(feedback_session)

    # 2️⃣ Resolve stakeholder_type from form_name
    form_name = form.get("form_name")

    stakeholder_map = {
        "studentfeedback": "STUDENT",
        "parentfeedback": "PARENT",
        "alumnifeedback": "ALUMNI",
        "internalfaculty": "TEACHER",
        "externalfaculty": "OUTSIDE_TEACHER",
        "industryrep": "EMPLOYER"
    }

    stakeholder_type = stakeholder_map.get(form_name)
    if not stakeholder_type:
        raise HTTPException(status_code=400, detail="Invalid form")

    stakeholder = (
        db.query(models.Stakeholder)
        .filter(models.Stakeholder.stakeholder_type == stakeholder_type)
        .first()
    )

    if not stakeholder:
        stakeholder = models.Stakeholder(stakeholder_type=stakeholder_type)
        db.add(stakeholder)
        db.commit()
        db.refresh(stakeholder)

    # 3️⃣ Create person entry (no hard-coded name fields)
    person = models.StakeholderPersonalInfo(
        session_id=feedback_session.session_id,
        stakeholder_id=stakeholder.stakeholder_id,
        name="N/A",               # optional placeholder
        association_name=None     # optional placeholder
    )
    db.add(person)
    db.flush()  # IMPORTANT: get person_id without committing

    # 4️⃣ Save ALL answers dynamically
    for key, value in form.items():
        if key.startswith("q_"):
            try:
                question_id = int(key.split("_")[1])
            except ValueError:
                continue

            db.add(
                models.FeedbackAnswer(
                    person_id=person.person_id,
                    question_id=question_id,
                    answer_text=str(value)
                )
            )

    db.commit()

    return RedirectResponse(url="/submitted-feedback", status_code=303)

@router.get("/submitted-feedback", response_class=HTMLResponse)
async def submit_conf(request: Request):
    return templates.TemplateResponse(request=request, name="thankyou.html")
