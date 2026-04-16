import json
import time
from datetime import datetime
from google.adk.plugins import base_plugin

class AuditLogPlugin(base_plugin.BasePlugin):
    """
    WHAT: Plugin ghi nhật ký kiểm tra (Audit Logging) và Giám sát (Monitoring).
    WHY: Cung cấp bằng chứng số để điều tra các vụ tấn công (Forensics). Nó đóng vai trò 
         theo dõi hiệu năng của toàn bộ pipeline và đưa ra cảnh báo (Alert) nếu Block Rate 
         vượt ngưỡng an toàn (ví dụ > 20%), giúp quản trị viên phát hiện sớm các chiến dịch tấn công.
    """
    
    def __init__(self, log_file="security_audit.json", alert_threshold=0.2):
        super().__init__(name="audit_log")
        self.log_file = log_file
        self.alert_threshold = alert_threshold
        self.logs = []
        self.current_session = {}

    def get_block_rate(self):
        if not self.logs: return 0
        blocks = sum(1 for log in self.logs if log.get("status") == "BLOCKED")
        return blocks / len(self.logs)

    def check_alerts(self):
        rate = self.get_block_rate()
        if rate > self.alert_threshold:
            print(f"!!! SECURITY ALERT: Block Rate is {rate*100:.1f}% (Threshold: {self.alert_threshold*100:.1f}%)")
            return True
        return False

    def _extract_text(self, content):
        if hasattr(content, 'parts'):
            return "".join([p.text for p in content.parts if hasattr(p, 'text')])
        return str(content)

    async def on_user_message_callback(self, *, invocation_context, user_message):
        # Khởi tạo bản ghi session mới
        self.current_session = {
            "timestamp": datetime.now().isoformat(),
            "input": self._extract_text(user_message),
            "start_time": time.time(),
            "status": "PASS",
            "blocked_by": None
        }
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        # Ghi nhận kết quả cuối cùng
        end_time = time.time()
        self.current_session["output"] = self._extract_text(llm_response)
        self.current_session["latency_ms"] = int((end_time - self.current_session["start_time"]) * 1000)
        
        # Nếu output chứa thông báo từ chối, đánh dấu là BLOCKED
        is_blocked = any(kw in self.current_session["output"].lower() 
                         for kw in ["sorry", "cannot", "blocked", "inappropriate", "too many requests"])
        if is_blocked:
            self.current_session["status"] = "BLOCKED"
        
        self.save_log()
        return llm_response

    def save_log(self):
        try:
            self.logs.append(self.current_session)
            
            # Giới hạn bộ nhớ 
            if len(self.logs) > 100:
                self.logs = self.logs[-100:]

            with open(self.log_file, "w") as f:
                json.dump(self.logs, f, indent=2)
                
            # Kiểm tra giám sát và đưa ra Alert nếu cần
            self.check_alerts()
        except Exception as e:
            print(f"Failed to save audit log: {e}")
