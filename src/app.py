"""
Slalom Capabilities Management System API

A FastAPI application that enables Slalom consultants to register their
capabilities and manage consulting expertise across the organization.
"""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./capabilities.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Capability(Base):
    __tablename__ = "capabilities"

    name = Column(String, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    practice_area = Column(String, nullable=False)
    skill_levels = Column(Text, nullable=False)       # JSON-encoded list
    certifications = Column(Text, nullable=False)     # JSON-encoded list
    industry_verticals = Column(Text, nullable=False) # JSON-encoded list
    capacity = Column(Integer, nullable=False)


class ConsultantRegistration(Base):
    __tablename__ = "consultant_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    capability_name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

SEED_CAPABILITIES = [
    {
        "name": "Cloud Architecture",
        "description": "Design and implement scalable cloud solutions using AWS, Azure, and GCP",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["AWS Solutions Architect", "Azure Architect Expert"],
        "industry_verticals": ["Healthcare", "Financial Services", "Retail"],
        "capacity": 40,
        "consultants": ["alice.smith@slalom.com", "bob.johnson@slalom.com"],
    },
    {
        "name": "Data Analytics",
        "description": "Advanced data analysis, visualization, and machine learning solutions",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Tableau Desktop Specialist", "Power BI Expert", "Google Analytics"],
        "industry_verticals": ["Retail", "Healthcare", "Manufacturing"],
        "capacity": 35,
        "consultants": ["emma.davis@slalom.com", "sophia.wilson@slalom.com"],
    },
    {
        "name": "DevOps Engineering",
        "description": "CI/CD pipeline design, infrastructure automation, and containerization",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Docker Certified Associate", "Kubernetes Admin", "Jenkins Certified"],
        "industry_verticals": ["Technology", "Financial Services"],
        "capacity": 30,
        "consultants": ["john.brown@slalom.com", "olivia.taylor@slalom.com"],
    },
    {
        "name": "Digital Strategy",
        "description": "Digital transformation planning and strategic technology roadmaps",
        "practice_area": "Strategy",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Digital Transformation Certificate", "Agile Certified Practitioner"],
        "industry_verticals": ["Healthcare", "Financial Services", "Government"],
        "capacity": 25,
        "consultants": ["liam.anderson@slalom.com", "noah.martinez@slalom.com"],
    },
    {
        "name": "Change Management",
        "description": "Organizational change leadership and adoption strategies",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Prosci Certified", "Lean Six Sigma Black Belt"],
        "industry_verticals": ["Healthcare", "Manufacturing", "Government"],
        "capacity": 20,
        "consultants": ["ava.garcia@slalom.com", "mia.rodriguez@slalom.com"],
    },
    {
        "name": "UX/UI Design",
        "description": "User experience design and digital product innovation",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Adobe Certified Expert", "Google UX Design Certificate"],
        "industry_verticals": ["Retail", "Healthcare", "Technology"],
        "capacity": 30,
        "consultants": ["amelia.lee@slalom.com", "harper.white@slalom.com"],
    },
    {
        "name": "Cybersecurity",
        "description": "Information security strategy, risk assessment, and compliance",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["CISSP", "CISM", "CompTIA Security+"],
        "industry_verticals": ["Financial Services", "Healthcare", "Government"],
        "capacity": 25,
        "consultants": ["ella.clark@slalom.com", "scarlett.lewis@slalom.com"],
    },
    {
        "name": "Business Intelligence",
        "description": "Enterprise reporting, data warehousing, and business analytics",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Microsoft BI Certification", "Qlik Sense Certified"],
        "industry_verticals": ["Retail", "Manufacturing", "Financial Services"],
        "capacity": 35,
        "consultants": ["james.walker@slalom.com", "benjamin.hall@slalom.com"],
    },
    {
        "name": "Agile Coaching",
        "description": "Agile transformation and team coaching for scaled delivery",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Certified Scrum Master", "SAFe Agilist", "ICAgile Certified"],
        "industry_verticals": ["Technology", "Financial Services", "Healthcare"],
        "capacity": 20,
        "consultants": ["charlotte.young@slalom.com", "henry.king@slalom.com"],
    },
]


def seed_database(db: Session) -> None:
    """Populate the database with initial capability data if empty."""
    if db.query(Capability).count() > 0:
        return
    for item in SEED_CAPABILITIES:
        capability = Capability(
            name=item["name"],
            description=item["description"],
            practice_area=item["practice_area"],
            skill_levels=json.dumps(item["skill_levels"]),
            certifications=json.dumps(item["certifications"]),
            industry_verticals=json.dumps(item["industry_verticals"]),
            capacity=item["capacity"],
        )
        db.add(capability)
        for email in item["consultants"]:
            db.add(ConsultantRegistration(capability_name=item["name"], email=email))
    db.commit()


# Seed on startup
with SessionLocal() as _seed_session:
    seed_database(_seed_session)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Slalom Capabilities Management API",
    description="API for managing consulting capabilities and consultant expertise",
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _capability_to_dict(capability: Capability, db: Session) -> dict:
    registrations = (
        db.query(ConsultantRegistration)
        .filter(ConsultantRegistration.capability_name == capability.name)
        .all()
    )
    return {
        "description": capability.description,
        "practice_area": capability.practice_area,
        "skill_levels": json.loads(capability.skill_levels),
        "certifications": json.loads(capability.certifications),
        "industry_verticals": json.loads(capability.industry_verticals),
        "capacity": capability.capacity,
        "consultants": [r.email for r in registrations],
    }


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/capabilities")
def get_capabilities(db: Session = Depends(get_db)):
    capabilities = db.query(Capability).all()
    return {cap.name: _capability_to_dict(cap, db) for cap in capabilities}


@app.post("/capabilities/{capability_name}/register")
def register_for_capability(capability_name: str, email: str, db: Session = Depends(get_db)):
    """Register a consultant for a capability"""
    capability = db.query(Capability).filter(Capability.name == capability_name).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    existing = (
        db.query(ConsultantRegistration)
        .filter(
            ConsultantRegistration.capability_name == capability_name,
            ConsultantRegistration.email == email,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Consultant is already registered for this capability",
        )

    db.add(ConsultantRegistration(capability_name=capability_name, email=email))
    db.commit()
    return {"message": f"Registered {email} for {capability_name}"}


@app.delete("/capabilities/{capability_name}/unregister")
def unregister_from_capability(capability_name: str, email: str, db: Session = Depends(get_db)):
    """Unregister a consultant from a capability"""
    capability = db.query(Capability).filter(Capability.name == capability_name).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    registration = (
        db.query(ConsultantRegistration)
        .filter(
            ConsultantRegistration.capability_name == capability_name,
            ConsultantRegistration.email == email,
        )
        .first()
    )
    if not registration:
        raise HTTPException(
            status_code=400,
            detail="Consultant is not registered for this capability",
        )

    db.delete(registration)
    db.commit()
    return {"message": f"Unregistered {email} from {capability_name}"}
