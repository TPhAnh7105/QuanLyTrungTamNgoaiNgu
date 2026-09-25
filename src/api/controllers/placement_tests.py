from typing import List, Any, Optional
from fastapi import APIRouter, Header, Query, status
from sqlalchemy import text
import json

from src.infrastructure.database.connection import AsyncSessionLocal
from src.application.dtos.placement_test import (
    PlacementTestResultDto,
    CourseRecommendationDto
)
from src.application.services.ai_service import AIService
from src.domain.exceptions.base import DomainException
from src.api.auth_helper import verify_auth_sql

router = APIRouter(prefix="/placement-tests", tags=["AI Placement Test (Direct SQL Queries)"])

@router.post("/submit", response_model=PlacementTestResultDto, status_code=status.HTTP_200_OK)
async def submit_placement_test(
    student_id: int = Query(..., description="ID của học viên"),
    essay_text: str = Query(..., min_length=20, description="Nội dung bài viết luận tiếng Anh"),
    authorization: Optional[str] = Header(None)
):
    """
    Nộp bài thi xếp lớp và chấm điểm AI bằng SQL Queries trực tiếp.
    """
    await verify_auth_sql(authorization)

    async with AsyncSessionLocal() as session:
        # 1. Kiểm tra học viên tồn tại bằng SQL
        student_query = text("SELECT id, full_name FROM students WHERE id = :student_id AND is_deleted = 0")
        res_student = await session.execute(student_query, {"student_id": student_id})
        student = res_student.mappings().first()
        if not student:
            raise DomainException("Học viên không tồn tại.", status_code=404)

        # 2. Lấy hoặc tạo Exam Placement bằng SQL
        exam_query = text("SELECT id FROM exams WHERE exam_type = 'Placement' AND is_deleted = 0 LIMIT 1")
        res_exam = await session.execute(exam_query)
        exam = res_exam.mappings().first()
        if not exam:
            insert_exam_query = text("""
                INSERT INTO exams (name, exam_type, max_score, is_deleted, created_at)
                VALUES ('Bài thi Xếp lớp Tiếng Anh (AI Placement Test)', 'Placement', 10.00, 0, NOW())
            """)
            await session.execute(insert_exam_query)
            await session.commit()
            res_exam = await session.execute(exam_query)
            exam = res_exam.mappings().first()

        # 3. Chấm bài bằng AI
        ai_service = AIService()
        evaluation = await ai_service.evaluate_essay(essay_text)

        # 4. Lưu Grade bằng SQL
        insert_grade_query = text("""
            INSERT INTO grades (student_id, exam_id, score, essay_text, ai_evaluation_json, graded_by, graded_at, is_deleted)
            VALUES (:student_id, :exam_id, :score, :essay_text, :ai_evaluation_json, NULL, NOW(), 0)
        """)
        await session.execute(insert_grade_query, {
            "student_id": student["id"],
            "exam_id": exam["id"],
            "score": evaluation.band_score,
            "essay_text": essay_text,
            "ai_evaluation_json": evaluation.model_dump_json()
        })
        await session.commit()

        # Lấy grade vừa tạo
        get_grade_query = text("SELECT * FROM grades WHERE student_id = :student_id AND exam_id = :exam_id ORDER BY id DESC LIMIT 1")
        grade = (await session.execute(get_grade_query, {"student_id": student["id"], "exam_id": exam["id"]})).mappings().first()

        # 5. Gợi ý khóa học phù hợp theo CEFR level bằng SQL
        courses_query = text("""
            SELECT id, name, level, fee 
            FROM courses 
            WHERE level = :level AND is_active = 1 AND is_deleted = 0 
            LIMIT 5
        """)
        res_courses = await session.execute(courses_query, {"level": evaluation.cefr_level})
        recommended_courses = [
            CourseRecommendationDto(
                id=c["id"],
                name=c["name"],
                level=c["level"],
                fee=float(c["fee"])
            )
            for c in res_courses.mappings().all()
        ]

        return PlacementTestResultDto(
            grade_id=grade["id"],
            student_id=student["id"],
            exam_id=exam["id"],
            score=float(grade["score"]),
            cefr_level=evaluation.cefr_level,
            evaluation_details=evaluation,
            recommended_courses=recommended_courses,
            graded_at=grade["graded_at"]
        )

@router.get("/history", response_model=List[Any])
async def get_placement_test_history(
    student_id: int = Query(..., description="ID của học viên"),
    authorization: Optional[str] = Header(None)
):
    """
    Lấy lịch sử chấm điểm thi xếp lớp bằng SQL Query.
    """
    await verify_auth_sql(authorization)

    async with AsyncSessionLocal() as session:
        query = text("""
            SELECT id, exam_id, score, essay_text, ai_evaluation_json, graded_at
            FROM grades 
            WHERE student_id = :student_id AND is_deleted = 0 
            ORDER BY graded_at DESC
        """)
        res = await session.execute(query, {"student_id": student_id})
        grades = res.mappings().all()

        results = []
        for g in grades:
            eval_details = None
            if g["ai_evaluation_json"]:
                try:
                    eval_details = json.loads(g["ai_evaluation_json"])
                except Exception:
                    eval_details = None
            results.append({
                "grade_id": g["id"],
                "exam_id": g["exam_id"],
                "score": float(g["score"]),
                "essay_text": g["essay_text"],
                "evaluation_details": eval_details,
                "graded_at": g["graded_at"]
            })
        return results
