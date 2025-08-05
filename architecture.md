# Architecture Documentation / 아키텍처 문서

## 개요 / Overview

### 일반 사용자를 위한 설명 / For General Users

#### 한국어
Enhanced NASDAQ Stock Screener는 나스닥 상장 주식들을 자동으로 분석하여 투자 가치가 높은 종목을 찾아내는 프로그램입니다. 마치 수천 명의 애널리스트가 동시에 모든 주식을 분석하는 것과 같은 효과를 제공합니다. 이 프로그램은 기업의 재무 상태, 성장성, 리스크, 가치 평가 등을 종합적으로 검토하여 0에서 1 사이의 품질 점수를 계산합니다. 높은 점수일수록 더 좋은 투자 기회를 의미합니다.

#### English
The Enhanced NASDAQ Stock Screener is a program that automatically analyzes NASDAQ-listed stocks to identify those with high investment value. It works like having thousands of analysts simultaneously analyzing all stocks. The program comprehensively evaluates companies' financial health, growth potential, risk levels, and valuations to calculate a quality score between 0 and 1. A higher score indicates a better investment opportunity.

### 프로그래머를 위한 설명 / For Programmers

#### 한국어
이 시스템은 Python 기반의 비동기 주식 스크리닝 애플리케이션으로, Financial Modeling Prep API를 통해 실시간 금융 데이터를 수집하고 분석합니다. asyncio를 활용한 동시성 처리로 수천 개의 주식을 효율적으로 분석하며, 섹터별 상대 평가를 통해 객관적인 투자 지표를 제공합니다. 모듈화된 아키텍처로 설계되어 성장성, 리스크, 가치평가, 시장 심리 분석기가 독립적으로 작동하며, 최종적으로 가중치 기반 품질 점수를 산출합니다.

#### English
This system is a Python-based asynchronous stock screening application that collects and analyzes real-time financial data through the Financial Modeling Prep API. Using asyncio for concurrency, it efficiently analyzes thousands of stocks and provides objective investment metrics through sector-relative evaluation. Designed with a modular architecture, growth, risk, valuation, and sentiment analyzers operate independently, ultimately producing a weighted quality score.

## 시스템 아키텍처 / System Architecture

```mermaid
graph TB
    subgraph "사용자 인터페이스 / User Interface"
        GUI[GUI<br/>tkinter 기반]
        CLI[CLI<br/>명령줄 인터페이스]
    end
    
    subgraph "핵심 엔진 / Core Engine"
        SS[Stock Screener<br/>주식 스크리너]
        QS[Quality Scorer<br/>품질 평가기]
    end
    
    subgraph "분석 모듈 / Analysis Modules"
        GA[Growth Analyzer<br/>성장성 분석기]
        RA[Risk Analyzer<br/>리스크 분석기]
        VA[Valuation Analyzer<br/>가치 평가기]
        SA[Sentiment Analyzer<br/>시장 심리 분석기]
    end
    
    subgraph "데이터 계층 / Data Layer"
        API[API Client<br/>비동기 API 클라이언트]
        DP[Data Processing<br/>데이터 처리]
        CACHE[Cache<br/>캐시]
    end
    
    subgraph "외부 시스템 / External Systems"
        FMP[Financial Modeling Prep API]
    end
    
    subgraph "출력 / Output"
        EXCEL[Excel Report<br/>엑셀 보고서]
        TXT[Text Report<br/>텍스트 보고서]
    end
    
    GUI --> SS
    CLI --> SS
    SS --> QS
    QS --> GA
    QS --> RA
    QS --> VA
    QS --> SA
    SS --> API
    API --> FMP
    API --> CACHE
    SS --> DP
    SS --> EXCEL
    SS --> TXT
    
    style GUI fill:#e1f5fe
    style CLI fill:#e1f5fe
    style SS fill:#fff3e0
    style QS fill:#fff3e0
    style GA fill:#f3e5f5
    style RA fill:#f3e5f5
    style VA fill:#f3e5f5
    style SA fill:#f3e5f5
    style API fill:#e8f5e9
    style DP fill:#e8f5e9
    style FMP fill:#ffebee
```

