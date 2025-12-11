"""
Test Generator Module
Python 함수에 대한 pytest 테스트 자동 생성
"""

import re
import ast
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os


class TestGenerator:
    """자동 테스트 생성기"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Test Generator
        
        Args:
            api_key: Gemini API key
        """
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
        
        self.ai_available = False
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.ai_available = True
            except Exception as e:
                print(f"AI 초기화 실패: {e}")
    
    def parse_function(self, code: str) -> List[Dict]:
        """
        코드에서 함수 추출
        
        Args:
            code: Python 코드
        
        Returns:
            함수 정보 리스트
        """
        functions = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'lineno': node.lineno,
                        'has_return': any(isinstance(n, ast.Return) for n in ast.walk(node)),
                        'docstring': ast.get_docstring(node)
                    }
                    functions.append(func_info)
        
        except Exception as e:
            print(f"함수 파싱 실패: {e}")
        
        return functions
    
    def generate_test(self, code: str, function_name: Optional[str] = None) -> str:
        """
        pytest 테스트 생성
        
        Args:
            code: 테스트할 코드
            function_name: 특정 함수명 (None이면 모든 함수)
        
        Returns:
            생성된 테스트 코드
        """
        if not self.ai_available:
            return "AI를 사용할 수 없습니다. API 키를 확인해주세요."
        
        prompt = f"""
다음 Python 코드에 대한 pytest 테스트를 생성해주세요.

코드:
```python
{code}
```

요구사항:
1. pytest 형식 사용
2. 정상 케이스 테스트
3. 엣지 케이스 테스트
4. 예외 케이스 테스트 (해당되는 경우)
5. 각 테스트에 명확한 docstring 추가

형식:
```python
import pytest

def test_함수명_정상케이스():
    \"\"\"정상 동작 테스트\"\"\"
    # 테스트 코드

def test_함수명_엣지케이스():
    \"\"\"엣지 케이스 테스트\"\"\"
    # 테스트 코드

def test_함수명_예외케이스():
    \"\"\"예외 처리 테스트\"\"\"
    # 테스트 코드
```

**주의**: 테스트 코드만 출력하고 설명은 하지 마세요.
"""
        
        try:
            response = self.model.generate_content(prompt)
            test_code = response.text.strip()
            
            # 마크다운 코드 블록 제거
            if test_code.startswith("```"):
                lines = test_code.split('\n')
                test_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else test_code
            
            return test_code
            
        except Exception as e:
            return f"테스트 생성 실패: {str(e)}"
    
    def generate_quick_test(self, function_code: str) -> str:
        """
        간단한 테스트 빠르게 생성
        
        Args:
            function_code: 함수 코드
        
        Returns:
            간단한 테스트 코드
        """
        if not self.ai_available:
            return "AI를 사용할 수 없습니다."
        
        prompt = f"""
다음 함수에 대한 간단한 pytest 테스트 1개만 생성해주세요:

{function_code}

형식:
```python
def test_함수명():
    assert 함수명(입력) == 예상결과
```

**주의**: 테스트 코드만 출력하세요.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"테스트 생성 실패: {str(e)}"


# Example usage
if __name__ == "__main__":
    generator = TestGenerator()
    
    sample_code = """
def add_numbers(a, b):
    \"\"\"두 숫자를 더합니다\"\"\"
    return a + b

def divide_numbers(a, b):
    \"\"\"두 숫자를 나눕니다\"\"\"
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    return a / b
"""
    
    print("=== 함수 파싱 ===")
    functions = generator.parse_function(sample_code)
    for func in functions:
        print(f"함수: {func['name']}, 인자: {func['args']}")
    
    print("\n=== 테스트 생성 ===")
    test_code = generator.generate_test(sample_code)
    print(test_code)
