# TÀI LIỆU KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)
## Smart Language Center Management System

---

## 1. TỔNG QUAN HỆ THỐNG & ĐỊNH HƯỚNG KIẾN TRÚC

Hệ thống **Smart Language Center Management System** được xây dựng trên nền tảng **Python FastAPI** và tuân thủ chặt chẽ mô hình **Kiến trúc củ hành 4 tầng (4-Layer Onion / Clean Architecture)** kết hợp các nguyên lý **Domain-Driven Design (DDD)**.

### Mục tiêu thiết kế:
1. **Tính độc lập của Domain (Framework Independence)**: Nghiệp vụ cốt lõi không bị phụ thuộc vào Web Framework (FastAPI), ORM/Database hay các thư viện bên thứ ba.
2. **Hiệu năng cao & Bất đồng bộ (Async First)**: Sử dụng cơ chế async/await xuyên suốt từ tầng Web API xuống tầng truy cập CSDL qua `SQLAlchemy Core (Async)` và driver `aiomysql` (hoặc `asyncmy`).
3. **Tính toàn vẹn & Kiểm soát dữ liệu**: 
   - Kiểm tra dữ liệu đầu vào chặt chẽ qua **Pydantic v2**.
   - Bảo toàn dữ liệu lịch sử với cơ chế **Xóa mềm (Soft-Delete)**.
   - Chuẩn hóa thông điệp lỗi toàn hệ thống theo tiêu chuẩn quốc tế **RFC 7807 (Problem Details)**.
   - Định danh luồng xử lý với **Correlation ID Tracing**.

---

## 2. SƠ ĐỒ KIẾN TRÚC 4 TẦNG (CLEAN ARCHITECTURE)

Mô hình luồng phụ thuộc tuân thủ nguyên tắc **Dependency Inversion**: Tầng bên ngoài phụ thuộc vào tầng bên trong, tầng bên trong hoàn toàn không biết đến tầng bên ngoài.

```
+-----------------------------------------------------------------------+
|                             API LAYER                                 |
|   - Controllers / Routers (courses, students, teachers)               |
|   - Middlewares (Error Handler RFC 7807, Correlation ID, Logger)      |
|   - Dependencies & Lifecycle (main.py, dependencies.py)               |
+-----------------------------------+-----------------------------------+
                                    | phụ thuộc vào
                                    v
+-----------------------------------------------------------------------+
|                         APPLICATION LAYER                             |
|   - Data Transfer Objects (DTOs) (Validation, Request/Response)       |
|   - Application Services (Orchestration, Use Cases)                  |
|   - Interfaces (Contracts, Repository Abstractions)                   |
+-----------------------------------+-----------------------------------+
                                    | phụ thuộc vào
                                    v
+-----------------------------------------------------------------------+
|                           DOMAIN LAYER                                |
|   - Entities (Course, Student, Teacher, User)                         |
|   - Domain Exceptions (DomainException, Business Rules)               |
+-----------------------------------+-----------------------------------+
                                    ^
                                    | triển khai / kế thừa
+-----------------------------------+-----------------------------------+
|                      INFRASTRUCTURE LAYER                             |
|   - Database Engine & Session Management (SQLAlchemy Core, aiosqlite) |
|   - Repositories Implementation (BaseRepository, CourseRepository...) |
|   - Cache, ML Models, External Services (Redis, Celery, AI)           |
+-----------------------------------------------------------------------+
```

---

## 3. CHI TIẾT TỔNG THỂ CÁC TẦNG & TÁC DỤNG TỪNG THÀNH PHẦN