## 데이터 흐름 / Data Flow

```mermaid
sequenceDiagram
    participant User as 사용자/User
    participant GUI as GUI/CLI
    participant Screener as Stock Screener
    participant API as API Client
    participant FMP as FMP API
    participant Analyzers as 분석기들/Analyzers
    participant Scorer as Quality Scorer
    participant Output as 출력/Output
    
    User->>GUI: 스크리닝 시작/Start Screening
    GUI->>Screener: 스크리닝 요청/Request Screening
    
    rect rgb(255, 243, 224)
        Note over Screener,FMP: 1단계: 초기 필터링/Initial Filtering
        Screener->>API: NASDAQ 종목 목록 요청/Request NASDAQ List
        API->>FMP: GET /symbol/NASDAQ
        FMP-->>API: 종목 목록/Stock List
        API-->>Screener: ~3000개 종목/~3000 Stocks
        
        Screener->>API: 기업 프로필 요청/Request Company Profiles
        API->>FMP: GET /profile (배치/Batch)
        FMP-->>API: 프로필 데이터/Profile Data
        API-->>Screener: 시가총액, 섹터 정보/Market Cap, Sector
        
        Note over Screener: 시가총액 필터 적용/Apply Market Cap Filter<br/>$10B - $20B
        Note over Screener: ROE 필터 적용/Apply ROE Filter<br/>3년 평균 15% 이상/3-year avg > 15%
    end
    
    rect rgb(240, 248, 255)
        Note over Screener,Analyzers: 2단계: 상세 분석/Detailed Analysis
        loop 각 통과 종목에 대해/For Each Passing Stock
            Screener->>API: 재무 데이터 요청/Request Financial Data
            API->>FMP: 병렬 API 호출/Parallel API Calls
            FMP-->>API: 재무제표, 비율, 지표/Statements, Ratios, Metrics
            API-->>Screener: 종합 데이터/Comprehensive Data
            
            Screener->>Scorer: 품질 점수 계산/Calculate Quality Score
            Scorer->>Analyzers: 각 분석기 호출/Call Each Analyzer
            
            Note over Analyzers: 성장성 40%/Growth 40%<br/>리스크 25%/Risk 25%<br/>가치평가 20%/Valuation 20%<br/>시장심리 15%/Sentiment 15%
            
            Analyzers-->>Scorer: 부문별 점수/Component Scores
            Scorer-->>Screener: 최종 품질 점수/Final Quality Score
        end
    end
    
    rect rgb(232, 245, 233)
        Note over Screener,Output: 3단계: 결과 생성/Result Generation
        Screener->>Screener: 품질 점수 정규화/Normalize Scores
        Screener->>Screener: 섹터별 백분위 계산/Calculate Sector Percentiles
        Screener->>Output: 보고서 생성/Generate Reports
        Output-->>User: Excel/Text 보고서/Reports
    end
```

## 스크리닝 기준 상세 / Detailed Screening Criteria

### 초기 필터 / Initial Filters

```mermaid
flowchart LR
    subgraph "시가총액 필터 / Market Cap Filter"
        MC[시가총액/Market Cap]
        MC --> MC1[최소/Min: $10B]
        MC --> MC2[최대/Max: $20B]
    end
    
    subgraph "ROE 필터 / ROE Filter"
        ROE[자기자본이익률/ROE]
        ROE --> ROE1[3년 평균/3-year avg ≥ 15%]
        ROE --> ROE2[매년 최소/Each year ≥ 10%]
    end
    
    subgraph "섹터 필터 / Sector Filter"
        SECTOR[섹터 제외/Sector Exclusion]
        SECTOR --> SF[금융 섹터 제외 옵션<br/>Optional Financial Exclusion]
    end
```

