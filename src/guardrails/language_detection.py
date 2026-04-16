from google.adk.plugins import base_plugin
from google.genai import types

class LanguageDetectionPlugin(base_plugin.BasePlugin):
    """
    WHAT: Plugin phát hiện và giới hạn ngôn ngữ (Language Detection).
    WHY: Đây là lớp bảo mật Layer 6 (Bonus). Nó đảm bảo hệ thống chỉ tương tác bằng 
         tiếng Anh và tiếng Việt. Việc giới hạn ngôn ngữ giúp ngăn chặn các kỹ thuật 
         'Language-based Jailbreaking' - nơi kẻ tấn công dùng các ngôn ngữ ít phổ biến 
         để đánh lừa bộ lọc từ khóa regex vốn chỉ tập trung vào Anh/Việt.
    """
    
    def __init__(self, allowed_languages=["vi", "en"]):
        super().__init__(name="language_detection")
        self.allowed_languages = allowed_languages

    def _extract_text(self, content):
        return "".join([p.text for p in content.parts if hasattr(p, 'text')])

    async def on_user_message_callback(self, *, invocation_context, user_message):
        text = self._extract_text(user_message)
        
        # Sử dụng một logic đơn giản để detect tiếng Việt (qua các nguyên âm có dấu) 
        # hoặc gán mặc định nếu là tiếng Anh cơ bản.
        # Trong thực tế sẽ dùng thư viện 'langdetect', ở đây ta mô phỏng logic block.
        
        vietnamese_chars = "àáảãạăằắẳẵặcằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữự"
        is_vietnamese = any(char in text.lower() for char in vietnamese_chars)
        is_english = all(ord(char) < 128 for char in text)
        
        if not (is_vietnamese or is_english):
            return types.Content(
                role="model",
                parts=[types.Part.from_text(
                    text="Unsupported language detected. Please use English or Vietnamese only for security reasons."
                )]
            )
        return None
