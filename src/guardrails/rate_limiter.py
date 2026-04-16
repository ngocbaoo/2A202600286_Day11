from collections import defaultdict, deque
import time
from google.adk.plugins import base_plugin
from google.genai import types

class RateLimitPlugin(base_plugin.BasePlugin):
    """
    WHAT: Plugin giới hạn tần suất yêu cầu (Rate Limiting) sử dụng thuật toán Sliding Window.
    WHY: Đây là lớp phòng thủ đầu tiên (Layer 1). Nó chặn các cuộc tấn công DoS hoặc brute-force
         trước khi chúng tiêu tốn tài nguyên của các lớp kiểm duyệt LLM đắt đỏ phía sau. 
         Lớp này bắt các lỗi mà các lớp nội dung (Input/Output) không thể thấy: Tần suất yêu cầu bất thường.
    """
    
    def __init__(self, max_requests=5, window_seconds=60):
        super().__init__(name="rate_limiter")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_windows = defaultdict(deque)

    async def on_user_message_callback(self, *, invocation_context, user_message):
        # Xác định user_id (mặc định là 'anonymous' nếu không có context)
        user_id = "default_user"
        if invocation_context and hasattr(invocation_context, 'user_id'):
            user_id = invocation_context.user_id
            
        now = time.time()
        window = self.user_windows[user_id]

        # Xóa các timestamp đã hết hạn (nằm ngoài cửa sổ window_seconds)
        while window and window[0] < now - self.window_seconds:
            window.popleft()

        # Kiểm tra nếu vượt quá giới hạn
        if len(window) >= self.max_requests:
            wait_time = int(window[0] + self.window_seconds - now)
            return types.Content(
                role="model",
                parts=[types.Part.from_text(
                    text=f"Too many requests. Please wait {wait_time} seconds before trying again."
                )]
            )

        # Ghi nhận timestamp mới
        window.append(now)
        return None