### 성장성 평가 (40% 가중치) / Growth Quality Assessment (40% Weight)

#### 한국어 설명
성장성 평가는 기업의 미래 성장 잠재력을 측정합니다. 매출, 주당순이익(EPS), 잉여현금흐름(FCF)의 연평균 성장률(CAGR)을 계산하고, 성장의 일관성과 지속가능성을 평가합니다.

#### English Explanation
Growth assessment measures a company's future growth potential. It calculates the Compound Annual Growth Rate (CAGR) for revenue, EPS, and FCF, while evaluating growth consistency and sustainability.

```mermaid
graph TD
    subgraph "성장성 점수 계산 / Growth Score Calculation"
        GS[성장성 점수/Growth Score]
        
        MAG[크기 점수/Magnitude Score - 35%]
        CON[일관성 점수/Consistency Score - 35%]
        SUS[지속가능성 점수/Sustainability Score - 30%]
        
        GS --> MAG
        GS --> CON
        GS --> SUS
        
        MAG --> REV_CAGR[매출 CAGR/Revenue CAGR<br/>목표/Target: 20%]
        MAG --> EPS_CAGR[EPS CAGR<br/>목표/Target: 15%]
        MAG --> FCF_CAGR[FCF CAGR<br/>목표/Target: 15%]
        
        CON --> YOY[전년대비 성장률 변동성<br/>Year-over-Year Volatility]
        CON --> TREND[성장 추세 분석<br/>Growth Trend Analysis]
        
        SUS --> RD[R&D 투자 추세<br/>R&D Investment Trend]
        SUS --> CAPEX[자본효율성<br/>Capital Efficiency]
        SUS --> MARGIN[마진 안정성<br/>Margin Stability]
    end
```

#### 성장성 점수 계산 공식 / Growth Score Formula

```
크기 점수 (Magnitude Score):
- 실제 CAGR ≤ 0: 점수 = 0
- 실제 CAGR ≥ 목표 × 2: 점수 = 1.0
- 그 외: 점수 = 0.5 × (1 + log(실제/목표) / log(2))

일관성 점수 (Consistency Score):
- 변동계수(CV) = 표준편차 / 평균
- 점수 = 1 / (1 + CV)
- 모든 기간 양의 성장 시 +0.2 보너스

최종 성장성 점수 = 0.35 × 크기 + 0.35 × 일관성 + 0.30 × 지속가능성
```

### 리스크 평가 (25% 가중치) / Risk Assessment (25% Weight)

#### 한국어 설명
리스크 평가는 기업의 재무 안정성과 위험 요소를 측정합니다. 부채 수준, 이자보상배율, 운전자본, 현금흐름 품질을 종합적으로 평가합니다.

#### English Explanation
Risk assessment measures a company's financial stability and risk factors. It comprehensively evaluates debt levels, interest coverage, working capital, and cash flow quality.

```mermaid
graph TD
    subgraph "리스크 점수 계산 / Risk Score Calculation"
        RS[리스크 점수/Risk Score]
        
        DEBT[부채 지표/Debt Metrics - 30%]
        WC[운전자본/Working Capital - 25%]
        MS[마진 안정성/Margin Stability - 25%]
        CF[현금흐름 품질/Cash Flow Quality - 20%]
        
        RS --> DEBT
        RS --> WC
        RS --> MS
        RS --> CF
        
        DEBT --> DE[부채비율/Debt-to-Equity<br/>섹터별 기준/Sector-specific]
        DEBT --> IC[이자보상배율/Interest Coverage<br/>최소/Min: 3.0]
        DEBT --> DEBITDA[부채/EBITDA<br/>최대/Max: 5.0]
        
        WC --> WCP[운전자본 양수 여부<br/>Positive Working Capital]
        WC --> WCT[운전자본 추세<br/>Working Capital Trend]
        
        MS --> GM[매출총이익률 안정성<br/>Gross Margin Stability]
        MS --> OM[영업이익률 안정성<br/>Operating Margin Stability]
        
        CF --> OCFNI[영업현금흐름/순이익<br/>OCF/Net Income<br/>이상적/Ideal: 0.9-1.2]
        CF --> FCFP[FCF 양수 여부<br/>Positive FCF]
    end
```

