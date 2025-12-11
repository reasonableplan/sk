"""
Code Analyzer Module
코드 품질 및 스타일 분석
"""

import re
from typing import Dict, List
try:
    import pycodestyle
    PYCODESTYLE_AVAILABLE = True
except ImportError:
    PYCODESTYLE_AVAILABLE = False
    print("Warning: pycodestyle not available. Install with: pip install pycodestyle")


class CodeAnalyzer:
    """코드 분석기"""
    
    def __init__(self):
        self.pycodestyle_available = PYCODESTYLE_AVAILABLE
    
    def analyze_code(self, code: str, language: str = "python") -> Dict:
        """
        코드 종합 분석
        
        Args:
            code: 분석할 코드
            language: 프로그래밍 언어
        
        Returns:
            분석 결과 dict
        """
        result = {
            'language': language,
            'lines': code.count('\n') + 1,
            'characters': len(code),
            'complexity': self.estimate_complexity(code),
            'style_issues': [],
            'security_issues': [],
            'suggestions': []
        }
        
        if language.lower() == "python":
            result['style_issues'] = self.check_pep8(code)
            result['security_issues'] = self.check_security(code)
        
        result['suggestions'] = self.generate_suggestions(result)
        
        return result
    
    def check_pep8(self, code: str) -> List[str]:
        """
        PEP 8 스타일 체크
        
        Args:
            code: Python 코드
        
        Returns:
            스타일 이슈 리스트
        """
        if not self.pycodestyle_available:
            return ["pycodestyle 패키지가 설치되지 않았습니다"]
        
        issues = []
        
        try:
            # 임시 파일에 저장하지 않고 직접 체크
            style_guide = pycodestyle.StyleGuide(quiet=True)
            
            # 코드를 라인별로 체크
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                # 라인 길이 체크
                if len(line) > 79:
                    issues.append(f"라인 {i}: 79자 초과 ({len(line)}자)")
                
                # 들여쓰기 체크 (4칸)
                if line and not line.startswith('#'):
                    leading_spaces = len(line) - len(line.lstrip(' '))
                    if leading_spaces % 4 != 0:
                        issues.append(f"라인 {i}: 들여쓰기가 4의 배수가 아님")
        
        except Exception as e:
            issues.append(f"PEP 8 체크 실패: {str(e)}")
        
        return issues[:10]  # 최대 10개만
    
    def estimate_complexity(self, code: str) -> Dict:
        """
        코드 복잡도 추정
        
        Args:
            code: 코드
        
        Returns:
            복잡도 정보
        """
        lines = code.count('\n') + 1
        
        # 제어 구조 개수
        control_count = (
            code.count('if ') +
            code.count('for ') +
            code.count('while ') +
            code.count('elif ') +
            code.count('else:')
        )
        
        # 함수 개수
        function_count = code.count('def ') + code.count('function ')
        
        # 클래스 개수
        class_count = code.count('class ')
        
        # 복잡도 점수 계산
        complexity_score = (
            lines * 0.1 +
            control_count * 2 +
            function_count * 1 +
            class_count * 3
        )
        
        if complexity_score < 10:
            level = "낮음"
        elif complexity_score < 30:
            level = "보통"
        else:
            level = "높음"
        
        return {
            'level': level,
            'score': round(complexity_score, 1),
            'lines': lines,
            'control_structures': control_count,
            'functions': function_count,
            'classes': class_count
        }
    
    def check_security(self, code: str) -> List[str]:
        """
        보안 이슈 체크
        
        Args:
            code: Python 코드
        
        Returns:
            보안 이슈 리스트
        """
        issues = []
        
        # 위험한 함수 사용
        dangerous_functions = [
            ('eval(', '위험: eval() 사용 - 코드 인젝션 위험'),
            ('exec(', '위험: exec() 사용 - 코드 인젝션 위험'),
            ('pickle.loads', '주의: pickle.loads() - 신뢰할 수 없는 데이터 역직렬화 위험'),
            ('os.system(', '주의: os.system() - 명령 인젝션 위험'),
            ('subprocess.call(', '주의: subprocess - 셸 인젝션 위험 (shell=True 확인)'),
        ]
        
        for func, warning in dangerous_functions:
            if func in code:
                issues.append(warning)
        
        # SQL 인젝션 가능성
        if 'execute(' in code and '%s' in code:
            issues.append('주의: SQL 쿼리 - 파라미터화된 쿼리 사용 권장')
        
        # 하드코딩된 비밀번호/키
        if re.search(r'password\s*=\s*["\']', code, re.IGNORECASE):
            issues.append('경고: 하드코딩된 비밀번호 발견')
        
        if re.search(r'api[_-]?key\s*=\s*["\']', code, re.IGNORECASE):
            issues.append('경고: 하드코딩된 API 키 발견')
        
        return issues
    
    def generate_suggestions(self, analysis: Dict) -> List[str]:
        """
        분석 결과 기반 개선 제안
        
        Args:
            analysis: 분석 결과
        
        Returns:
            제안 리스트
        """
        suggestions = []
        
        # 복잡도 기반 제안
        if analysis['complexity']['level'] == "높음":
            suggestions.append("코드 복잡도가 높습니다. 함수를 더 작은 단위로 분리하세요.")
        
        if analysis['complexity']['functions'] == 0:
            suggestions.append("함수가 없습니다. 재사용 가능한 함수로 분리하세요.")
        
        # 스타일 이슈 기반 제안
        if len(analysis['style_issues']) > 5:
            suggestions.append("PEP 8 스타일 가이드를 따르도록 코드를 정리하세요.")
        
        # 보안 이슈 기반 제안
        if analysis['security_issues']:
            suggestions.append("보안 이슈가 발견되었습니다. 즉시 수정하세요.")
        
        # 코드 길이 기반 제안
        if analysis['lines'] > 100:
            suggestions.append("코드가 길어 가독성이 떨어질 수 있습니다. 모듈화를 고려하세요.")
        
        return suggestions
    
    def format_analysis_result(self, result: Dict) -> str:
        """
        분석 결과 포맷팅
        
        Args:
            result: 분석 결과
        
        Returns:
            포맷팅된 문자열
        """
        text = "🔍 코드 분석 결과\n"
        text += "=" * 50 + "\n\n"
        
        # 기본 정보
        text += f"📊 기본 정보:\n"
        text += f"  • 언어: {result['language']}\n"
        text += f"  • 줄 수: {result['lines']}줄\n"
        text += f"  • 문자 수: {result['characters']}자\n\n"
        
        # 복잡도
        comp = result['complexity']
        text += f"📈 복잡도: {comp['level']} (점수: {comp['score']})\n"
        text += f"  • 제어 구조: {comp['control_structures']}개\n"
        text += f"  • 함수: {comp['functions']}개\n"
        text += f"  • 클래스: {comp['classes']}개\n\n"
        
        # 스타일 이슈
        if result['style_issues']:
            text += f"⚠️ 스타일 이슈 ({len(result['style_issues'])}개):\n"
            for issue in result['style_issues'][:5]:
                text += f"  • {issue}\n"
            if len(result['style_issues']) > 5:
                text += f"  ... 외 {len(result['style_issues']) - 5}개\n"
            text += "\n"
        
        # 보안 이슈
        if result['security_issues']:
            text += f"🔒 보안 이슈 ({len(result['security_issues'])}개):\n"
            for issue in result['security_issues']:
                text += f"  • {issue}\n"
            text += "\n"
        
        # 제안
        if result['suggestions']:
            text += f"💡 개선 제안:\n"
            for suggestion in result['suggestions']:
                text += f"  • {suggestion}\n"
        
        return text


# Example usage
if __name__ == "__main__":
    analyzer = CodeAnalyzer()
    
    sample_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        if num > 0:
            total = total + num
    return total

password = "admin123"  # 하드코딩된 비밀번호
"""
    
    result = analyzer.analyze_code(sample_code)
    print(analyzer.format_analysis_result(result))
