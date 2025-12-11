"""
AI Code Reviewer Module
Gemini API를 사용하여 코드를 분석하고 리뷰를 제공합니다.
"""

import os
from typing import Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

class AICodeReviewer:
    """AI 기반 코드 리뷰어"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI Code Reviewer
        
        Args:
            api_key: Gemini API key. If None, loads from environment
        """
        # Load API key
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in .env file or pass as parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.api_configured = True
    
    def review_code(self, code: str, language: str = "python") -> Dict[str, any]:
        """
        코드를 리뷰하고 상세한 피드백을 제공합니다.
        
        Args:
            code: 리뷰할 코드
            language: 프로그래밍 언어 (기본값: python)
        
        Returns:
            Dict containing:
                - score: 코드 품질 점수 (1-10)
                - issues: 발견된 문제점 리스트
                - suggestions: 개선 제안 리스트
                - refactored_code: 리팩토링된 코드
                - summary: 전체 요약
        """
        if not code.strip():
            return {
                "score": 0,
                "issues": ["코드가 비어있습니다."],
                "suggestions": [],
                "refactored_code": "",
                "summary": "리뷰할 코드가 없습니다."
            }
        
        prompt = f"""
당신은 시니어 소프트웨어 엔지니어입니다. 다음 {language} 코드를 전문가 관점에서 리뷰해주세요.

```{language}
{code}
```

다음 형식으로 응답해주세요:

## 코드 품질 점수
[1-10점 사이의 점수와 간단한 이유]

## 발견된 문제점
1. [문제점 1]
2. [문제점 2]
...

## 개선 제안
1. [제안 1]
2. [제안 2]
...

## 리팩토링된 코드
```{language}
[개선된 코드]
```

## 요약
[전체적인 평가와 핵심 개선 사항]

**주의사항**:
- 코드 스타일, 성능, 보안, 가독성 모두 고려
- 구체적이고 실행 가능한 제안 제공
- 긍정적인 부분도 언급
"""
        
        try:
            response = self.model.generate_content(prompt)
            review_text = response.text
            
            # Parse the response
            parsed = self._parse_review(review_text)
            return parsed
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"AI 리뷰 중 오류 발생: {str(e)}"],
                "suggestions": [],
                "refactored_code": "",
                "summary": "리뷰를 완료할 수 없습니다."
            }
    
    def _parse_review(self, review_text: str) -> Dict[str, any]:
        """
        AI 응답을 파싱하여 구조화된 데이터로 변환
        
        Args:
            review_text: AI의 원본 응답
        
        Returns:
            구조화된 리뷰 데이터
        """
        result = {
            "score": 5,
            "issues": [],
            "suggestions": [],
            "refactored_code": "",
            "summary": "",
            "raw_review": review_text
        }
        
        # Extract score
        if "점수" in review_text or "Score" in review_text:
            import re
            score_match = re.search(r'(\d+)/10|(\d+)점', review_text)
            if score_match:
                result["score"] = int(score_match.group(1) or score_match.group(2))
        
        # Extract sections
        sections = review_text.split("##")
        
        for section in sections:
            section = section.strip()
            
            if "문제점" in section or "Issues" in section:
                lines = section.split("\n")[1:]  # Skip header
                result["issues"] = [
                    line.strip().lstrip("1234567890.-• ") 
                    for line in lines 
                    if line.strip() and not line.startswith("#")
                ]
            
            elif "개선" in section or "Suggestions" in section:
                lines = section.split("\n")[1:]
                result["suggestions"] = [
                    line.strip().lstrip("1234567890.-• ") 
                    for line in lines 
                    if line.strip() and not line.startswith("#")
                ]
            
            elif "리팩토링" in section or "Refactored" in section:
                # Extract code block
                import re
                code_match = re.search(r'```[\w]*\n(.*?)\n```', section, re.DOTALL)
                if code_match:
                    result["refactored_code"] = code_match.group(1).strip()
            
            elif "요약" in section or "Summary" in section:
                lines = section.split("\n")[1:]
                result["summary"] = "\n".join(
                    line.strip() for line in lines if line.strip()
                )
        
        return result
    
    def quick_check(self, code: str, language: str = "python") -> str:
        """
        빠른 코드 체크 (간단한 피드백만)
        
        Args:
            code: 체크할 코드
            language: 프로그래밍 언어
        
        Returns:
            간단한 피드백 문자열
        """
        prompt = f"""
다음 {language} 코드를 간단히 체크하고 1-2문장으로 피드백을 주세요:

```{language}
{code}
```

형식: [품질: 좋음/보통/나쁨] - [핵심 피드백 1-2문장]
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"체크 실패: {str(e)}"
    
    def suggest_improvements(self, code: str, language: str = "python") -> list:
        """
        개선 제안만 빠르게 가져오기
        
        Args:
            code: 분석할 코드
            language: 프로그래밍 언어
        
        Returns:
            개선 제안 리스트
        """
        review = self.review_code(code, language)
        return review.get("suggestions", [])
    
    def analyze_security(self, code: str, language: str = "python") -> Dict[str, any]:
        """
        보안 취약점 분석
        
        Args:
            code: 분석할 코드
            language: 프로그래밍 언어
        
        Returns:
            보안 분석 결과
        """
        prompt = f"""
다음 {language} 코드의 보안 취약점을 분석해주세요:

```{language}
{code}
```

다음 항목을 체크해주세요:
1. SQL Injection
2. XSS (Cross-Site Scripting)
3. 인증/인가 문제
4. 민감 정보 노출
5. 안전하지 않은 함수 사용

형식:
## 보안 등급
[안전함/주의/위험]

## 발견된 취약점
1. [취약점과 위험도]

## 보안 개선 방안
1. [구체적인 개선 방법]
"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "analysis": response.text,
                "safe": "안전함" in response.text or "Safe" in response.text
            }
        except Exception as e:
            return {
                "analysis": f"보안 분석 실패: {str(e)}",
                "safe": None
            }


# Example usage
if __name__ == "__main__":
    # Test the reviewer
    reviewer = AICodeReviewer()
    
    test_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item
    return total
"""
    
    print("=== AI Code Review ===")
    result = reviewer.review_code(test_code)
    
    print(f"\n점수: {result['score']}/10")
    print(f"\n문제점:")
    for issue in result['issues']:
        print(f"  - {issue}")
    
    print(f"\n개선 제안:")
    for suggestion in result['suggestions']:
        print(f"  - {suggestion}")
    
    if result['refactored_code']:
        print(f"\n리팩토링된 코드:")
        print(result['refactored_code'])
    
    print(f"\n요약:")
    print(result['summary'])