#### 리스크 점수 계산 기준 / Risk Score Calculation Criteria

```
부채 점수 (Debt Score):
- 부채비율 = 0: 점수 = 1.0
- 부채비율 ≥ 섹터 최대: 점수 = 0.0
- 이자보상배율 < 1.5: 점수 = 0.0 (위험)
- 이자보상배율 ≥ 10: 점수 = 1.0 (우수)

현금흐름 품질 (Cash Flow Quality):
- OCF/NI 비율 0.9-1.2: 점수 = 1.0 (이상적)
- OCF/NI 비율 < 0.7: 점수 = 0.3 (수익 품질 의심)
- FCF 3년 연속 양수: 보너스 점수
```

### 가치평가 (20% 가중치) / Valuation (20% Weight)

#### 한국어 설명
가치평가는 현재 주가가 기업의 실제 가치 대비 적정한지 평가합니다. PER, PBR, FCF 수익률, 성장 대비 가치(PEG)를 분석합니다.

#### English Explanation
Valuation assesses whether the current stock price is appropriate relative to the company's actual value. It analyzes P/E ratio, P/B ratio, FCF yield, and PEG ratio.

```mermaid
graph TD
    subgraph "가치평가 점수 / Valuation Score"
        VS[가치평가 점수/Valuation Score]
        
        PER[PER - 30%]
        PBR[PBR - 20%]
        FCFY[FCF 수익률/FCF Yield - 30%]
        PEG[PEG 비율/PEG Ratio - 20%]
        
        VS --> PER
        VS --> PBR
        VS --> FCFY
        VS --> PEG
        
        PER --> PERM[섹터별 최대 PER<br/>Sector Max P/E<br/>기술주/Tech: 30<br/>금융/Financial: 20]
        
        PBR --> PBRM[섹터별 최대 PBR<br/>Sector Max P/B<br/>기술주/Tech: 5.0<br/>금융/Financial: 2.0]
        
        FCFY --> FCFYM[FCF/시가총액<br/>FCF/Market Cap<br/>목표/Target ≥ 4%]
        
        PEG --> PEGM[PER/(성장률×100)<br/>P/E/(Growth×100)<br/>이상적/Ideal < 1.0]
    end
```

### 시장 심리 (15% 가중치) / Market Sentiment (15% Weight)

#### 한국어 설명
시장 심리는 내부자 거래, 실적 서프라이즈, 소셜 미디어 감성을 분석하여 시장의 기업에 대한 인식을 평가합니다.

#### English Explanation
Market sentiment evaluates market perception of the company by analyzing insider trading, earnings surprises, and social media sentiment.

```mermaid
graph TD
    subgraph "시장 심리 점수 / Sentiment Score"
        SS[시장 심리 점수/Sentiment Score]
        
        IT[내부자 거래/Insider Trading - 40%]
        ES[실적 서프라이즈/Earnings Surprise - 35%]
        SOC[소셜 감성/Social Sentiment - 25%]
        
        SS --> IT
        SS --> ES
        SS --> SOC
        
        IT --> BUYSELL[매수/매도 비율<br/>Buy/Sell Ratio]
        IT --> VALUE[거래 금액 비율<br/>Transaction Value Ratio]
        
        ES --> EPSS[EPS 서프라이즈<br/>EPS Surprise %]
        ES --> REVS[매출 서프라이즈<br/>Revenue Surprise %]
        
        SOC --> BULL[강세 비율/Bullish %]
        SOC --> CHANGE[감성 변화/Sentiment Change]
    end
```

## 품질 점수 계산 알고리즘 / Quality Score Calculation Algorithm

