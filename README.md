# 인사, 노무 챗봇

이 프로젝트는 인사, 노무 관련 질문을 처리하는 챗봇 서버입니다. Python을 기반으로 개발되었습니다.

## 요구 사항
- Python 3.10 이상
- openai API 키
- langchain API 키
- flask
- mongoDB

## 설치방법
```python
git clone https://github.com/komehere777/labor_chatbot_server.git
cd labor_chatbot_server
# 가상환경 생성
python -m venv venv
# 가상환경 활성화: 윈도우
venv\Scripts\activate
# 가상환경 활성화: 리눅스
source venv/bin/activate
# 패키지 설치
pip install -r requirements.txt
```
# 시크릿키 생성
```python
python generate_secret_key.py
```

## config.py 설정
config.py 파일을 생성하고 다음과 같이 설정을 추가합니다.
```python
OPENAI_API_KEY = 'your openai api key'
MONGO_URI = 'mongodb://localhost:27017/'
MONGO_DBNAME = 'your db name'
SECRET_KEY = 'your secret key'
LANGSMITH_API_KEY = 'your langsmith api key'
LANGCHAIN_PROJECT_NAME = "your langchain project name"
LANCHAIN_ENDPOINT = "https://api.smith.langchain.com"
```

## 실행
```python
python app.py
```
서버는 http://{서버ip}:5001에서 실행됩니다. 웹 브라우저나 챗봇 클라이언트를 통해 접속할 수 있습니다.

## 프로젝트 구조
```python
app.py: 서버의 메인 엔트리 포인트
model.py: 챗봇 모델 로직
utils.py: llm 모델을 위한 유틸리티 함수
templates/: 웹 인터페이스를 위한 HTML 템플릿
static/: 프론트엔드에서 사용하는 정적 파일 (CSS, JS 등)
