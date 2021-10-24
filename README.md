### 과정

1. python >= 3.7, 가상환경 사용을 적극 권장합니다.
2. [Google 프로젝트 생성 및 `Google Sheets API` 승인](https://developers.google.com/workspace/guides/create-project)
3. [Google 서비스계정 인증 토큰 발급](https://developers.google.com/workspace/guides/create-credentials)
4. [셀리니움 플러그인 설치](https://chancoding.tistory.com/136)

```
python3 -m pip install --user --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install .
```

### 실수하기 쉬운 것

```
ValueError: ('Unexpected credentials type', None, 'Expected', 'service_account')
```

- 서비스계정이 아니라 클라이언트 계정의 json 파일을 다운로드받아서 발생
- 서비스계정 > 키 > 키 추가 > 다운로드 와 같은 방식으로 해결 가능


```
gspread.exceptions.APIError: {'code': 403, 'message': 'Google Sheets API has not been used in project 439012858567 before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=439012858567 then retry.
```
