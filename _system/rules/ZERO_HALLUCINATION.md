# 🛡️ Sắc lệnh Chống Ảo giác (Zero-Hallucination Mandate)

## Nguyên tắc Tối thượng cho Hệ thống RAG
Hệ thống HaiVo LeadsMap là một **Closed-Domain RAG** (chỉ giới hạn trong kho dữ liệu được cung cấp). Lấy cảm hứng từ `llm-wiki`, độ tin cậy của dữ liệu là yếu tố sống còn.

### 1. Strict Grounding (Bám sát Dữ liệu)
- **Prompt System:** LLM (Gemini/Claude) BẮT BUỘC phải được cấu hình với prompt: *"Bạn là trợ lý dữ liệu BĐS. CHỈ trả lời dựa trên context được cung cấp. Nếu context không chứa câu trả lời, hãy nói: 'Tôi không có thông tin này trong cơ sở dữ liệu'. TUYỆT ĐỐI KHÔNG tự bịa đặt (hallucinate) hoặc sử dụng kiến thức bên ngoài."*

### 2. Source Citation (Trích dẫn Nguồn gốc)
- Mọi câu trả lời từ Chatbot phải kèm theo link trỏ về file Markdown gốc hoặc file PDF/Ảnh đầu vào (vd: `[Source: 2026 - prj-EatonPark.md]`).

### 3. Temperature Control (Kiểm soát Sáng tạo)
- Khi gọi API của Gemini hoặc LLM khác cho phần RAG, thông số `temperature` BẮT BUỘC phải set ở mức rất thấp (vd: `0.0` đến `0.2`) để tối đa hóa tính chính xác và loại bỏ sự "sáng tạo" không cần thiết.

## Yêu cầu cho Kỹ sư Claude:
Khi thiết lập module RAG bằng LlamaIndex, hãy đảm bảo tích hợp bộ lọc **Confidence Score**. Nếu điểm số trích xuất quá thấp, hệ thống phải báo cáo lại cho Admin thay vì cố gắng đưa ra câu trả lời gượng ép.