```
src/
├── api/                           # [TẦNG 1] API & Presentation Layer
│   ├── controllers/               # Điều hướng HTTP Request, gọi tầng Repo/Service
│   │   ├── courses.py             # Router quản lý danh mục Khóa học
│   │   ├── students.py            # Router quản lý danh mục Học viên
│   │   └── teachers.py            # Router quản lý danh mục Giáo viên
│   ├── middlewares/               # Middlewares xử lý trung gian
│   │   └── error_handler.py       # Global Exception Handler chuyển đổi lỗi sang RFC 7807
│   └── dependencies.py            # FastAPI Dependencies (Auth, Sessions, Permissions)
│
├── application/                   # [TẦNG 2] Application & Use Cases Layer
│   ├── dtos/                      # Pydantic Schemas validate dữ liệu đầu vào / đầu ra
│   │   ├── course.py              # DTO tạo mới, cập nhật và phản hồi Course
│   │   ├── student.py             # DTO tạo mới, cập nhật và phản hồi Student
│   │   ├── teacher.py             # DTO tạo mới, cập nhật và phản hồi Teacher
│   │   └── pagination.py          # DTO chung cho phân trang (PaginatedResponse, PaginationParams)
│   ├── interfaces/                # Định nghĩa giao diện mẫu (Interfaces/Protocols)
│   └── services/                  # Nghiệp vụ ứng dụng điều phối (Application Services)
│
├── domain/                        # [TẦNG 3] Domain Core (Trung tâm nghiệp vụ)
│   ├── entities/                  # Thực thể CSDL & nghiệp vụ lõi
│   │   ├── course.py              # Entity Khóa học
│   │   ├── student.py             # Entity Học viên (kèm tham số AI: study_hours, absence_rate...)
│   │   ├── teacher.py             # Entity Giáo viên (specialization, bio...)
│   │   └── user.py                # Entity Tài khoản người dùng (Auth/RBAC)
│   └── exceptions/                # Ngoại lệ nghiệp vụ
│       └── base.py                # Lớp cơ sở DomainException
│
├── infrastructure/                # [TẦNG 4] Infrastructure Layer
│   ├── database/                  # Kết nối và cấu hình cơ sở dữ liệu
│   │   └── connection.py          # Async Engine, AsyncSessionLocal, get_db_session dependency
│   ├── repositories/              # Triển khai truy xuất CSDL bằng SQLAlchemy Async
│   │   ├── base_repository.py     # Generic Base Repository hỗ trợ CRUD, Soft-delete, Pagination
│   │   ├── course_repository.py   # Repository riêng cho Khóa học
│   │   ├── student_repository.py  # Repository riêng cho Học viên
│   │   └── teacher_repository.py  # Repository riêng cho Giáo viên
│   ├── cache/                     # Tích hợp Redis Caching (sắp triển khai)
│   ├── ml_models/                 # Tích hợp mô hình AI/ML dự đoán Dropout (sắp triển khai)
│   └── services/                  # Tích hợp dịch vụ ngoài (AI Gemini, Email, PDF...)
│
└── main.py                        # Entry point: Khởi tạo FastAPI App, Lifespan, Middleware, Routers
```

---

## 4. PHÂN TÍCH CHUYÊN SÂU TỪNG THÀNH PHẦN

### 4.1. Domain Layer (`src/domain`)
- **Entities (`course.py`, `student.py`, `teacher.py`, `user.py`)**:
  - Định nghĩa cấu trúc dữ liệu bảng và thuộc tính nghiệp vụ.
  - Mỗi entity kế thừa `Base` từ SQLAlchemy, đồng thời được tích hợp sẵn trường `is_deleted` (mặc định bằng `0`) để hỗ trợ xóa mềm dữ liệu.
  - Riêng entity `Student` được thiết kế tương thích với các bài toán máy học AI (UCI Student Performance) như `weekly_study_hours`, `absence_rate`, `motivation_score`, `parental_support`.
- **Domain Exceptions (`exceptions/base.py`)**:
  - `DomainException`: Định nghĩa lỗi nghiệp vụ độc lập có chứa `message`, `error_code` và `status_code` tương ứng.

### 4.2. Application Layer (`src/application`)
- **Pydantic v2 DTOs (`dtos/`)**:
  - Thực hiện ràng buộc dữ liệu đầu vào bằng regex và validator (ví dụ: `level` của Course bắt buộc thuộc `A1`..`C2`; `specialization` của Teacher thuộc các chuyên môn hợp lệ).
  - Tách biệt rõ ràng: `Create...Dto` (chứa dữ liệu bắt buộc khi tạo), `Update...Dto` (các trường `Optional` cho phép cập nhật từng phần), và `...ResponseDto` (dữ liệu an toàn trả về cho client).
