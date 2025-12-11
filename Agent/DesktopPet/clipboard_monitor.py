"""
Clipboard Monitor Module
클립보드의 코드를 자동 감지하고 분석하는 모듈
"""

import re
import time
from typing import Optional, Callable
from PyQt6.QtCore import QThread, pyqtSignal
import pyperclip


class ClipboardMonitor(QThread):
    """클립보드 모니터링 스레드"""
    
    # 시그널 정의
    code_detected = pyqtSignal(str, str)  # (code, language)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.last_clipboard = ""
        self.check_interval = 1.0  # 1초마다 체크
        
        # 코드 감지 설정
        self.min_code_length = 20  # 최소 코드 길이
        self.enabled = False
    
    def run(self):
        """모니터링 스레드 실행"""
        self.running = True
        
        while self.running:
            if self.enabled:
                try:
                    current_clipboard = pyperclip.paste()
                    
                    # 클립보드가 변경되었고, 이전과 다르면
                    if current_clipboard != self.last_clipboard:
                        self.last_clipboard = current_clipboard
                        
                        # 코드인지 감지
                        if self._is_code(current_clipboard):
                            language = self._detect_language(current_clipboard)
                            self.code_detected.emit(current_clipboard, language)
                
                except Exception as e:
                    print(f"Clipboard monitoring error: {e}")
            
            time.sleep(self.check_interval)
    
    def stop(self):
        """모니터링 중지"""
        self.running = False
        self.wait()
    
    def enable(self):
        """모니터링 활성화"""
        self.enabled = True
    
    def disable(self):
        """모니터링 비활성화"""
        self.enabled = False
    
    def _is_code(self, text: str) -> bool:
        """
        텍스트가 코드인지 판단
        
        Args:
            text: 검사할 텍스트
        
        Returns:
            코드 여부
        """
        if not text or len(text) < self.min_code_length:
            return False
        
        # 코드 패턴 체크
        code_indicators = [
            r'def\s+\w+\s*\(',  # Python 함수
            r'function\s+\w+\s*\(',  # JavaScript 함수
            r'class\s+\w+',  # 클래스
            r'import\s+\w+',  # Import 문
            r'from\s+\w+\s+import',  # Python import
            r'const\s+\w+\s*=',  # JavaScript const
            r'let\s+\w+\s*=',  # JavaScript let
            r'var\s+\w+\s*=',  # JavaScript var
            r'public\s+\w+',  # Java/C# public
            r'private\s+\w+',  # Java/C# private
            r'if\s*\(',  # if 문
            r'for\s*\(',  # for 문
            r'while\s*\(',  # while 문
            r'=>',  # Arrow function
            r'\{[\s\S]*\}',  # 중괄호 블록
            r'return\s+',  # return 문
        ]
        
        # 하나라도 매칭되면 코드로 판단
        for pattern in code_indicators:
            if re.search(pattern, text):
                return True
        
        # 세미콜론이나 중괄호가 많으면 코드일 가능성
        semicolons = text.count(';')
        braces = text.count('{') + text.count('}')
        
        if semicolons > 2 or braces > 2:
            return True
        
        return False
    
    def _detect_language(self, code: str) -> str:
        """
        코드 언어 감지
        
        Args:
            code: 코드 텍스트
        
        Returns:
            감지된 언어
        """
        # Python 패턴
        python_patterns = [
            r'def\s+\w+\s*\(',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'elif\s*:',
            r'__init__',
            r'self\.',
        ]
        
        # JavaScript 패턴
        js_patterns = [
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'=>',
            r'console\.log',
            r'document\.',
        ]
        
        # Java 패턴
        java_patterns = [
            r'public\s+class',
            r'public\s+static\s+void',
            r'System\.out\.println',
            r'@Override',
        ]
        
        # C++ 패턴
        cpp_patterns = [
            r'#include\s*<',
            r'std::',
            r'cout\s*<<',
            r'namespace\s+',
        ]
        
        # 각 언어별 점수 계산
        scores = {
            'Python': sum(1 for p in python_patterns if re.search(p, code)),
            'JavaScript': sum(1 for p in js_patterns if re.search(p, code)),
            'Java': sum(1 for p in java_patterns if re.search(p, code)),
            'C++': sum(1 for p in cpp_patterns if re.search(p, code)),
        }
        
        # 가장 높은 점수의 언어 반환
        max_score = max(scores.values())
        if max_score > 0:
            for lang, score in scores.items():
                if score == max_score:
                    return lang
        
        return "Unknown"