```mermaid
flowchart TD
    subgraph "최종 품질 점수 계산 / Final Quality Score Calculation"
        START[시작/Start]
        
        G[성장성 점수/Growth Score<br/>가중치/Weight: 40%]
        R[리스크 점수/Risk Score<br/>가중치/Weight: 25%]
        V[가치평가 점수/Valuation Score<br/>가중치/Weight: 20%]
        S[시장심리 점수/Sentiment Score<br/>가중치/Weight: 15%]
        
        BASE[기본 품질 점수/Base Quality Score<br/>= 0.40×G + 0.25×R + 0.20×V + 0.15×S]
        
        COHERENCE[일관성 승수/Coherence Multiplier<br/>범위/Range: 0.9 - 1.15]
        
        FINAL[최종 품질 점수/Final Quality Score<br/>= Base × Coherence]
        
        NORM[정규화/Normalization<br/>0-1 범위/0-1 Range]
        
        PERCENTILE[섹터 백분위/Sector Percentile<br/>동일 섹터 내 순위/Rank within sector]
        
        OUTPUT[최종 출력/Final Output]
        
        START --> G
        START --> R
        START --> V
        START --> S
        
        G --> BASE
        R --> BASE
        V --> BASE
        S --> BASE
        
        BASE --> COHERENCE
        COHERENCE --> FINAL
        FINAL --> NORM
        NORM --> PERCENTILE
        PERCENTILE --> OUTPUT
    end
```

### 일관성 승수 계산 / Coherence Multiplier Calculation

#### 한국어 설명
일관성 승수는 각 평가 요소들이 서로 얼마나 조화를 이루는지 측정합니다. 예를 들어, 높은 성장률과 높은 FCF가 함께 나타나면 더 높은 점수를 받습니다.

#### English Explanation
The coherence multiplier measures how well different evaluation elements harmonize with each other. For example, high growth rate combined with high FCF receives a higher score.

일관성 체크 항목 / Coherence Check Items:
1. 매출 성장과 FCF 성장 일치 / Revenue and FCF growth alignment
2. 마진 안정성과 높은 ROE / Margin stability with high ROE
3. 성장률과 밸류에이션 균형 / Growth and valuation balance
4. 낮은 부채와 강한 현금흐름 / Low debt with strong cash flow
5. 매출과 수익의 일관성 / Revenue and earnings consistency

## 섹터별 벤치마크 / Sector-Specific Benchmarks

### 11개 섹터 기준 / 11 Sector Standards

```mermaid
graph LR
    subgraph "기술/Technology"
        T1[매출 성장/Revenue: 15%]
        T2[PER 최대/Max P/E: 30]
        T3[부채비율/D/E Max: 1.5]
    end
    
    subgraph "헬스케어/Healthcare"
        H1[매출 성장/Revenue: 8%]
        H2[PER 최대/Max P/E: 28]
        H3[부채비율/D/E Max: 1.2]
    end
    
    subgraph "금융/Financial"
        F1[매출 성장/Revenue: 6%]
        F2[PER 최대/Max P/E: 20]
        F3[부채비율/D/E Max: 5.0]
    end
    
    subgraph "소비재/Consumer"
        C1[매출 성장/Revenue: 10%]
        C2[PER 최대/Max P/E: 25]
        C3[부채비율/D/E Max: 2.0]
    end
```

각 섹터별로 다른 기준을 적용하여 공정한 비교가 가능합니다. 예를 들어, 기술주는 높은 성장률이 기대되지만, 유틸리티 섹터는 안정성이 더 중요합니다.

## API 통합 및 속도 제한 / API Integration and Rate Limiting

### API 요청 흐름 / API Request Flow