- **Pagination DTO (`dtos/pagination.py`)**:
  - Chuẩn hóa định dạng phân trang với Generic DTO: `PaginatedResponse[T]` gồm `items`, `total`, `page`, `size`, `pages`.

### 4.3. Infrastructure Layer (`src/infrastructure`)
- **Database Connection (`database/connection.py`)**:
  - Sử dụng `create_async_engine` kết nối MySQL bất đồng bộ với driver `aiomysql` (`mysql+aiomysql://root:123456@localhost:3306/WebAPI?charset=utf8mb4`).
  - Cấu hình Connection Pool chuyên dụng cho môi trường tải cao: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`.
  - Cung cấp dependency `get_db_session` quản lý vòng đời Session của từng request độc lập, tự động rollback khi gặp lỗi ngoại lệ.
- **Generic Base Repository (`repositories/base_repository.py`)**:
  - Áp dụng mẫu thiết kế **Generic Repository Pattern** (`BaseRepository[ModelType]`).
  - **Tự động áp dụng Soft-Delete Filter**: Hàm `_soft_delete_filter()` tự động bổ sung điều kiện `is_deleted == 0` cho mọi câu lệnh truy vấn `select` và `get_by_id`.
  - **Phương thức `get_paginated`**: Hỗ trợ phân trang động, tính tổng số dòng (`func.count()`), tìm kiếm `ilike` cho chuỗi ký tự, tìm kiếm chính xác cho số/enum và sắp xếp tăng/giảm (`asc`/`desc`).

### 4.4. API & Presentation Layer (`src/api`)
- **Controllers (`controllers/`)**:
  - Tiếp nhận HTTP Request, inject `AsyncSession` qua `Depends(get_db_session)`.
  - Gọi Repository để thực thi nghiệp vụ và trả về DTO tương ứng.
- **Global Error Handler (`middlewares/error_handler.py`)**:
  - Bắt toàn bộ ngoại lệ chưa được xử lý và ngoại lệ nghiệp vụ `DomainException`.
  - Chuyển đổi phản hồi thành chuẩn **RFC 7807 Problem Details** (chứa `type`, `title`, `status`, `detail`, `instance`, `correlation_id`).
- **Correlation ID & Logging Middleware (`main.py`)**:
  - Tự động trích xuất hoặc sinh mới UUID `X-Correlation-ID` cho mỗi request.
  - Ghi log thời gian thực thi (Process Time) và mã trạng thái HTTP thông qua thư viện `Loguru`.

---

## 5. DESIGN PATTERNS & QUY CHUẨN KỸ THUẬT NỔI BẬT

| STT | Quy chuẩn / Pattern | Nơi áp dụng | Mục đích / Giá trị mang lại |
|---|---|---|---|
| 1 | **Onion / Clean Architecture** | Toàn bộ `src/` | Phân tách trách nhiệm tuyệt đối, dễ bảo trì, dễ viết unit test |
| 2 | **Generic Repository Pattern** | `infrastructure/repositories/` | Tái sử dụng 90% logic CRUD cơ bản, trừu tượng hóa tầng CSDL |
| 3 | **Soft-Delete Pattern** | `BaseRepository`, Entities | Ngăn ngừa việc mất dữ liệu vật lý khi người dùng xóa bản ghi |
| 4 | **RFC 7807 Problem Details** | `api/middlewares/error_handler.py` | Chuẩn hóa định dạng lỗi JSON theo tiêu chuẩn quốc tế cho Client/Frontend |
| 5 | **Correlation ID Tracing** | `main.py` Middleware | Định danh từng request để dễ dàng truy vết và debug hệ thống |
| 6 | **FastAPI Lifespan Context** | `main.py` | Quản lý kết nối CSDL và tạo bảng tự động chuẩn theo FastAPI hiện đại |
| 7 | **Strict Validation (Pydantic v2)** | `application/dtos/` | Ngăn chặn dữ liệu rác, SQL Injection và sai kiểu dữ liệu ngay từ cổng vào API |
