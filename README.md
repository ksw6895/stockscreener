# Enhanced NASDAQ Stock Screener 📈

강력한 금융 분석과 백테스팅 기능을 갖춘 NASDAQ 주식 스크리너입니다.

A comprehensive stock screening and analysis system for NASDAQ stocks with powerful financial analysis and backtesting capabilities.

## 🌟 주요 기능 (Key Features)

- **고급 금융 분석**: 20개 이상의 금융 지표를 활용한 종합 분석
- **섹터 상대 평가**: 동일 섹터 내 상대적 성과 비교
- **리스크 프로파일링**: 부채 수준, 마진 안정성, 현금 흐름 품질 평가
- **백테스팅**: 과거 데이터 기반 전략 검증 (Sharpe Ratio, Maximum Drawdown 등)
- **벤치마크 비교**: S&P 500, NASDAQ 지수 대비 성과 분석
- **GUI & CLI 지원**: 그래픽 인터페이스와 커맨드라인 모두 지원
- **Excel 리포트**: 차트와 함께 상세한 분석 결과 제공

## 📋 사전 요구사항 (Prerequisites)

### 필수 요구사항
- Python 3.8 이상
- Financial Modeling Prep API 키 (유료 구독 필요)
- 최소 4GB RAM
- 인터넷 연결

### 운영체제별 요구사항
- **Windows**: Windows 10/11
- **WSL**: WSL2 (Ubuntu 20.04 이상 권장)
- **Linux/Mac**: Python 3.8+ 설치

---

## 🚀 설치 가이드 (Installation Guide)

## 🪟 Windows 설치 가이드

### 1단계: Python 설치

