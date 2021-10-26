# Naver SmartStore Helper

네이버 스마트스토어 운영을 도와주는 스크립트입니다.

<br>

## 환경

<br>

### 설치

1. python >= 3.8, 가상환경 사용을 적극 권장합니다.
2. [Google 프로젝트 생성 및 `Google Sheets API` 승인](https://developers.google.com/workspace/guides/create-project)
3. [Google 서비스계정 인증 토큰 발급](https://developers.google.com/workspace/guides/create-credentials)
4. [셀리니움 플러그인 설치](https://chancoding.tistory.com/136)

`command`
```
python3 -m pip install --user --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install .
```

<br>

### 경로 설정

TODO

<br>

## 문제해결

<br>

### 설치할 때

문제를 미연에 방지하기 위해 꼭 가상환경을 사용하세요.

<br>

### 실행할 때

`output`
```
ValueError: ('Unexpected credentials type', None, 'Expected', 'service_account')
```

- 서비스계정이 아니라 클라이언트 계정의 json 파일을 다운로드받아서 발생
- 서비스계정 > 키 > 키 추가 > 다운로드 와 같은 방식으로 해결 가능
