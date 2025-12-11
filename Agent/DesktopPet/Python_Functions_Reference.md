# Python 자주 쓰는 함수 완전 정리

## 📚 목차
1. 문자열 (str)
2. 리스트 (list)
3. 딕셔너리 (dict)
4. 튜플 (tuple)
5. 집합 (set)
6. 파일 입출력
7. 내장 함수
8. 리스트 컴프리헨션
9. 예외 처리
10. 날짜/시간
11. 정규표현식
12. JSON 처리

---

## 1. 문자열 (str)

### 기본 메서드
```python
# 공백 제거
text = "  hello  "
text.strip()        # "hello" (양쪽)
text.lstrip()       # "hello  " (왼쪽)
text.rstrip()       # "  hello" (오른쪽)

# 분할/합치기
text = "a,b,c"
text.split(",")     # ['a', 'b', 'c']
",".join(['a', 'b', 'c'])  # "a,b,c"

# 치환
text = "hello world"
text.replace("world", "python")  # "hello python"

# 대소문자
text.upper()        # "HELLO WORLD"
text.lower()        # "hello world"
text.capitalize()   # "Hello world"
text.title()        # "Hello World"

# 검색
text.find("world")  # 6 (인덱스, 없으면 -1)
text.index("world") # 6 (인덱스, 없으면 에러)
text.count("l")     # 3 (개수)
text.startswith("hello")  # True
text.endswith("world")    # True

# 포맷팅
name = "John"
age = 25
f"{name} is {age}"              # "John is 25" (f-string)
"{} is {}".format(name, age)    # "John is 25"
"{name} is {age}".format(name=name, age=age)
```

---

## 2. 리스트 (list)

### 추가/삭제
```python
lst = [1, 2, 3]

# 추가
lst.append(4)           # [1, 2, 3, 4] (끝에 추가)
lst.extend([5, 6])      # [1, 2, 3, 4, 5, 6] (리스트 확장)
lst.insert(0, 0)        # [0, 1, 2, 3, 4, 5, 6] (특정 위치)

# 삭제
lst.remove(3)           # 값으로 삭제 (첫 번째만)
lst.pop()               # 마지막 요소 삭제 & 반환
lst.pop(0)              # 인덱스로 삭제 & 반환
lst.clear()             # 전체 삭제
del lst[0]              # 인덱스로 삭제
```

### 정렬/검색
```python
lst = [3, 1, 2]

# 정렬
lst.sort()              # [1, 2, 3] (원본 변경)
sorted(lst)             # [1, 2, 3] (새 리스트)
lst.sort(reverse=True)  # [3, 2, 1] (내림차순)
sorted(lst, key=lambda x: -x)  # 커스텀 정렬

# 검색
lst.index(2)            # 1 (인덱스)
lst.count(2)            # 1 (개수)
2 in lst                # True (포함 여부)

# 기타
lst.reverse()           # 역순
lst.copy()              # 복사
```

---

## 3. 딕셔너리 (dict)

### 기본 메서드
```python
d = {'a': 1, 'b': 2}

# 접근
d['a']                  # 1 (없으면 에러)
d.get('a')              # 1 (없으면 None)
d.get('c', 0)           # 0 (기본값)

# 추가/수정
d['c'] = 3              # 추가
d.update({'d': 4, 'e': 5})  # 병합

# 삭제
del d['a']              # 키로 삭제
d.pop('b')              # 삭제 & 반환
d.popitem()             # 마지막 항목 삭제 & 반환
d.clear()               # 전체 삭제

# 조회
d.keys()                # dict_keys(['a', 'b'])
d.values()              # dict_values([1, 2])
d.items()               # dict_items([('a', 1), ('b', 2)])

# 기타
d.setdefault('f', 6)    # 키가 없으면 추가
d.copy()                # 복사
```

---

## 4. 튜플 (tuple)

```python
t = (1, 2, 3)

# 불변 (immutable)
t[0]                    # 1 (접근만 가능)
t.count(2)              # 1
t.index(2)              # 1

# 언패킹
a, b, c = t             # a=1, b=2, c=3
```

---

## 5. 집합 (set)

```python
s = {1, 2, 3}

# 추가/삭제
s.add(4)                # {1, 2, 3, 4}
s.remove(2)             # {1, 3, 4} (없으면 에러)
s.discard(2)            # {1, 3, 4} (없어도 OK)
s.pop()                 # 임의 요소 삭제 & 반환
s.clear()               # 전체 삭제

# 집합 연산
s1 = {1, 2, 3}
s2 = {3, 4, 5}
s1 | s2                 # {1, 2, 3, 4, 5} (합집합)
s1 & s2                 # {3} (교집합)
s1 - s2                 # {1, 2} (차집합)
s1 ^ s2                 # {1, 2, 4, 5} (대칭차집합)
```

---

## 6. 파일 입출력

```python
# 읽기
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()          # 전체 읽기
    lines = f.readlines()       # 줄 단위 리스트
    for line in f:              # 줄 단위 반복
        print(line.strip())

# 쓰기
with open('file.txt', 'w', encoding='utf-8') as f:
    f.write("Hello\n")
    f.writelines(["Line 1\n", "Line 2\n"])

# 추가
with open('file.txt', 'a', encoding='utf-8') as f:
    f.write("Append\n")

# 바이너리
with open('file.bin', 'rb') as f:
    data = f.read()
```

---

## 7. 내장 함수