```mermaid
sequenceDiagram
    participant Client as API Client
    participant Semaphore as 세마포어/Semaphore<br/>(동시 5개/5 Concurrent)
    participant RateLimit as 속도 제한/Rate Limiter<br/>(300/분/min)
    participant FMP as FMP API
    participant Cache as 캐시/Cache
    
    Client->>Semaphore: 요청 허가/Request Permission
    Semaphore->>RateLimit: 속도 체크/Check Rate
    
    alt 캐시 적중/Cache Hit
        RateLimit->>Cache: 캐시 확인/Check Cache
        Cache-->>Client: 캐시 데이터/Cached Data
    else 캐시 미스/Cache Miss
        RateLimit->>RateLimit: 60ms 대기/Wait 60ms
        RateLimit->>FMP: API 호출/API Call
        FMP-->>RateLimit: 응답/Response
        RateLimit->>Cache: 캐시 저장/Store Cache
        RateLimit-->>Client: 데이터/Data
    end
    
    Note over RateLimit,FMP: 재시도 로직/Retry Logic<br/>429 에러 시 지수 백오프<br/>Exponential backoff on 429
```

### API 엔드포인트 / API Endpoints

주요 사용 엔드포인트 / Main Endpoints Used:
- `/symbol/NASDAQ` - NASDAQ 종목 목록 / NASDAQ symbol list
- `/profile` - 기업 프로필 (배치 100개) / Company profiles (batch 100)
- `/income-statement` - 손익계산서 / Income statements
- `/cash-flow-statement` - 현금흐름표 / Cash flow statements
- `/balance-sheet-statement` - 재무상태표 / Balance sheets
- `/ratios` - 재무 비율 / Financial ratios
- `/key-metrics` - 핵심 지표 / Key metrics
- `/insider-trading` - 내부자 거래 / Insider trading
- `/social-sentiments` - 소셜 감성 / Social sentiment

## 사용자 인터페이스 / User Interfaces

### GUI 인터페이스 / GUI Interface

```mermaid
graph TD
    subgraph "GUI 구조 / GUI Structure"
        MAIN[메인 윈도우/Main Window]
        
        TABS[탭 인터페이스/Tab Interface]
        MAIN --> TABS
        
        TABS --> FILTER[초기 필터/Initial Filters<br/>시가총액, ROE/Market Cap, ROE]
        TABS --> GROWTH[성장 설정/Growth Settings<br/>CAGR 목표치/CAGR Targets]
        TABS --> RISK[리스크 설정/Risk Settings<br/>부채 한도/Debt Limits]
        TABS --> VAL[가치평가 설정/Valuation Settings<br/>PER, PBR 한도/P/E, P/B Limits]
        TABS --> OUTPUT[출력 설정/Output Settings<br/>형식, 파일명/Format, Filename]
        TABS --> LOG[실시간 로그/Real-time Log]
        TABS --> BACKTEST[백테스팅/Backtesting<br/>3개월, 6개월, 1년/3M, 6M, 1Y]
        
        CONTROL[제어 버튼/Control Buttons]
        MAIN --> CONTROL
        CONTROL --> START[스크리닝 시작/Start Screening]
        CONTROL --> SAVE[설정 저장/Save Settings]
        CONTROL --> LOAD[설정 불러오기/Load Settings]
    end
```

### CLI 인터페이스 / CLI Interface

명령줄 사용법 / Command Line Usage:
```bash
# 기본 실행 / Basic execution
python stock_screener.py

# GUI 실행 / Run GUI
python gui.py

# 백테스팅 실행 / Run backtesting
python backtest.py
```

## 출력 형식 / Output Formats

### Excel 보고서 구조 / Excel Report Structure

```mermaid
graph TD
    subgraph "Excel 보고서 / Excel Report"
        SUMMARY[요약 시트/Summary Sheet<br/>상위 종목, 품질 점수/Top Stocks, Quality Scores]
        
        DETAILED[상세 시트/Detailed Sheet<br/>모든 지표, 분석 결과/All Metrics, Analysis Results]
        
        CHARTS[차트 시트/Charts Sheet<br/>자동 생성 차트/Auto-generated Charts]
        
        SECTOR[섹터 분석/Sector Analysis<br/>섹터별 비교/Sector Comparison]
        
        SUMMARY --> DETAILED
        DETAILED --> CHARTS
        CHARTS --> SECTOR
    end
```

