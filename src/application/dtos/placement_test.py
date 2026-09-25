from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PlacementTestSubmitDto(BaseModel):
    student_id: int = Field(..., description="ID của học viên tham gia thi")
    essay_text: str = Field(..., min_length=20, description="Nội dung bài luận (tối thiểu 20 ký tự)")

class CourseRecommendationDto(BaseModel):
    id: int
    name: str
    level: str
    fee: float

class AIEvaluationDetailsDto(BaseModel):
    cefr_level: str = Field(..., description="Cấp độ CEFR: A1, A2, B1, B2, C1, C2")
    band_score: float = Field(..., description="Điểm quy đổi thang 10")
    grammar_analysis: str = Field(..., description="Đánh giá ngữ pháp & cấu trúc câu")
    vocabulary_analysis: str = Field(..., description="Đánh giá độ phong phú từ vựng")
    coherence_analysis: str = Field(..., description="Đánh giá tính mạch lạc & liên kết")
    strengths: List[str] = Field(default_factory=list, description="Điểm mạnh của bài viết")
    weaknesses: List[str] = Field(default_factory=list, description="Điểm cần khắc phục")
    detailed_feedback: str = Field(..., description="Nhận xét tổng quan")

class PlacementTestResultDto(BaseModel):
    grade_id: int
    student_id: int
    exam_id: int
    score: float
    cefr_level: str
    evaluation_details: AIEvaluationDetailsDto
    recommended_courses: List[CourseRecommendationDto]
    graded_at: datetime
