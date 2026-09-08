
-- 1. Table Users (Xác thực và Phân quyền)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Teacher', 'Student')),
    refresh_token VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table Teachers (Giáo viên)
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT UNIQUE NOT NULL,
    full_name NVARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL, -- TOEFL, IELTS, TOEIC, Communicative English
    bio TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Table Students (Học viên)
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT UNIQUE NOT NULL,
    full_name NVARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone VARCHAR(20) NULL,
    
    -- AI Predictive Features (UCI Student Performance & xAPI-Edu-Data Mapping)
    weekly_study_hours INT DEFAULT 5, -- Giờ tự học/tuần [0 - 30]
    absence_rate DECIMAL(5,2) DEFAULT 0.00, -- Tỷ lệ nghỉ học [0.00 - 100.00]%
    motivation_score INT DEFAULT 7, -- Điểm khảo sát động lực [1 - 10]
    parental_support VARCHAR(10) DEFAULT 'Medium' CHECK (parental_support IN ('Low', 'Medium', 'High')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Table Courses (Khóa học)
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name NVARCHAR(150) NOT NULL,
    level VARCHAR(10) NOT NULL CHECK (level IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    fee DECIMAL(18,2) NOT NULL,
    max_capacity INT DEFAULT 30,
    is_active INT DEFAULT 1, -- 1: Active, 0: Inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Table Enrollments (Ghi danh)
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrollment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Completed', 'Dropped')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(student_id, course_id)
);

-- 6. Table Exams (Kỳ thi/Kiểm tra)
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INT NULL, -- Nullable cho kỳ thi đầu vào (Placement Test)
    name NVARCHAR(100) NOT NULL,
    exam_type VARCHAR(20) NOT NULL CHECK (exam_type IN ('Placement', 'Midterm', 'Final')),
    max_score DECIMAL(5,2) DEFAULT 10.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
);

-- 7. Table Grades (Điểm số & Bài viết thi AI)
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INT NOT NULL,
    exam_id INT NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    
    -- AI NLP Features (CEFR Essay Auto-grading)
    essay_text TEXT NULL, -- Bài luận học viên nộp cho AI chấm điểm
    ai_evaluation_json TEXT NULL, -- Dữ liệu JSON đánh giá chi tiết của AI
    
    graded_by INT NOT NULL, -- Giáo viên chấm
    graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (graded_by) REFERENCES teachers(id) ON DELETE RESTRICT
);

-- 8. Table Invoices (Học phí & Hóa đơn)
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INT NOT NULL,
    enrollment_id INT NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'Pending' CHECK (payment_status IN ('Pending', 'Paid', 'Overdue')),
    due_date DATE NOT NULL,
    payment_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
);