포함되는 차트 / Included Charts:
1. 품질 점수 분포 / Quality Score Distribution
2. 섹터별 성과 / Performance by Sector
3. 성장률 vs 밸류에이션 / Growth vs Valuation
4. 리스크-수익 산점도 / Risk-Return Scatter Plot

## 백테스팅 방법론 / Backtesting Methodology

### 백테스팅 프로세스 / Backtesting Process

```mermaid
flowchart LR
    subgraph "백테스팅 워크플로우 / Backtesting Workflow"
        SELECT[기간 선택/Select Period<br/>3개월, 6개월, 1년/3M, 6M, 1Y]
        
        HISTORICAL[과거 시점 스크리닝<br/>Historical Screening<br/>과거 데이터로 분석/Analyze with past data]
        
        TRACK[성과 추적/Track Performance<br/>현재까지 수익률/Returns to present]
        
        COMPARE[벤치마크 비교/Compare Benchmark<br/>NASDAQ 지수 대비/vs NASDAQ Index]
        
        VISUAL[시각화/Visualization<br/>누적 수익률 차트/Cumulative Return Chart]
        
        SELECT --> HISTORICAL
        HISTORICAL --> TRACK
        TRACK --> COMPARE
        COMPARE --> VISUAL
    end
```

### 백테스팅 결과 해석 / Interpreting Backtest Results

#### 한국어
백테스팅은 과거 특정 시점에 이 스크리너를 사용했다면 어떤 결과를 얻었을지 보여줍니다. 선택된 종목들의 실제 수익률을 NASDAQ 지수와 비교하여 스크리너의 효과를 검증합니다.

#### English
Backtesting shows what results would have been achieved if this screener had been used at a specific point in the past. It validates the screener's effectiveness by comparing the actual returns of selected stocks with the NASDAQ index.

## 설정 옵션 / Configuration Options

### enhanced_config.json 주요 설정 / Key Settings

```json
{
    "초기 필터 / Initial Filters": {
        "market_cap_min": 10000000000,  // $10B
        "market_cap_max": 20000000000,  // $20B
        "roe": {
            "min_avg": 0.15,      // 15% 평균
            "min_each_year": 0.10, // 10% 매년
            "years": 3             // 3년 기준
        }
    },
    
    "점수 가중치 / Score Weights": {
        "growth_quality": 0.40,    // 40%
        "risk_quality": 0.25,      // 25%
        "valuation": 0.20,         // 20%
        "sentiment": 0.15          // 15%
    },
    
    "동시성 설정 / Concurrency": {
        "max_workers": 5,          // 동시 작업 수
        "request_delay": 0.06,     // 60ms 지연
        "max_retries": 3           // 최대 재시도
    }
}
```

## 성능 최적화 / Performance Optimization

### 최적화 기법 / Optimization Techniques

```mermaid
graph TD
    subgraph "성능 최적화 전략 / Performance Optimization Strategy"
        ASYNC[비동기 처리/Async Processing<br/>asyncio 활용/Using asyncio]
        
        BATCH[배치 처리/Batch Processing<br/>100개 단위 API 호출/100-unit API calls]
        
        CACHE[캐싱/Caching<br/>섹터 데이터 캐시/Sector data cache]
        
        POOL[연결 풀링/Connection Pooling<br/>aiohttp TCPConnector]
        
        LIMIT[동시성 제한/Concurrency Limiting<br/>세마포어 5개/Semaphore 5]
        
        ASYNC --> BATCH
        BATCH --> CACHE
        CACHE --> POOL
        POOL --> LIMIT
    end
```

### 처리 시간 / Processing Time