1. [Python 공식 웹사이트](https://www.python.org/downloads/)에서 Python 3.8 이상 다운로드
2. 설치 시 **"Add Python to PATH"** 체크박스 반드시 선택
3. 설치 완료 후 명령 프롬프트(cmd) 또는 PowerShell 열기
4. Python 설치 확인:
```cmd
python --version
```

### 2단계: Git 설치 (선택사항)

1. [Git for Windows](https://git-scm.com/download/win) 다운로드 및 설치
2. 설치 확인:
```cmd
git --version
```

### 3단계: 프로젝트 다운로드

**Git을 사용하는 경우:**
```cmd
git clone https://github.com/ksw6895/stockscreener.git
cd stockscreener
```

**Git이 없는 경우:**
1. GitHub에서 ZIP 파일로 다운로드
2. 원하는 폴더에 압축 해제
3. 명령 프롬프트에서 해당 폴더로 이동:
```cmd
cd C:\Users\사용자명\Documents\stockscreener
```

### 4단계: 가상환경 생성 (권장)

```cmd
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 활성화 확인 (프롬프트 앞에 (venv) 표시)
```

### 5단계: 패키지 설치

```cmd
# pip 업그레이드
python -m pip install --upgrade pip

# 필수 패키지 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install aiohttp numpy openpyxl python-dotenv matplotlib
```

### 6단계: API 키 설정

1. 프로젝트 폴더에 `.env` 파일 생성
2. 메모장으로 `.env` 파일 열기:
```cmd
notepad .env
```
3. 다음 내용 입력 후 저장:
```
FMP_API_KEY=your_actual_api_key_here
```

### 7단계: 실행

**GUI 모드:**
```cmd
python gui.py
```

**CLI 모드:**
```cmd
python stock_screener.py
```

**백테스팅:**
```cmd
python backtest.py --period 6m --investment 100000
```

---

## 🐧 WSL (Windows Subsystem for Linux) 설치 가이드

### 1단계: WSL2 설치

1. **PowerShell을 관리자 권한으로 실행**
2. WSL 설치:
```powershell
wsl --install
```
3. 컴퓨터 재시작
4. Ubuntu 설치 (Microsoft Store에서 Ubuntu 20.04 또는 22.04 설치)

### 2단계: WSL Ubuntu 초기 설정

1. Ubuntu 터미널 열기
2. 시스템 업데이트:
```bash
sudo apt update && sudo apt upgrade -y
```

### 3단계: Python 및 필수 도구 설치

```bash
# Python 및 pip 설치
sudo apt install python3.8 python3-pip python3-venv git -y

# tkinter 설치 (GUI를 위해 필요)
sudo apt install python3-tk -y

# 개발 도구 설치
sudo apt install build-essential -y
```

### 4단계: X Server 설정 (GUI 사용 시)

**Windows에서:**
1. [VcXsrv](https://sourceforge.net/projects/vcxsrv/) 다운로드 및 설치
2. XLaunch 실행:
   - "Multiple windows" 선택
   - "Start no client" 선택
   - "Disable access control" 체크
   - 완료

**WSL에서:**
```bash
# .bashrc 파일 편집
nano ~/.bashrc

# 파일 끝에 추가
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# 변경사항 적용
source ~/.bashrc
```

### 5단계: 프로젝트 설치

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 폴더 생성
mkdir projects
cd projects

# Git 클론
git clone https://github.com/ksw6895/stockscreener.git
cd stockscreener

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 6단계: 패키지 설치

```bash
# pip 업그레이드
pip install --upgrade pip

# requirements.txt가 있는 경우
pip install -r requirements.txt

# 또는 개별 설치
pip install aiohttp numpy openpyxl python-dotenv matplotlib
```

### 7단계: API 키 설정

```bash
# .env 파일 생성
nano .env

# 다음 내용 입력:
# FMP_API_KEY=your_actual_api_key_here
# Ctrl+X, Y, Enter로 저장

# 파일 확인
cat .env
```

### 8단계: 실행

```bash
# GUI 모드 (X Server 필요)
python gui.py

# CLI 모드
python stock_screener.py

# 백테스팅
python backtest.py --period 6m --investment 100000
```

---

## 📝 requirements.txt 파일 생성

프로젝트 루트에 `requirements.txt` 파일이 없다면 생성:

```txt
aiohttp>=3.8.0
numpy>=1.21.0
openpyxl>=3.0.9
python-dotenv>=0.19.0
matplotlib>=3.5.0
python-dateutil>=2.8.2
```

---

## 🔑 API 키 획득 방법

### Financial Modeling Prep API 키 구독

1. [Financial Modeling Prep](https://financialmodelingprep.com/) 웹사이트 방문
2. "Pricing" 메뉴 클릭
3. 적절한 플랜 선택 (최소 Starter 플랜 필요)
4. 가입 후 Dashboard에서 API 키 복사
5. `.env` 파일에 붙여넣기

**주의사항:**
- 무료 플랜은 하루 250 요청으로 제한되어 전체 기능 사용 불가
- 최소 Starter 플랜 ($19/월) 권장
- API 키는 절대 GitHub에 업로드하지 마세요

---

## 💻 사용 방법 (Usage)

### GUI 모드 사용법

1. GUI 실행:
```bash
python gui.py
```

2. 설정 조정:
   - Market Cap Range: 시가총액 범위 설정
   - ROE Criteria: ROE 기준 설정
   - Sector Filter: 금융 섹터 제외 옵션
   - Quality Score Threshold: 최소 품질 점수

3. "Run Screening" 버튼 클릭

4. 결과 확인:
   - 화면에 상위 10개 종목 표시
   - Excel 파일 자동 생성 (`screening_results_YYYYMMDD_HHMMSS.xlsx`)

### CLI 모드 사용법

```bash
# 기본 실행
python stock_screener.py

# 로그 레벨 설정
python stock_screener.py --log-level INFO

# 설정 파일 지정
python stock_screener.py --config custom_config.json
```

### 백테스팅 사용법

```bash
# 6개월 백테스트
python backtest.py --period 6m --investment 100000

# 1년 백테스트
python backtest.py --period 1y --investment 50000

# 3개월 백테스트
python backtest.py --period 3m
```

백테스팅 결과는 `backtest_results/` 폴더에 저장됩니다:
- `backtest_summary_*.txt`: 요약 리포트
- `individual_performance_*.png`: 개별 주식 성과 그래프
- `portfolio_performance_*.png`: 포트폴리오 성과 그래프
- `wealth_growth_*.png`: 자산 증가 그래프

---

## 🔧 문제 해결 (Troubleshooting)

### Windows 문제 해결

**문제: "python이 내부 또는 외부 명령... 으로 인식되지 않습니다"**
- 해결: Python을 PATH에 추가하거나 재설치

**문제: pip 명령어가 작동하지 않음**
```cmd
python -m pip install --upgrade pip
```

**문제: tkinter 모듈을 찾을 수 없음**
- Python 재설치 시 "tcl/tk and IDLE" 옵션 선택

### WSL 문제 해결

**문제: GUI가 표시되지 않음**
1. VcXsrv가 실행 중인지 확인
2. Windows 방화벽에서 VcXsrv 허용
3. DISPLAY 변수 확인:
```bash
echo $DISPLAY
```

**문제: Permission denied 오류**
```bash
chmod +x script_name.py
```

**문제: ModuleNotFoundError**
```bash
# 가상환경 활성화 확인
which python
# venv/bin/python이 표시되어야 함

# 패키지 재설치
pip install -r requirements.txt
```

### API 관련 문제

**문제: 429 Too Many Requests**
- API 요청 한도 초과
- 해결: 더 높은 플랜으로 업그레이드 또는 요청 간격 조정

**문제: Invalid API Key**
- `.env` 파일의 API 키 확인
- 키 앞뒤 공백 제거

---

## 📁 프로젝트 구조 (Project Structure)

```
stockscreener/
├── .env                    # API 키 (Git에 포함되지 않음)
├── .gitignore             # Git 제외 파일 목록
├── README.md              # 이 파일
├── requirements.txt       # Python 패키지 목록
├── config.json           # 설정 파일
├── gui.py                # GUI 인터페이스
├── stock_screener.py     # 메인 스크리닝 로직
├── backtest.py           # 백테스팅 기능
├── api_client.py         # API 통신
├── config.py             # 설정 관리
├── models.py             # 데이터 모델
├── quality_scorer.py     # 품질 점수 계산
├── data_processing.py    # 데이터 처리
├── output_formatter.py   # 출력 포맷팅
├── src/                  # 소스 코드
│   ├── analyzers/        # 분석 모듈
│   │   ├── growth_analyzer.py
│   │   ├── risk_analyzer.py
│   │   ├── valuation_analyzer.py
│   │   └── sentiment_analyzer.py
│   └── data_fetcher.py  # 데이터 수집
└── backtest_results/     # 백테스트 결과 (자동 생성)
```

---

## 📊 출력 예시 (Output Examples)

### Excel 리포트 내용
- **Summary Sheet**: 전체 종목 순위
- **Top Stocks**: 상위 10개 종목 상세 분석
- **Sector Analysis**: 섹터별 분포 차트
- **Growth Metrics**: 성장 지표 비교
- **Risk Metrics**: 리스크 지표 분석
- **Valuation**: 밸류에이션 비교

### 백테스팅 리포트
```
Backtest Summary Report
=====================
Backtest Date: 2024-01-01
Initial Investment: $100,000

Portfolio Performance:
Overall Return: 25.3%
Sharpe Ratio: 1.245
Maximum Drawdown: -8.7%

Benchmark Comparison:
S&P 500 Return: 18.2%
Alpha: +7.1%
```

---

## ⚠️ 주의사항 (Important Notes)

1. **API 키 보안**
   - `.env` 파일을 절대 공유하지 마세요
   - GitHub에 업로드하지 마세요

2. **투자 책임**
   - 이 도구는 교육 및 연구 목적입니다
   - 실제 투자 결정 전 전문가 상담 필요

3. **API 제한**
   - 분당 300 요청 제한
   - 동시 연결 5개로 제한

4. **데이터 정확성**
   - 실시간 데이터가 아닌 일일 종가 기준
   - 과거 데이터는 조정 종가(adjusted close) 사용

---

## 🤝 기여 방법 (Contributing)

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📜 라이선스 (License)

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 📞 지원 (Support)

문제 발생 시:
1. [Issues](https://github.com/ksw6895/stockscreener/issues) 페이지에 문의
2. 자세한 오류 메시지와 함께 제보

---

## 🚦 빠른 시작 체크리스트

- [ ] Python 3.8+ 설치 확인
- [ ] Git 설치 (선택사항)
- [ ] 프로젝트 다운로드/클론
- [ ] 가상환경 생성 및 활성화
- [ ] 필수 패키지 설치
- [ ] FMP API 키 획득
- [ ] `.env` 파일 생성 및 API 키 입력
- [ ] GUI 또는 CLI로 첫 실행
- [ ] 백테스팅 실행 (선택사항)

모든 단계를 완료하면 성공적으로 실행됩니다! 🎉