```python
# 길이/범위
len([1, 2, 3])          # 3
range(5)                # 0, 1, 2, 3, 4
range(1, 5)             # 1, 2, 3, 4
range(0, 10, 2)         # 0, 2, 4, 6, 8

# 변환
int("10")               # 10
float("3.14")           # 3.14
str(123)                # "123"
list("abc")             # ['a', 'b', 'c']
tuple([1, 2])           # (1, 2)
set([1, 1, 2])          # {1, 2}

# 수학
abs(-5)                 # 5
max([1, 2, 3])          # 3
min([1, 2, 3])          # 1
sum([1, 2, 3])          # 6
round(3.14159, 2)       # 3.14
pow(2, 3)               # 8

# 반복/변환
enumerate(['a', 'b'])   # [(0, 'a'), (1, 'b')]
zip([1, 2], ['a', 'b']) # [(1, 'a'), (2, 'b')]
reversed([1, 2, 3])     # [3, 2, 1]

# 필터/맵
map(lambda x: x*2, [1, 2, 3])       # [2, 4, 6]
filter(lambda x: x>1, [1, 2, 3])    # [2, 3]

# 논리
any([False, True, False])   # True (하나라도 True)
all([True, True, True])     # True (모두 True)

# 타입 체크
type(123)               # <class 'int'>
isinstance(123, int)    # True
```

---

## 8. 리스트 컴프리헨션

```python
# 기본
[x for x in range(5)]                   # [0, 1, 2, 3, 4]
[x*2 for x in range(5)]                 # [0, 2, 4, 6, 8]

# 조건
[x for x in range(10) if x % 2 == 0]   # [0, 2, 4, 6, 8]

# 중첩
[(x, y) for x in range(3) for y in range(3)]

# 딕셔너리 컴프리헨션
{x: x**2 for x in range(5)}             # {0: 0, 1: 1, 2: 4, ...}

# 집합 컴프리헨션
{x for x in [1, 1, 2, 2, 3]}            # {1, 2, 3}
```

---

## 9. 예외 처리

```python
# 기본
try:
    result = 10 / 0
except ZeroDivisionError:
    print("0으로 나눌 수 없습니다")
except Exception as e:
    print(f"에러: {e}")
else:
    print("성공")
finally:
    print("항상 실행")

# 예외 발생
raise ValueError("잘못된 값")

# assert
assert x > 0, "x는 양수여야 합니다"

# 커스텀 예외
class MyError(Exception):
    pass

raise MyError("커스텀 에러")
```

---

## 10. 날짜/시간

```python
from datetime import datetime, timedelta

# 현재 시간
now = datetime.now()                    # 2024-01-01 12:00:00
now.year, now.month, now.day            # 2024, 1, 1
now.hour, now.minute, now.second        # 12, 0, 0

# 포맷팅
now.strftime("%Y-%m-%d %H:%M:%S")       # "2024-01-01 12:00:00"
datetime.strptime("2024-01-01", "%Y-%m-%d")

# 시간 계산
tomorrow = now + timedelta(days=1)
week_ago = now - timedelta(weeks=1)
```

---

## 11. 정규표현식

```python
import re

text = "My email is test@example.com"

# 검색
re.search(r'\w+@\w+\.\w+', text)        # Match 객체
re.findall(r'\d+', "abc123def456")      # ['123', '456']

# 치환
re.sub(r'\d+', 'X', "abc123def456")     # "abcXdefX"

# 분할
re.split(r'\s+', "a  b   c")            # ['a', 'b', 'c']

# 패턴
# \d : 숫자 [0-9]
# \w : 단어 문자 [a-zA-Z0-9_]
# \s : 공백
# . : 모든 문자
# * : 0회 이상
# + : 1회 이상
# ? : 0 또는 1회
# {n} : 정확히 n회
# [abc] : a, b, c 중 하나
# ^ : 시작
# $ : 끝
```

---

## 12. JSON 처리

```python
import json

# 딕셔너리 → JSON 문자열
data = {'name': 'John', 'age': 25}
json_str = json.dumps(data)             # '{"name": "John", "age": 25}'
json_str = json.dumps(data, indent=2, ensure_ascii=False)  # 예쁘게

# JSON 문자열 → 딕셔너리
data = json.loads(json_str)

# 파일 저장
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# 파일 읽기
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
```

---

## 💡 자주 쓰는 패턴

### 파일 읽기 (안전)
```python
import os

if os.path.exists('file.txt'):
    with open('file.txt', 'r', encoding='utf-8') as f:
        content = f.read()
```

### 리스트 중복 제거
```python
lst = [1, 2, 2, 3, 3]
unique = list(set(lst))                 # [1, 2, 3]
unique = list(dict.fromkeys(lst))       # 순서 유지
```

### 딕셔너리 병합
```python
d1 = {'a': 1, 'b': 2}
d2 = {'b': 3, 'c': 4}
merged = {**d1, **d2}                   # {'a': 1, 'b': 3, 'c': 4}
```

### 리스트 평탄화
```python
nested = [[1, 2], [3, 4], [5]]
flat = [item for sublist in nested for item in sublist]  # [1, 2, 3, 4, 5]
```

### 카운팅
```python
from collections import Counter

lst = ['a', 'b', 'a', 'c', 'b', 'a']
Counter(lst)                            # {'a': 3, 'b': 2, 'c': 1}
```

---

## 🎯 성능 팁

1. **리스트 대신 제너레이터**: 메모리 절약
   ```python
   (x*2 for x in range(1000000))  # 제너레이터
   ```

2. **in 연산**: set이 list보다 빠름
   ```python
   s = set([1, 2, 3])
   2 in s  # O(1)
   ```

3. **문자열 합치기**: join 사용
   ```python
   ''.join(['a', 'b', 'c'])  # 빠름
   'a' + 'b' + 'c'           # 느림
   ```

4. **딕셔너리 기본값**: setdefault, defaultdict
   ```python
   from collections import defaultdict
   d = defaultdict(list)
   d['key'].append(1)  # 자동 초기화
   ```
