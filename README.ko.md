# Enhanced NASDAQ 주식 스크리너 (고급형 나스닥 주식 분석 도구)

**전문가 수준의 주식 분석을 당신의 컴퓨터에서!**

Enhanced NASDAQ Stock Screener는 복잡한 금융 데이터를 분석하여 나스닥 시장에서 잠재력 높은 성장주를 발굴하는 강력한 자동화 도구입니다. 이 시스템은 수십 개의 재무 지표, 성장성, 리스크, 가치 평가, 시장 심리를 종합하여 각 주식의 품질을 점수로 평가하고, 상세한 분석 리포트를 제공합니다.

[English Readme](README.md)

## ✨ 주요 기능

- **고급 재무 분석**: 20개 이상의 재무 지표를 활용한 심층 분석.
- **섹터별 상대 평가**: 동일 섹터 내 경쟁사 대비 상대적 성과를 측정하여 객관적인 평가 제공.
- **성장 품질 평가**: 매출, 이익, 현금흐름 성장의 규모, 일관성, 지속가능성을 다각도로 분석.
- **리스크 프로파일링**: 부채 수준, 마진 안정성, 현금흐름의 질을 평가하여 재무 안정성 검토.
- **가치 평가 분석**: 전통적인 가치 지표(PER, PBR)와 성장성을 고려한 가치 지표를 함께 분석.
- **시장 심리 분석**: 내부자 거래, 어닝 서프라이즈, 소셜 미디어 동향을 분석하여 시장의 기대를 측정.
- **상세 리포트**: 분석 결과를 텍스트 및 Excel 형식의 종합 리포트로 제공.
- **사용자 친화적 GUI**: 직관적인 그래픽 인터페이스를 통해 손쉽게 스크리너 설정 및 실행.
- **안전한 API 키 관리**: `.env` 파일을 사용하여 API 키를 안전하게 보관.

## 🚀 설치 및 설정

### 사전 요구사항

- Python 3.8 이상
- [Financial Modeling Prep (FMP)](https://financialmodelingprep.com/) API 유료 구독 (무료 버전은 요청 제한으로 인해 전체 기능 사용 불가)
- 필요한 Python 패키지:
  - `aiohttp`
  - `numpy`
  - `openpyxl`
  - `python-dotenv`
  - `matplotlib`
  - `tkinter` (Python 설치 시 대부분 포함)

### 설정 절차

1.  **리포지토리 복제(Clone)**:
    ```bash
    git clone https://github.com/ksw6895/stockscreener.git
    cd stockscreener
    ```

2.  **필요한 패키지 설치**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **.env 파일 생성 및 API 키 설정**:
    프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 FMP API 키를 추가합니다.
    ```
    # Financial Modeling Prep API Key
    FMP_API_KEY=여기에_당신의_API_키를_입력하세요
    ```

4.  **(선택) 상세 설정 변경**:
    `enhanced_config.json` 파일에서 스크리닝 기준(시가총액, 성장률 목표 등)을 필요에 맞게 수정할 수 있습니다.

## 💻 사용 방법

### GUI 모드 (그래픽 인터페이스)

직관적인 GUI를 통해 스크리너를 실행하려면 다음 명령어를 입력하세요.

```bash
python gui.py
```

GUI에서는 각 탭을 통해 필터, 성장성, 리스크, 가치평가 등의 기준을 세밀하게 조정한 후 "Start Screening" 버튼을 눌러 분석을 시작할 수 있습니다.

### CLI 모드 (명령줄)

명령줄에서 직접 스크리너를 실행하려면 다음 명령어를 사용하세요.

```bash
python stock_screener.py
```

이 모드는 `enhanced_config.json` 파일에 정의된 설정을 기반으로 실행됩니다.

### 백테스팅 모드

과거 특정 시점에서 스크리너를 실행했을 경우의 성과를 검증하려면 다음 명령어를 사용하세요.

```bash
python backtest.py
```

## ⚙️ 설정 (Configuration)

이 애플리케이션의 모든 설정은 `enhanced_config.json` 파일에서 관리됩니다. GUI를 통해 설정을 변경하고 저장할 수도 있습니다.

주요 설정 항목:

-   `initial_filters`: 초기 필터링 조건 (예: 시가총액 범위, 특정 섹터 제외).
-   `growth_quality`: 성장성 평가 기준 (예: 최소 연평균 성장률 목표).
-   `risk_quality`: 리스크 평가 기준 (예: 최대 부채 비율).
-   `valuation`: 가치 평가 기준 (예: 최대 PER, PBR).
-   `scoring`: 최종 품질 점수 계산을 위한 각 부문별 가중치.
-   `output`: 결과 리포트의 형식(text, excel) 및 파일명 설정.
-   `sector_benchmarks`: 각 산업 섹터별 벤치마크 값.

## 📂 파일 구조

```
├── analyzers/              # 재무 분석 모듈 (성장성, 리스크, 가치, 심리)
├── backtest_results/       # 백테스팅 결과 파일 저장 위치
├── api_client.py           # API 통신 관리
├── backtest.py             # 백테스팅 기능
├── config.py               # 설정 관리
├── data_processing.py      # 데이터 전처리
├── enhanced_config.json    # 핵심 설정 파일
├── gui.py                  # 그래픽 사용자 인터페이스
├── models.py               # 데이터 모델 (타입 정의)
├── output.py               # 리포트 생성
├── quality_scorer.py       # 종합 품질 점수 계산
└── stock_screener.py       # 메인 스크리닝 로직
```

## 🔑 API 요구사항

이 애플리케이션은 **[Financial Modeling Prep API](https://financialmodelingprep.com/)의 유료 구독이 필요합니다.** 무료 버전은 API 요청 횟수 제한이 있어 수천 개의 주식을 분석하는 데 충분하지 않습니다.

## 📊 출력 결과 예시

스크리너는 다음과 같은 상세 분석 리포트를 생성합니다.

1.  **요약 리포트**: 모든 기준을 통과한 주식들을 품질 점수 순으로 정렬하여 보여줍니다.
2.  **상세 분석**: 각 주식에 대한 세부 지표 (성장률, 리스크, 가치평가 점수 등)를 제공합니다.
3.  **Excel 리포트**: 다양한 차트와 시각화 자료를 포함하여 심층적인 분석을 돕습니다.
4.  **백테스팅 결과**: 포트폴리오의 과거 성과 분석 및 벤치마크(나스닥 지수)와의 비교 결과를 제공합니다.

## 🤝 기여하기 (Contributing)

이 프로젝트에 기여하고 싶으시다면 다음 절차를 따라주세요.

1.  리포지토리를 Fork 하세요.
2.  새로운 기능 브랜치를 만드세요 (`git checkout -b feature/새로운-기능`).
3.  변경사항을 커밋하세요 (`git commit -m '새로운 기능 추가'`).
4.  브랜치에 Push 하세요 (`git push origin feature/새로운-기능`).
5.  Pull Request를 열어주세요.

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

## ⚠️ 면책 조항

이 소프트웨어는 교육 및 연구 목적으로만 제공됩니다. 제공되는 정보는 금융 자문으로 간주되어서는 안 됩니다. 투자 결정을 내리기 전에는 반드시 자격을 갖춘 금융 전문가와 상담하세요.
