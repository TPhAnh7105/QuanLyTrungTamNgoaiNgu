# TÀI LIỆU CHI TIẾT CÁC API (API SPECIFICATION & DOCUMENTATION)
## Smart Language Center Management System

---

## 1. THÔNG TIN CHUNG (GENERAL INFORMATION)

- **Base URL:** `http://localhost:8000/api/v1`
- **Swagger UI (Interactive Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc (Alternative Docs):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Chuẩn dữ liệu trao đổi:** `application/json; charset=utf-8`

### Headers tiêu chuẩn:
| Header Name | Bắt buộc | Mô tả |
|---|---|---|
| `Content-Type` | Có (cho POST/PUT) | `application/json` |
| `X-Correlation-ID` | Không | Mã UUID định danh luồng request (nếu client không gửi, server sẽ tự động sinh và trả về trong response header) |

---

## 2. ĐỊNH DẠNG PHẢN HỒI CHUẨN (STANDARD RESPONSE FORMATS)

### 2.1. Phản hồi danh sách phân trang (`PaginatedResponse[T]`)
Tất cả các API lấy danh sách đều trả về cấu trúc phân trang đồng nhất:
```json
{
  "items": [ ... ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### 2.2. Phản hồi lỗi chuẩn RFC 7807 (`Problem Details`)
Khi xảy ra lỗi (Lỗi nghiệp vụ 400, không tìm thấy 404, sai phương thức HTTP 405, lỗi dữ liệu đầu vào 422, hoặc lỗi server 500), API luôn trả về cấu trúc Problem Details chuẩn quốc tế.

#### Ví dụ Lỗi 405 (Method Not Allowed) khi gọi sai HTTP Method:
```json
{
  "type": "https://example.com/probs/method-not-allowed",
  "title": "Method Not Allowed",
  "status": 405,
  "detail": "Method 'POST' is not allowed for endpoint '/'.",
  "instance": "http://localhost:8000/",
  "correlation_id": "d8722b8e-659a-4434-ab15-0acf70259b1e"
}
```

#### Ví dụ Lỗi 404 (Not Found):
```json
{
  "type": "https://example.com/probs/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Course with ID 999 not found",
  "instance": "http://localhost:8000/api/v1/courses/999",
  "correlation_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

---

## 3. DANH SÁCH CHI TIẾT CÁC API ENDPOINTS

---

### A. ROOT & HEALTH CHECK

#### 1. Kiểm tra trạng thái API
- **Endpoint:** `GET /`
- **Mô tả:** Kiểm tra API Server có đang hoạt động hay không.
- **Phản hồi mẫu (`200 OK`):**
```json
{
  "message": "Welcome to the Smart Language Center Management System API"
}
```

---

### B. QUẢN LÝ KHÓA HỌC (COURSES API)
**Prefix:** `/api/v1/courses`

---

#### 1. Tạo mới khóa học
- **Method & Path:** `POST /api/v1/courses/`
- **Status Code:** `201 Created`
- **Quy tắc Validation:**
  - `name`: Chuỗi ký tự từ 3 đến 150 ký tự.
  - `level`: Bắt buộc là một trong các cấp độ: `"A1"`, `"A2"`, `"B1"`, `"B2"`, `"C1"`, `"C2"`.
  - `fee`: Số tiền học phí, phải lớn hơn 0 (> 0).
  - `max_capacity`: Sĩ số tối đa của lớp, phải lớn hơn 0 (> 0).
  - `is_active`: `1` (Đang mở) hoặc `0` (Đang đóng), mặc định là `1`.
- **Request Body mẫu:**
```json
{
  "name": "IELTS Intensive Masterclass",
  "level": "B2",
  "fee": 7500000.0,
  "max_capacity": 25,
  "is_active": 1
}
```
- **Response mẫu (`201 Created`):**
```json
{
  "id": 1,
  "name": "IELTS Intensive Masterclass",
  "level": "B2",
  "fee": 7500000.0,
  "max_capacity": 25,
  "is_active": 1,
  "created_at": "2026-09-21T08:00:00Z"
}
```

---

#### 2. Lấy danh sách khóa học (Phân trang, Lọc & Sắp xếp)
- **Method & Path:** `GET /api/v1/courses/`
- **Status Code:** `200 OK`
- **Query Parameters:**
  | Tên Param | Kiểu | Mặc định | Mô tả |
  |---|---|---|---|
  | `page` | `int` | `1` | Số trang (tối thiểu 1) |
  | `size` | `int` | `20` | Số lượng bản ghi / trang (1 - 100) |
  | `sort_by` | `string` | `null` | Tên trường muốn sắp xếp (`id`, `name`, `fee`, `created_at`...) |
  | `sort_desc` | `bool` | `false` | `true` nếu muốn sắp xếp giảm dần, `false` nếu tăng dần |
  | `name` | `string` | `null` | Lọc theo tên khóa học (tìm kiếm tương đối / chứa chuỗi) |
  | `level` | `string` | `null` | Lọc chính xác theo cấp độ (`A1`, `B1`, `B2`...) |
  | `is_active` | `int` | `null` | Lọc theo trạng thái mở (`1` hoặc `0`) |

- **Ví dụ gọi URL:** `GET /api/v1/courses/?level=B2&page=1&size=10&sort_by=fee&sort_desc=true`
- **Response mẫu (`200 OK`):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "IELTS Intensive Masterclass",
      "level": "B2",
      "fee": 7500000.0,
      "max_capacity": 25,
      "is_active": 1,
      "created_at": "2026-09-21T08:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

---

#### 3. Lấy chi tiết một khóa học theo ID
- **Method & Path:** `GET /api/v1/courses/{id}`
- **Path Parameter:** `id` (int) - ID khóa học cần tra cứu.
- **Response mẫu (`200 OK`):**
```json
{
  "id": 1,
  "name": "IELTS Intensive Masterclass",
  "level": "B2",
  "fee": 7500000.0,
  "max_capacity": 25,
  "is_active": 1,
  "created_at": "2026-09-21T08:00:00Z"
}
```
- **Response khi không tìm thấy hoặc đã bị xóa mềm (`404 Not Found`):**
```json
{
  "type": "https://example.com/probs/domain_error",
  "title": "DOMAIN_ERROR",
  "status": 404,
  "detail": "Course with ID 999 not found",
  "instance": "http://localhost:8000/api/v1/courses/999",
  "correlation_id": "abc-123"
}
```

---

#### 4. Cập nhật thông tin khóa học
- **Method & Path:** `PUT /api/v1/courses/{id}`
- **Status Code:** `200 OK`
- **Mô tả:** Cho phép cập nhật từng phần (Partial update), chỉ cần gửi các trường muốn thay đổi.
- **Request Body mẫu:**
```json
{
  "fee": 8000000.0,
  "max_capacity": 30
}
```
- **Response mẫu (`200 OK`):** Trả về đối tượng sau khi đã cập nhật thành công.

---

#### 5. Xóa mềm khóa học (Soft Delete)
- **Method & Path:** `DELETE /api/v1/courses/{id}`
- **Status Code:** `204 No Content`
- **Mô tả:** Đặt trường `is_deleted = 1` trong database. Bản ghi vẫn được lưu trữ lịch sử nhưng sẽ bị ẩn hoàn toàn khỏi tất cả các API GET sau đó.
- **Response:** Không có Body trả về (`204 No Content`).

---

### C. QUẢN LÝ HỌC VIÊN (STUDENTS API)
**Prefix:** `/api/v1/students`

---

#### 1. Thêm mới học viên
- **Method & Path:** `POST /api/v1/students/`
- **Status Code:** `201 Created`
- **Quy tắc Validation & AI Features:**
  - `user_id`: Khóa ngoại trỏ tới tài khoản trong bảng `users` (> 0).
  - `full_name`: Tên học viên (2 - 100 ký tự).
  - `date_of_birth`: Ngày sinh (ISO DateTime format, ví dụ: `"2005-05-20T00:00:00Z"`).
  - `phone`: Số điện thoại (tối đa 20 ký tự, có thể `null`).
  - `weekly_study_hours`: Số giờ tự học mỗi tuần (>= 0).
  - `absence_rate`: Tỷ lệ nghỉ học (từ `0.0` đến `1.0`).
  - `motivation_score`: Điểm đánh giá động lực học tập (từ `0` đến `10`).
  - `parental_support`: Mức độ hỗ trợ từ phụ huynh (`"Low"`, `"Medium"`, `"High"`).
- **Request Body mẫu:**
```json
{
  "user_id": 1,
  "full_name": "Nguyễn Văn An",
  "date_of_birth": "2005-08-15T00:00:00Z",
  "phone": "0912345678",
  "weekly_study_hours": 12,
  "absence_rate": 0.04,
  "motivation_score": 9,
  "parental_support": "High"
}
```
- **Response mẫu (`201 Created`):**
```json
{
  "id": 1,
  "user_id": 1,
  "full_name": "Nguyễn Văn An",
  "date_of_birth": "2005-08-15T00:00:00Z",
  "phone": "0912345678",
  "weekly_study_hours": 12,
  "absence_rate": 0.04,
  "motivation_score": 9,
  "parental_support": "High",
  "created_at": "2026-09-21T08:05:00Z"
}
```

---

#### 2. Lấy danh sách học viên (Phân trang, Lọc & Sắp xếp)
- **Method & Path:** `GET /api/v1/students/`
- **Status Code:** `200 OK`
- **Query Parameters:**
  - `page`, `size`, `sort_by`, `sort_desc`
  - `full_name`: Tìm kiếm theo tên học viên (chuỗi tương đối).
  - `phone`: Lọc theo số điện thoại.
  - `parental_support`: Lọc theo mức hỗ trợ (`"Low"`, `"Medium"`, `"High"`).
- **Ví dụ gọi URL:** `GET /api/v1/students/?parental_support=High&page=1&size=20`

---

#### 3. Lấy chi tiết học viên theo ID
- **Method & Path:** `GET /api/v1/students/{id}`
- **Status Code:** `200 OK` hoặc `404 Not Found`

---

#### 4. Cập nhật thông tin học viên
- **Method & Path:** `PUT /api/v1/students/{id}`
- **Request Body mẫu:**
```json
{
  "weekly_study_hours": 15,
  "absence_rate": 0.02,
  "motivation_score": 10
}
```

---

#### 5. Xóa mềm học viên
- **Method & Path:** `DELETE /api/v1/students/{id}`
- **Status Code:** `204 No Content`

---

### D. QUẢN LÝ GIÁO VIÊN (TEACHERS API)
**Prefix:** `/api/v1/teachers`

---

#### 1. Thêm mới giáo viên
- **Method & Path:** `POST /api/v1/teachers/`
- **Status Code:** `201 Created`
- **Quy tắc Validation:**
  - `user_id`: Khóa ngoại tài khoản `users` (> 0).
  - `full_name`: Họ tên giáo viên (2 - 100 ký tự).
  - `specialization`: Bắt buộc là một trong các chuyên môn: `"TOEFL"`, `"IELTS"`, `"TOEIC"`, `"Communicative English"`.
  - `bio`: Tiểu sử / kinh nghiệm (tối đa 1000 ký tự, có thể `null`).
- **Request Body mẫu:**
```json
{
  "user_id": 2,
  "full_name": "ThS. Trần Thị Mai",
  "specialization": "IELTS",
  "bio": "8.5 IELTS Overall, 8 năm kinh nghiệm luyện thi chuyên sâu"
}
```
- **Response mẫu (`201 Created`):**
```json
{
  "id": 1,
  "user_id": 2,
  "full_name": "ThS. Trần Thị Mai",
  "specialization": "IELTS",
  "bio": "8.5 IELTS Overall, 8 năm kinh nghiệm luyện thi chuyên sâu",
  "created_at": "2026-09-21T08:10:00Z"
}
```

---

#### 2. Lấy danh sách giáo viên (Phân trang, Lọc & Sắp xếp)
- **Method & Path:** `GET /api/v1/teachers/`
- **Query Parameters:** `page`, `size`, `sort_by`, `sort_desc`, `full_name`, `specialization`.
- **Ví dụ gọi URL:** `GET /api/v1/teachers/?specialization=IELTS`

---

#### 3. Lấy chi tiết giáo viên theo ID
- **Method & Path:** `GET /api/v1/teachers/{id}`
- **Status Code:** `200 OK` hoặc `404 Not Found`

---

#### 4. Cập nhật thông tin giáo viên
- **Method & Path:** `PUT /api/v1/teachers/{id}`
- **Request Body mẫu:**
```json
{
  "bio": "9.0 IELTS Overall, Giảng viên chính tại trung tâm"
}
```

---

#### 5. Xóa mềm giáo viên
- **Method & Path:** `DELETE /api/v1/teachers/{id}`
- **Status Code:** `204 No Content`

---

## 4. HƯỚNG DẪN TEST NHANH VỚI CURL / POSTMAN

### 1. Tạo Khóa học (cURL):
```bash
curl -X POST "http://localhost:8000/api/v1/courses/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "General English",
       "level": "A2",
       "fee": 3500000,
       "max_capacity": 20,
       "is_active": 1
     }'
```

### 2. Lấy danh sách Khóa học với Phân trang & Lọc (cURL):
```bash
curl -X GET "http://localhost:8000/api/v1/courses/?level=A2&page=1&size=5"
```

### 3. Xóa mềm Khóa học (cURL):
```bash
curl -X DELETE "http://localhost:8000/api/v1/courses/1"
```
