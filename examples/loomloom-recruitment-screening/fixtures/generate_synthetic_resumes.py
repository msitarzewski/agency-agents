#!/usr/bin/env python3
"""Generate synthetic PDF resumes for the Loomloom screening example."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


OUTPUT_DIR = Path(__file__).resolve().parent / "resumes"


PROFILES = [
    {
        "filename": "candidate-strong.pdf",
        "title": "Candidate Strong",
        "headline": "Backend Engineer",
        "summary": (
            "Backend engineer with five years of production Python experience, "
            "focused on API reliability, performance, and service ownership."
        ),
        "experience": [
            (
                "Senior Backend Engineer - Northstar Systems - 2023 to Present",
                [
                    "Designed and operated Python REST APIs serving 4 million requests per day.",
                    "Reduced p95 API latency by 38 percent through query and caching improvements.",
                    "Owned PostgreSQL schema changes, production rollout plans, and on-call response.",
                    "Deployed services to AWS using Docker and Kubernetes.",
                    "Mentored three engineers and introduced API review checklists."
                ],
            ),
            (
                "Backend Engineer - Harbor Analytics - 2021 to 2023",
                [
                    "Built Python data services and documented REST endpoints for partner teams.",
                    "Added service metrics and alerts that reduced repeated incidents by 24 percent."
                ],
            ),
        ],
        "skills": "Python, FastAPI, REST APIs, PostgreSQL, Redis, Docker, Kubernetes, AWS, observability",
        "projects": (
            "Led a zero-downtime migration of a customer API from a monolith to three services, "
            "including load tests, rollback procedures, and production monitoring."
        ),
    },
    {
        "filename": "candidate-consider.pdf",
        "title": "Candidate Consider",
        "headline": "Software Engineer",
        "summary": (
            "Software engineer with three years of web-service experience and recent hands-on "
            "Python delivery in internal automation projects."
        ),
        "experience": [
            (
                "Software Engineer - Meridian Commerce - 2024 to Present",
                [
                    "Maintained Node.js REST APIs and integrated payment and inventory services.",
                    "Created Python scripts that reduced manual reconciliation time by 12 hours per month.",
                    "Used Docker for local development and continuous integration builds.",
                    "Participated in production incident reviews with the service owner."
                ],
            ),
            (
                "Junior Software Engineer - Cedar Works - 2023 to 2024",
                [
                    "Implemented TypeScript endpoints and MongoDB data access for internal tools.",
                    "Added unit tests and API documentation for two customer-facing features."
                ],
            ),
        ],
        "skills": "TypeScript, Node.js, Python, REST APIs, MongoDB, Docker, GitHub Actions",
        "projects": (
            "Built a small FastAPI service for an internal hackathon and deployed it to a test "
            "environment; production ownership and relational database experience are not stated."
        ),
    },
    {
        "filename": "candidate-reject.pdf",
        "title": "Candidate Reject",
        "headline": "Frontend Developer",
        "summary": (
            "Frontend developer with two years of experience building responsive web interfaces "
            "and component libraries."
        ),
        "experience": [
            (
                "Frontend Developer - Lumen Studio - 2024 to Present",
                [
                    "Built React and TypeScript interfaces for marketing and account pages.",
                    "Improved Lighthouse accessibility scores from 78 to 94.",
                    "Worked with designers to maintain a shared component library."
                ],
            ),
            (
                "Web Design Intern - Orchard Creative - 2023",
                [
                    "Implemented HTML and CSS landing pages from design specifications.",
                    "Performed cross-browser visual testing."
                ],
            ),
        ],
        "skills": "React, TypeScript, JavaScript, HTML, CSS, Storybook, Figma",
        "projects": (
            "Created a reusable form component library. No production Python, backend API design, "
            "relational database, or service operations experience is stated."
        ),
    },
]


def footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(0.65 * inch, 0.38 * inch, "Synthetic resume for testing only")
    canvas.drawRightString(7.85 * inch, 0.38 * inch, f"Page {document.page}")
    canvas.restoreState()


def build_resume(profile: dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / str(profile["filename"])
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.62 * inch,
        title=str(profile["title"]),
        author="Synthetic test fixture",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ResumeTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#173F35"),
        spaceAfter=2,
    )
    headline_style = ParagraphStyle(
        "Headline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475467"),
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#176B57"),
        borderColor=colors.HexColor("#D0D5DD"),
        borderWidth=0,
        borderPadding=0,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=12.2,
        textColor=colors.HexColor("#1D2939"),
        spaceAfter=4,
    )
    role_style = ParagraphStyle(
        "Role",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#344054"),
        spaceBefore=3,
        spaceAfter=2,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-7,
        bulletIndent=0,
        spaceAfter=2,
    )

    story = [
        Paragraph(str(profile["title"]), title_style),
        Paragraph(str(profile["headline"]), headline_style),
        Paragraph("PROFESSIONAL SUMMARY", section_style),
        Paragraph(str(profile["summary"]), body_style),
        Paragraph("EXPERIENCE", section_style),
    ]
    for role, bullets in profile["experience"]:  # type: ignore[index]
        story.append(Paragraph(str(role), role_style))
        for bullet in bullets:
            story.append(Paragraph(f"- {bullet}", bullet_style))
    story.extend(
        [
            Paragraph("SKILLS", section_style),
            Paragraph(str(profile["skills"]), body_style),
            Paragraph("SELECTED PROJECT", section_style),
            Paragraph(str(profile["projects"]), body_style),
            Spacer(1, 6),
            Paragraph(
                "This document contains fictional information created solely to test the "
                "Loomloom recruitment-screening workflow.",
                ParagraphStyle(
                    "FixtureNote",
                    parent=body_style,
                    fontSize=8,
                    leading=10,
                    textColor=colors.HexColor("#667085"),
                ),
            ),
        ]
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    for profile in PROFILES:
        build_resume(profile)
    print(f"generated={len(PROFILES)} output={OUTPUT_DIR}")


if __name__ == "__main__":
    main()
