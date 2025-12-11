"""
Git Assistant Module
Git 작업 자동화 및 AI 커밋 메시지 생성
"""

import os
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv


class GitAssistant:
    """Git 통합 및 자동화 도우미"""
    
    def __init__(self, repo_path: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Git Assistant
        
        Args:
            repo_path: Git 저장소 경로. None이면 현재 디렉토리
            api_key: Gemini API key. None이면 환경변수에서 로드
        """
        self.repo_path = repo_path or os.getcwd()
        
        # API 키 설정
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
        
        # Git 저장소 확인
        self.is_git_repo = self._check_git_repo()
    
    def _check_git_repo(self) -> bool:
        """현재 디렉토리가 Git 저장소인지 확인"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, any]:
        """
        Git 저장소 상태 가져오기
        
        Returns:
            Dict containing:
                - branch: 현재 브랜치명
                - modified: 수정된 파일 리스트
                - staged: 스테이징된 파일 리스트
                - untracked: 추적되지 않는 파일 리스트
                - clean: 변경사항이 없는지 여부
        """
        if not self.is_git_repo:
            return {
                "error": "Git 저장소가 아닙니다",
                "branch": None,
                "modified": [],
                "staged": [],
                "untracked": [],
                "clean": False
            }
        
        try:
            # 현재 브랜치
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            branch = branch_result.stdout.strip()
            
            # 상태 확인
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            
            modified = []
            staged = []
            untracked = []
            
            for line in status_result.stdout.split('\n'):
                if not line.strip():
                    continue
                
                status_code = line[:2]
                filename = line[3:].strip()
                
                if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                    staged.append(filename)
                if status_code[1] == 'M':
                    modified.append(filename)
                if status_code == '??':
                    untracked.append(filename)
            
            return {
                "branch": branch,
                "modified": modified,
                "staged": staged,
                "untracked": untracked,
                "clean": len(modified) == 0 and len(staged) == 0 and len(untracked) == 0
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "branch": None,
                "modified": [],
                "staged": [],
                "untracked": [],
                "clean": False
            }
    
    def get_diff(self, staged_only: bool = True) -> str:
        """
        변경사항 diff 가져오기
        
        Args:
            staged_only: True면 스테이징된 변경사항만, False면 모든 변경사항
        
        Returns:
            Diff 텍스트
        """
        if not self.is_git_repo:
            return "Git 저장소가 아닙니다"
        
        try:
            cmd = ['git', 'diff']
            if staged_only:
                cmd.append('--cached')
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            return result.stdout
            
        except Exception as e:
            return f"Diff 가져오기 실패: {str(e)}"
    
    def generate_commit_message(self, diff: Optional[str] = None, style: str = "conventional") -> str:
        """
        AI를 사용하여 커밋 메시지 생성
        
        Args:
            diff: Git diff 텍스트. None이면 자동으로 가져옴
            style: 커밋 메시지 스타일 (conventional, simple, detailed)
        
        Returns:
            생성된 커밋 메시지
        """
        if not self.ai_available:
            return "AI를 사용할 수 없습니다. API 키를 확인해주세요."
        
        if diff is None:
            diff = self.get_diff(staged_only=True)
        
        if not diff or diff.strip() == "":
            return "변경사항이 없습니다"
        
        # 스타일별 프롬프트
        if style == "conventional":
            prompt = f"""
다음 Git diff를 분석하여 Conventional Commits 형식의 커밋 메시지를 생성해주세요.

Git Diff:
```
{diff[:3000]}  # 너무 길면 잘라냄
```

형식:
<type>(<scope>): <subject>

<body>

type: feat, fix, docs, style, refactor, test, chore 중 선택
scope: 변경된 모듈/파일 (선택사항)
subject: 50자 이내 요약
body: 상세 설명 (선택사항)

예시:
feat(auth): add user login functionality

Implement JWT-based authentication system
- Add login endpoint
- Create token validation middleware

**주의**: 커밋 메시지만 출력하고 다른 설명은 하지 마세요.
"""
        elif style == "simple":
            prompt = f"""
다음 Git diff를 분석하여 간단한 한 줄 커밋 메시지를 생성해주세요.

Git Diff:
```
{diff[:3000]}
```

형식: 동사로 시작하는 간결한 문장 (50자 이내)
예시: Add user authentication feature

**주의**: 커밋 메시지만 출력하고 다른 설명은 하지 마세요.
"""
        else:  # detailed
            prompt = f"""
다음 Git diff를 분석하여 상세한 커밋 메시지를 생성해주세요.

Git Diff:
```
{diff[:3000]}
```

형식:
[제목] 변경사항 요약 (50자 이내)

[본문]
- 변경된 내용 1
- 변경된 내용 2
- 변경된 내용 3

**주의**: 커밋 메시지만 출력하고 다른 설명은 하지 마세요.
"""
        
        try:
            response = self.model.generate_content(prompt)
            message = response.text.strip()
            
            # 마크다운 코드 블록 제거
            if message.startswith("```"):
                lines = message.split('\n')
                message = '\n'.join(lines[1:-1]) if len(lines) > 2 else message
            
            return message
            
        except Exception as e:
            return f"커밋 메시지 생성 실패: {str(e)}"
    
    def stage_files(self, files: List[str]) -> Tuple[bool, str]:
        """
        파일을 스테이징 영역에 추가
        
        Args:
            files: 스테이징할 파일 경로 리스트
        
        Returns:
            (성공 여부, 메시지)
        """
        if not self.is_git_repo:
            return False, "Git 저장소가 아닙니다"
        
        try:
            cmd = ['git', 'add'] + files
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode == 0:
                return True, f"{len(files)}개 파일 스테이징 완료"
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)
    
    def commit(self, message: str) -> Tuple[bool, str]:
        """
        커밋 실행
        
        Args:
            message: 커밋 메시지
        
        Returns:
            (성공 여부, 메시지)
        """
        if not self.is_git_repo:
            return False, "Git 저장소가 아닙니다"
        
        if not message.strip():
            return False, "커밋 메시지가 비어있습니다"
        
        try:
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "커밋 성공!\n" + result.stdout
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)
    
    def get_recent_commits(self, count: int = 10) -> List[Dict[str, str]]:
        """
        최근 커밋 히스토리 가져오기
        
        Args:
            count: 가져올 커밋 개수
        
        Returns:
            커밋 정보 리스트 [{hash, author, date, message}]
        """
        if not self.is_git_repo:
            return []
        
        try:
            result = subprocess.run(
                ['git', 'log', f'-{count}', '--pretty=format:%h|%an|%ar|%s'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            return commits
            
        except Exception as e:
            print(f"커밋 히스토리 가져오기 실패: {e}")
            return []
    
    def get_branch_info(self) -> Dict[str, any]:
        """
        브랜치 정보 가져오기
        
        Returns:
            Dict containing:
                - current: 현재 브랜치
                - all: 모든 브랜치 리스트
                - remote: 원격 브랜치 리스트
        """
        if not self.is_git_repo:
            return {"current": None, "all": [], "remote": []}
        
        try:
            # 현재 브랜치
            current_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            current = current_result.stdout.strip()
            
            # 모든 로컬 브랜치
            all_result = subprocess.run(
                ['git', 'branch'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            all_branches = [
                line.strip().replace('* ', '') 
                for line in all_result.stdout.split('\n') 
                if line.strip()
            ]
            
            # 원격 브랜치
            remote_result = subprocess.run(
                ['git', 'branch', '-r'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            remote_branches = [
                line.strip() 
                for line in remote_result.stdout.split('\n') 
                if line.strip() and 'HEAD' not in line
            ]
            
            return {
                "current": current,
                "all": all_branches,
                "remote": remote_branches
            }
            
        except Exception as e:
            print(f"브랜치 정보 가져오기 실패: {e}")
            return {"current": None, "all": [], "remote": []}


# Example usage
if __name__ == "__main__":
    git = GitAssistant()
    
    print("=== Git 상태 ===")
    status = git.get_status()
    print(f"브랜치: {status['branch']}")
    print(f"수정된 파일: {status['modified']}")
    print(f"스테이징된 파일: {status['staged']}")
    
    if status['staged']:
        print("\n=== AI 커밋 메시지 생성 ===")
        message = git.generate_commit_message(style="conventional")
        print(message)
