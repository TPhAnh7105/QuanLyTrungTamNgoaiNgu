import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.application.dtos.placement_test import (
    PlacementTestSubmitDto,
    PlacementTestResultDto,
    AIEvaluationDetailsDto,
    CourseRecommendationDto
)
from src.domain.exceptions.base import DomainException
from src.domain.entities.student import Student
from src.domain.entities.course import Course
from src.domain.entities.grade import Grade
from src.infrastructure.repositories.exam_repository import ExamRepository
from src.infrastructure.repositories.grade_repository import GradeRepository
from src.application.services.ai_service import AIService

class PlacementTestService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.exam_repo = ExamRepository(session)
        self.grade_repo = GradeRepository(session)
        self.ai_service = AIService()

    async def evaluate_and_grade_student(self, dto: PlacementTestSubmitDto) -> PlacementTestResultDto:
        """
        Xử lý nộp bài thi xếp lớp:
        1. Kiểm tra học viên
        2. Chấm bài tự động qua AI (CEFR A1-C1)
        3. Lưu bài thi & kết quả JSON vào bảng grades
        4. Gợi ý danh sách khóa học phù hợp theo trình độ
        """
        # 1. Kiểm tra học viên
        student_stmt = select(Student).where(Student.id == dto.student_id, Student.is_deleted == 0)
        student = (await self.session.execute(student_stmt)).scalar_one_or_none()
        if not student:
            raise DomainException("Học viên không tồn tại.", status_code=404)

        # 2. Lấy hoặc tạo Exam Placement Test
        exam = await self.exam_repo.get_or_create_placement_exam()

        # 3. Chấm bài bằng AI
        evaluation = await self.ai_service.evaluate_essay(dto.essay_text)

        # 4. Lưu Grade vào Database
        grade = Grade(
            student_id=student.id,
            exam_id=exam.id,
            score=evaluation.band_score,
            essay_text=dto.essay_text,
            ai_evaluation_json=evaluation.model_dump_json(),
            graded_by=None  # AI Tự động chấm
        )
        self.session.add(grade)
        await self.session.flush()
        await self.session.commit()

        # 5. Gợi ý các khóa học phù hợp theo CEFR level
        courses_stmt = (
            select(Course)
            .where(
                Course.level == evaluation.cefr_level,
                Course.is_active == 1,
                Course.is_deleted == 0
            )
            .limit(5)
        )
        recommended_courses_records = (await self.session.execute(courses_stmt)).scalars().all()
        recommended_courses = [
            CourseRecommendationDto(
                id=c.id,
                name=c.name,
                level=c.level,
                fee=float(c.fee)
            )
            for c in recommended_courses_records
        ]

        return PlacementTestResultDto(
            grade_id=grade.id,
            student_id=student.id,
            exam_id=exam.id,
            score=float(grade.score),
            cefr_level=evaluation.cefr_level,
            evaluation_details=evaluation,
            recommended_courses=recommended_courses,
            graded_at=grade.graded_at
        )

    async def get_student_placement_history(self, student_id: int):
        """
        Lấy lịch sử các bài thi xếp lớp của học viên.
        """
        grades = await self.grade_repo.get_by_student_id(student_id)
        results = []
        for g in grades:
            eval_details = None
            if g.ai_evaluation_json:
                try:
                    eval_details = json.loads(g.ai_evaluation_json)
                except Exception:
                    eval_details = None
            results.append({
                "grade_id": g.id,
                "exam_id": g.exam_id,
                "score": float(g.score),
                "essay_text": g.essay_text,
                "evaluation_details": eval_details,
                "graded_at": g.graded_at
            })
        return results