일반적인 처리 시간 / Typical Processing Times:
- 초기 필터링: ~5초 / Initial filtering: ~5 seconds
- 상세 분석 (100개 종목): ~60초 / Detailed analysis (100 stocks): ~60 seconds
- 보고서 생성: ~5초 / Report generation: ~5 seconds
- 전체 프로세스: ~70-90초 / Total process: ~70-90 seconds

## 확장 가능성 / Scalability and Extensibility

### 향후 개선 방향 / Future Improvements

#### 한국어
1. **머신러닝 통합**: 과거 데이터를 학습하여 예측 정확도 향상
2. **실시간 모니터링**: 선택된 종목의 실시간 추적 및 알림
3. **포트폴리오 최적화**: 현대 포트폴리오 이론 적용
4. **글로벌 시장 확장**: NASDAQ 외 다른 거래소 지원
5. **사용자 맞춤 전략**: 개인 투자 성향에 따른 맞춤 분석

#### English
1. **Machine Learning Integration**: Improve prediction accuracy by learning from historical data
2. **Real-time Monitoring**: Real-time tracking and alerts for selected stocks
3. **Portfolio Optimization**: Apply Modern Portfolio Theory
4. **Global Market Expansion**: Support exchanges beyond NASDAQ
5. **Custom User Strategies**: Personalized analysis based on investment preferences

## 보안 고려사항 / Security Considerations

### API 키 관리 / API Key Management

```mermaid
graph LR
    subgraph "API 키 보안 / API Key Security"
        ENV[.env 파일/File]
        ENV --> GITIGNORE[.gitignore 등록<br/>Added to .gitignore]
        
        ENV --> CONFIG[Config Manager]
        CONFIG --> VALIDATE[유효성 검증<br/>Validation]
        VALIDATE --> USE[API 사용<br/>API Usage]
        
        style ENV fill:#ffebee
        style GITIGNORE fill:#e8f5e9
    end
```

보안 모범 사례 / Security Best Practices:
1. API 키를 코드에 하드코딩하지 않음 / Never hardcode API keys
2. .env 파일 사용 및 버전 관리 제외 / Use .env file and exclude from version control
3. 환경 변수를 통한 키 관리 / Manage keys through environment variables
4. 정기적인 키 교체 / Regular key rotation

## 용어 사전 / Glossary

### 재무 용어 / Financial Terms

| 한국어 | English | 설명 / Description |
|--------|---------|-------------------|
| 시가총액 | Market Cap | 발행 주식 수 × 현재 주가 / Shares × Current Price |
| ROE | Return on Equity | 순이익 ÷ 자기자본 / Net Income ÷ Equity |
| PER | P/E Ratio | 주가 ÷ 주당순이익 / Price ÷ EPS |
| PBR | P/B Ratio | 주가 ÷ 주당순자산 / Price ÷ Book Value |
| FCF | Free Cash Flow | 영업현금흐름 - 자본지출 / Operating CF - CapEx |
| CAGR | Compound Annual Growth Rate | 연평균 성장률 / Annual Growth Rate |
| EBITDA | Earnings Before Interest, Taxes, Depreciation, and Amortization | 이자, 세금, 감가상각 전 이익 |

## 결론 / Conclusion

### 한국어
Enhanced NASDAQ Stock Screener는 복잡한 금융 분석을 자동화하여 개인 투자자도 전문가 수준의 종목 분석을 수행할 수 있게 합니다. 섹터별 상대 평가, 다차원 품질 점수, 백테스팅 기능을 통해 객관적이고 검증 가능한 투자 의사결정을 지원합니다.

### English
The Enhanced NASDAQ Stock Screener automates complex financial analysis, enabling individual investors to perform professional-level stock analysis. Through sector-relative evaluation, multi-dimensional quality scoring, and backtesting capabilities, it supports objective and verifiable investment decision-making.

---

*이 문서는 Enhanced NASDAQ Stock Screener v1.0의 아키텍처를 설명합니다.*
*This document describes the architecture of Enhanced NASDAQ Stock Screener v1.0.*