class ClipboardAnalyzer:
    """클립보드 코드 분석기"""
    
    def __init__(self, ai_reviewer=None):
        """
        Initialize Clipboard Analyzer
        
        Args:
            ai_reviewer: AI Code Reviewer 인스턴스 (선택사항)
        """
        self.ai_reviewer = ai_reviewer
    
    def quick_analyze(self, code: str, language: str = "python") -> dict:
        """
        코드 빠른 분석
        
        Args:
            code: 분석할 코드
            language: 코드 언어
        
        Returns:
            분석 결과 dict
        """
        result = {
            'length': len(code),
            'lines': code.count('\n') + 1,
            'language': language,
            'has_functions': self._has_functions(code),
            'has_classes': self._has_classes(code),
            'complexity': self._estimate_complexity(code),
        }
        
        # AI 리뷰어가 있으면 간단한 피드백 추가
        if self.ai_reviewer:
            try:
                feedback = self.ai_reviewer.quick_check(code, language.lower())
                result['ai_feedback'] = feedback
            except Exception as e:
                result['ai_feedback'] = f"AI 분석 실패: {str(e)}"
        
        return result
    
    def _has_functions(self, code: str) -> bool:
        """함수 정의 포함 여부"""
        patterns = [r'def\s+\w+', r'function\s+\w+', r'public\s+\w+\s+\w+\s*\(']
        return any(re.search(p, code) for p in patterns)
    
    def _has_classes(self, code: str) -> bool:
        """클래스 정의 포함 여부"""
        return bool(re.search(r'class\s+\w+', code))
    
    def _estimate_complexity(self, code: str) -> str:
        """코드 복잡도 추정"""
        lines = code.count('\n') + 1
        
        # 제어 구조 개수
        control_structures = (
            code.count('if ') + 
            code.count('for ') + 
            code.count('while ') +
            code.count('switch ')
        )
        
        # 복잡도 판단
        if lines < 10 and control_structures < 2:
            return "낮음"
        elif lines < 50 and control_structures < 5:
            return "보통"
        else:
            return "높음"
    
    def format_analysis_result(self, result: dict) -> str:
        """
        분석 결과를 보기 좋게 포맷팅
        
        Args:
            result: 분석 결과 dict
        
        Returns:
            포맷팅된 문자열
        """
        text = "📋 클립보드 코드 분석\n"
        text += "=" * 40 + "\n\n"
        
        text += f"📊 기본 정보:\n"
        text += f"  • 언어: {result['language']}\n"
        text += f"  • 길이: {result['length']}자\n"
        text += f"  • 줄 수: {result['lines']}줄\n"
        text += f"  • 복잡도: {result['complexity']}\n\n"
        
        text += f"🔍 구조:\n"
        text += f"  • 함수 포함: {'✅' if result['has_functions'] else '❌'}\n"
        text += f"  • 클래스 포함: {'✅' if result['has_classes'] else '❌'}\n\n"
        
        if 'ai_feedback' in result:
            text += f"🤖 AI 피드백:\n"
            text += f"{result['ai_feedback']}\n"
        
        return text


# Example usage
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    def on_code_detected(code, language):
        print(f"\n코드 감지! 언어: {language}")
        print(f"코드 길이: {len(code)}자")
        print(f"코드 미리보기:\n{code[:100]}...")
        
        analyzer = ClipboardAnalyzer()
        result = analyzer.quick_analyze(code, language)
        print(f"\n분석 결과:\n{analyzer.format_analysis_result(result)}")
    
    monitor = ClipboardMonitor()
    monitor.code_detected.connect(on_code_detected)
    monitor.enable()
    monitor.start()
    
    print("클립보드 모니터링 시작...")
    print("코드를 복사해보세요!")
    
    sys.exit(app.exec())
