# MeerkatAI 크레인 양중 검토 기능 기획·설계 정리 v0.5

작성 목적: 현재까지 논의한 기능 방향, 데이터 전략, 공통 스키마, PDF 파싱 구조, 검증 원칙, PoC 범위를 한 문서로 정리하여 동료 검토 및 다음 개발 단계의 기준 문서로 사용한다.


## v0.5 주요 변경사항

v0.5에 대한 구현 전 2차 검토를 반영하여 문서 내부 충돌과 구현 명세를 정리했다.  
**v0.5를 Terex TRT60 Parser PoC의 최종 구현 기준선(Implementation Baseline)으로 사용한다.**

- 현재 단계는 **Terex TRT60 Parser Vertical Slice PoC**로 확정
- 현재 Parser PoC 종료점을 `Canonical Data + Validation + Source Traceability + Deterministic Output`으로 고정
- `Required Height / Reach / Capacity Review / Geometry / User Confirmation / Engineer Approval / UI`는 현재 Parser PoC에서 제외
- 다음 단계는 별도의 **Engineering Review PoC**로 분리
- `Required Height`는 Engineering Review 단계부터 **사용자가 직접 입력하는 필수값**으로 사용
- `capacity_basis`를 실제 `load_charts` 스키마 필드로 정의하고 원문 근거를 추적
- Parser Verification / User Confirmation / Engineer Approval을 서로 다른 상태축으로 분리
- `source_text → parsed_source_value → canonical_value_si`의 3단계 수치 모델을 명시
- “정확 일치”는 원문 수치 의미의 정확한 파싱에 적용하며, SI 정규화 값의 문자열 동일성을 의미하지 않음
- 단위 변환은 deterministic conversion으로 별도 검증
- `LoadChartCell`에 `cell_status` 및 원문 표현을 보존하여 빈 셀·금지·적용불가·파싱오류를 구분
- Parser PoC의 Critical Error 목표는 **0건**
- 동일 PDF + 동일 Parser Profile + 동일 Parser Version은 동일 Canonical Data를 생성해야 함
- 섹션 번호 및 PoC 단계 명칭 충돌을 정리

---

---

## 1. 기능을 만들려는 이유

초기에는 제조사별 크레인 제원표 PDF를 수집·파싱하여 자체 크레인 제원 DB를 구축하고, 사용자가 인양 조건을 입력하면 적합한 장비를 역제안하는 기능을 검토했다.

그러나 검토 과정에서 다음 문제가 확인되었다.

- 제조사·제3자 자료의 라이선스 조건 때문에 대량 수집 후 자체 상용 DB/API로 재배포하는 방식은 법적·운영상 리스크가 있다.
- ChatGPT, NotebookLM 등 범용 AI도 사용자가 제원표 PDF를 업로드하면 문서를 읽고 질의응답을 할 수 있다.
- 단순 “PDF 읽기/질의응답”만으로는 MeerkatAI만의 제품 차별성이 약하다.
- 실제 현장에서 필요한 것은 PDF 요약이 아니라 **양중 검토 절차 자체의 표준화·자동화**다.

따라서 제품 정의를 다음과 같이 수정한다.

> **MeerkatAI의 핵심 기능은 ‘크레인 PDF 분석기’가 아니라 ‘양중계획 검토 Workflow’다.**
>
> 사용자가 실제 사용할 크레인의 제원표를 업로드하고 인양 조건을 입력하면, 시스템이 해당 장비의 구성 조건과 Load Chart를 구조화하여 제원 검토를 수행하고, 근거 원문을 제시하며, 이후 줄걸이 검토·안전기준·작업계획서 생성으로 연결한다.

---

## 2. 목표 사용자 흐름

### 기본 흐름

```text
크레인 제원표 PDF 업로드
        ↓
제조사 / 모델 / Crane Type 자동 식별
        ↓
Load Chart 페이지 및 Configuration 자동 분리
        ↓
사용자 작업조건 입력
        ↓
Gross Load 계산
        ↓
Reach / Geometry 검토
        ↓
해당 Configuration의 Load Chart 조회
        ↓
Rated Capacity 비교
        ↓
조건 충족 / 조건부 / 부적합 판정
        ↓
근거 Load Chart 원문 표시
        ↓
줄걸이 검토
        ↓
관련 안전기준 확인
        ↓
양중 작업계획서 생성
```

### 사용자가 입력할 핵심 작업조건

- 인양물 중량
- 줄걸이/슬링 중량
- Hook Block 중량
- Spreader/Lifting Beam 등 부속 중량
- 작업반경
- 필요 인양높이
- 실제 사용할 크레인의 아웃트리거 또는 크롤러 조건
- 필요한 경우 Counterweight/Ballast 조건

### 시스템이 계산할 값

```text
Gross Load
= Payload
+ Hook Block
+ Sling / Wire
+ Spreader / Lifting Beam
+ 기타 인양부속
```

정격하중과 비교할 때는 Payload만 보지 않고 Gross Load를 사용한다.

---

## 3. 기능 범위

### V1에서 포함

- Mobile Crane
  - All Terrain
  - Rough Terrain
  - Truck Crane
- Crawler Crane
- **Main Boom Load Chart**
- Counterweight / Ballast 조건
- Outrigger 또는 Crawler Configuration
- Working Area
- Radius
- Boom Length / Boom Configuration
- Rated Capacity
- Hook Block
- Parts of Line / Reeving 관련 기본정보
- 원문 PDF 페이지 근거 연결
- 사용자 PDF 기반 단일 장비 제원 검토
- **Configuration 자동 추출 후 사용자 확인 단계**
- **Geometry/Reach Check와 Capacity Check 분리**
- **임의 수치 보간 금지**

> V1은 Main Boom의 정적 양중 검토에 집중한다. Jib, Luffing Jib, Runner, Derrick 등은 공통 구조에 필드는 준비하되 실제 판정 로직은 후속 단계에서 활성화한다.

### 이후 확장

- Fixed Jib
- Swing-away Jib
- Luffing Jib
- Runner
- Derrick
- Pick & Carry / On Tires
- 풍속 조건
- 지반지지력 및 Outrigger Reaction
- 줄걸이 상세 검토
- 양중 작업계획서 자동 생성
- 제조사 라이선스 확보 시 자체 DB 기반 장비 역제안

### 현재 보류

- 제조사 전체 카탈로그를 무단 대량 수집하여 자체 상용 Crane DB로 재배포
- 전 세계 크레인을 포괄하는 즉시 역제안 서비스
- LLM이 직접 정격하중을 추론하여 안전 판정을 내리는 구조

---

## 4. 수집된 분석 자료

현재 폴더 구조는 Mobile Crane / Crawler Crane으로 분리하고, 그 아래 제조사별로 정리했다.

실제 ZIP 확인 결과 PDF는 총 27개다.

### Crawler Crane

#### Kobelco
- 7120SFS
- CKS1350
- CKS3000

#### Liebherr
- Derrick for 400t crane
- LR 1100
- LR1400.1 SX

#### Manitowoc
- MLC150-1
- MLC300
- MLC650

### Mobile Crane

#### Grove
- GMK3060L-1
- GMK4100L-2
- GMK7550

#### KATO
- SR-500LX
- CR-200Rf
- SR-700LII

#### Liebherr
- LTM1090-4.2
- LTM1120-4.1
- LTM1400-6.1

#### SANY
- SAC2500C8
- SAC600E
- SAC8000T7

#### Tadano
- AC 2.040-1
- AC 4.070L-1
- GR250N-4

#### Terex
- TRT35
- TRT60
- TRT70

> 폴더명 `Kobleco`는 코드 및 DB에서는 `Kobelco`로 정규화할 예정.

---

## 5. 분석에서 확인된 핵심 원칙

### 5.1 Capacity는 크레인의 고정 속성이 아니다

같은 장비라도 다음 조건에 따라 정격하중이 달라진다.

- Counterweight / Ballast
- Outrigger 전개율 및 폭
- Crawler Configuration
- Working Area
- Boom/Jib 구성
- Boom Length
- Radius
- Reeving / Parts of Line
- Hook Block
- Standard
- 일부 제조사 특수조건

따라서 아래 구조는 사용할 수 없다.

```text
crane
radius
boom_length
capacity
```

정확한 구조는 다음과 같다.

```text
CRANE
  ↓
LIFTING CONFIGURATION
  ↓
BOOM CONFIGURATION
  ↓
LOAD CHART
  ↓
LOAD CHART CELL
```

### 5.2 보간(Interpolation) 및 Grid 처리 원칙

Load Chart에 사용자의 작업반경 또는 붐 조건과 정확히 일치하는 값이 없더라도 시스템이 임의로 선형보간하지 않는다.

원칙:

```text
Radius
→ 제조사 지침이 별도로 없으면
→ 사용자의 실제 반경보다 작은 값으로 이동하지 않음
→ 적용 가능한 다음 큰 Radius 등 보수적 Grid 선택 규칙을 제조사 지침과 함께 검토

Boom
→ '더 짧은 Boom이 보수적'이라고 일반화하지 않음
→ 먼저 실제 작업반경 + 필요높이를 만족하는 Boom Configuration을 결정
→ 해당 Boom Configuration의 Load Chart만 사용

Capacity
→ 임의 Linear Interpolation 금지
```

따라서 판정 엔진은 다음처럼 분리한다.

```text
작업반경 + 필요높이
        ↓
Geometry / Reach Engine
        ↓
가능한 Boom Configuration 결정
        ↓
해당 Load Chart 선택
        ↓
Capacity Engine
```

### 5.3 Unit Normalization 원칙

원문 단위와 내부 계산 단위를 분리한다.

```text
source_value
source_unit
        ↓
Unit Normalizer
        ↓
canonical_value_si
canonical_unit
```

특히 다음을 엄격히 구분한다.

- metric tonne = 1,000 kg
- US short ton ≈ 907.185 kg
- imperial long ton ≈ 1,016.047 kg
- ft / in / lb / kip 등 북미 문서 단위

원문 단위가 명확하지 않으면 추론 승인하지 않고 `UNIT_UNRESOLVED` 상태로 검토를 차단한다.

---

## 6. Mobile과 Crawler를 함께 처리하는 이유

양중 검토의 상위 로직은 Mobile과 Crawler가 동일하다.

```text
인양중량
+ 작업반경
+ 필요높이
        ↓
장비 Configuration 확인
        ↓
Reach / Geometry 검토
        ↓
Load Chart 확인
        ↓
Rated Capacity 비교
```

차이는 Capacity를 결정하는 Configuration이다.

### Mobile 전용 또는 중요 조건

- Outrigger
- Outrigger Extension
- Outrigger Width
- On Tires
- Pick & Carry
- Over Rear / 360° 등 Working Area

### Crawler 전용 또는 중요 조건

- Crawler Gauge / Track Width
- Crawler Extension
- Upper Counterweight
- Carbody Weight
- Lower Weight
- Boom/Jib 조합
- Derrick 구성

따라서 DB를 Mobile / Crawler로 완전히 분리하지 않고, 공통 상위 Schema를 사용하되 타입별 Support Configuration을 둔다.

---

## 7. 제조사별 문서 특성 및 Parser 방향

### Terex

분석 대상: TRT35 / TRT60 / TRT70

특징:
- 문서 구조가 비교적 일관적
- Main Boom Load Chart의 Header가 명확함
- Counterweight, Outrigger, 360°, EN13000 등이 한 페이지에 구조적으로 표시됨
- Outrigger 100% / 50% / 0% 및 On Tires 표가 분리되는 경우가 있음

판단:
- 초기 PoC 대상에 적합
- `TerexRTParser` 또는 유사 Profile 하나로 여러 모델을 처리할 가능성이 높음
- 파싱 난이도: 낮음~중간

---

### Tadano

분석 대상: AC 2.040-1 / AC 4.070L-1 / GR250N-4

특징:
- AC 계열은 비교적 일관된 Layout
- Counterweight별 Load Chart가 분리됨
- HA / HAV / MS 등 구성 코드가 중요
- 360° / Max / Over Rear 등의 조건을 구분해야 함
- GR 계열은 AC와 문서 Layout이 달라 별도 Profile 필요 가능성이 높음

예상 Profile:
- `TADANO_AC_MODERN`
- `TADANO_GR_KR`

파싱 난이도: 중간

---

### Liebherr Mobile

분석 대상: LTM1090-4.2 / LTM1120-4.1 / LTM1400-6.1

특징:
- 정보 품질이 높고 제조사 내부 규칙도 비교적 일관적
- 페이지 상단의 아이콘, 숫자, 위치, 색상으로 Configuration을 표현하는 경우가 많음
- Counterweight/Ballast, Working Area, Boom/Jib, Outrigger 등이 Header Symbol에 의존하는 경우가 있음

필요:
- Native Text
- Header ROI
- Symbol Dictionary
- Layout Position
- 필요 시 Color/Highlight 정보

예상 Profile:
- `LIEBHERR_MOBILE_MODERN`

파싱 난이도: 중간

---

### Grove

분석 대상: GMK3060L-1 / GMK4100L-2 / GMK7550

특징:
- 최신 GMK와 구형 Product Guide의 Layout 차이가 큼
- 최신형은 구조가 비교적 정돈됨
- GMK7550은 문서 규모가 크고 Jib/Luffing/Imperial 요소가 복잡함

예상 Profile:
- `GROVE_GMK_MODERN`
- `GROVE_LEGACY_PRODUCT_GUIDE`

파싱 난이도: 중간~높음

---

### KATO

분석 대상: SR-500LX / CR-200Rf / SR-700LII

특징:
- 유럽계 제조사와 문서 표현이 다름
- Outrigger 관련 조건이 중요
- Boom/Jib 정보 밀도가 높음
- 문서가 상대적으로 짧은 편

예상 Profile:
- `KATO_RT`

파싱 난이도: 중간

---

### SANY

분석 대상: SAC2500C8 / SAC600E / SAC8000T7

특징:
- 영문/중문 혼합
- 모델별 Layout 변화가 비교적 큼
- 대형 장비로 갈수록 Boom/Jib/Counterweight/Outrigger Configuration이 복잡
- 고정 좌표만 사용하는 Parser는 불안정할 가능성이 높음

추천:
- Semantic Anchor + Layout 기반
- `Load Chart`, `Counterweight`, `Outrigger`, `Main Boom` 등의 텍스트 Anchor를 우선 활용

예상 Profile:
- `SANY_AT_PROFILE_A`
- `SANY_AT_PROFILE_B`

파싱 난이도: 중간~높음

---

### Kobelco Crawler

분석 대상: 7120SFS / CKS1350 / CKS3000

특징:
- Counterweight에 따른 Load Chart 구분이 명확한 경우가 있음
- Parts of Line, Hook Block, Slings, Operating Radius 등이 구조적으로 표시됨
- 대형 모델에서는 Upper Counterweight와 Carbody Weight를 별도로 관리해야 함
- Main Boom / Long Boom / Fixed Jib / Luffing Jib 등 Boom System이 중요

중요 결론:
- Crawler는 `counterweight_t` 하나만으로 부족
- `upper_counterweight_t`, `carbody_weight_t`를 분리해야 함

예상 Profile:
- `KOBELCO_CRAWLER`

파싱 난이도: 중간

---

### Manitowoc Crawler

분석 대상: MLC150-1 / MLC300 / MLC650

특징:
- Boom / Jib / Luffing Jib / Counterweight / Carbody 조건이 체계적
- 대형 Crawler는 특정 Boom/Jib 조합 자체가 하나의 Configuration
- 단순 `boom_length`, `jib_length`보다 제조사의 구성 코드 또는 `boom_configuration_id`를 보존하는 것이 유리

예상 Profile:
- `MANITOWOC_MLC`

파싱 난이도: 중간

---

### Liebherr Crawler

분석 대상: LR1100 / LR1400.1 SX / Derrick 관련 자료

역할:
- 같은 Liebherr 브랜드 내 Mobile과 Crawler의 차이를 비교하는 좋은 표본
- 제조사 고유 Symbol/Layout 규칙과 Crane Type 고유 Configuration 차이를 분리하는 데 활용

예상 Profile:
- `LIEBHERR_CRAWLER_MODERN`

---

## 8. Common Schema v1 초안

### 8.1 `cranes`

```text
id
manufacturer
brand
model
crane_type
nominal_capacity_t
source_document_id
created_at
updated_at
```

예상 `crane_type`:

```text
all_terrain
rough_terrain
truck_crane
crawler
```

---

### 8.2 `lifting_configurations`

장비 전체의 안정성·운용 조건을 정의한다.

```text
id
crane_id

counterweight_t
upper_counterweight_t
carbody_weight_t

support_mode
working_area
standard

manufacturer_specific JSONB
created_at
```

예상 `support_mode`:

```text
OUTRIGGER
ON_TIRES
CRAWLER
BARGE
OTHER
```

---

### 8.3 `support_configurations`

Mobile / Crawler의 지지조건 차이를 흡수한다.

```text
id
lifting_configuration_id

support_type

outrigger_percent
outrigger_width_m
outrigger_length_m

crawler_gauge_m
crawler_extension

manufacturer_specific JSONB
```

---

### 8.4 `boom_configurations`

Boom/Jib 계열 Configuration을 별도 관리한다.

```text
id
lifting_configuration_id

boom_type
main_boom_length_m

jib_type
jib_length_m
jib_offset_deg

luffing_jib_length_m
boom_angle_deg

configuration_code
manufacturer_specific JSONB
```

초기 `boom_type` 후보:

```text
MAIN
LONG_BOOM
FIXED_JIB
SWING_AWAY_JIB
LUFFING_JIB
RUNNER
DERRICK
OTHER
```

---

### 8.5 `load_charts`

```text
id
boom_configuration_id

chart_type
unit_system

capacity_basis
capacity_basis_source_document_id
capacity_basis_source_page
capacity_basis_source_bbox

source_document_id
source_page

parser_profile
parser_version

verification_status
created_at
```

---

### 8.6 `load_chart_cells`

실제 Rule Engine이 향후 조회할 정격하중 데이터다.

```text
id
load_chart_id

radius_m
boom_length_m
rated_capacity_t
boom_angle_deg

source_radius_text
parsed_source_radius_value
source_radius_unit

source_capacity_text
parsed_source_capacity_value
source_capacity_unit

canonical_radius_m
canonical_capacity_t

cell_status
source_text
source_bbox
confidence
```

권장 `cell_status`:

```text
AVAILABLE
NOT_AVAILABLE
PROHIBITED
BLANK
PARSE_ERROR
```

### 수치 표현 원칙

수치는 다음 3단계를 구분한다.

```text
source_text
→ parsed_source_value
→ canonical_value_si
```

예:

```text
source_capacity_text = "12,500 kg"
parsed_source_capacity_value = 12500
source_capacity_unit = "kg"
canonical_capacity_t = 12.5
```

원칙:

- `source_text`: PDF에서 실제로 관찰된 원문 문자열
- `parsed_source_value`: 원문 숫자를 정확히 해석한 값
- `canonical_value_si`: 내부 계산용 SI 정규화 값
- Parser의 “정확 일치”는 `source_text → parsed_source_value`의 의미 보존에 적용
- 단위 정규화는 별도의 deterministic conversion test로 검증
- 빈 셀과 금지 셀을 `null` 하나로 혼동하지 않음
- Counterweight / Outrigger / Working Area 등 Chart-level Configuration을 Cell마다 중복 저장하지 않음

예:

```text
source_text = "-"
cell_status = NOT_AVAILABLE
canonical_capacity_t = null
```

Parts of Line은 제조사 문서에서 Chart-level인지 Cell-level인지 확인한 뒤 Parser Profile별로 모델링한다.


### 8.7 `hook_blocks`

```text
id
crane_id

capacity_t
weight_t
sheave_count
max_parts_of_line

source_document_id
source_page
```

---

### 8.8 `capacity_basis`

`capacity_basis`는 개념 설명이 아니라 **`load_charts`의 실제 필드**로 관리한다.

`load_charts` 필드:

```text
capacity_basis
capacity_basis_source_document_id
capacity_basis_source_page
capacity_basis_source_bbox
```

권장 상태:

```text
GROSS_RATED_LOAD
NET_LOAD
UNKNOWN
```

원칙:

- 제조사 문서의 Notes / Load Chart 설명을 근거로 결정
- Hook Block, Sling, Spreader, Wire Rope, Stowed Jib 등의 포함/차감 관계를 임의 추정하지 않음
- `UNKNOWN`이면 향후 Engineering Review 자동 Capacity 판정을 차단
- 동일 Load Component가 사용자 Gross Load와 Manufacturer Deduction 양쪽에서 중복 적용되지 않도록 함
- Chart/Configuration 수준에서 관리하며 모든 Cell에 반복 저장하지 않음


### 8.9 `capacity_adjustment_rules`

Hook Block 이외의 제조사 지정 차감·보정조건을 별도 관리한다.

```text
id
crane_id
lifting_configuration_id

adjustment_type
value
unit
condition_json

source_document_id
source_page
source_bbox

manufacturer_specific JSONB
```

초기 `adjustment_type` 후보:

```text
HOOK_BLOCK_WEIGHT
SLING_WEIGHT
STOWED_JIB_DEDUCTION
AUX_HEAD_DEDUCTION
WIRE_ROPE_DEDUCTION
OTHER
```

> 시스템이 임의의 Deduction 공식을 생성하지 않는다. 제조사 Load Chart, Operation Manual 또는 검증된 원문에서 명시한 규칙만 적용한다.

### 8.10 향후 `reeving_rules`

```text
id
crane_id
hook_block_id

parts_of_line
max_allowable_load_t
rope_diameter_mm
source_document_id
source_page
```

---

### 8.11 `source_documents`

```text
id
crane_id

original_filename
manufacturer
model

revision
issue_date
document_type

file_hash_sha256
storage_path

parser_profile
parser_version

created_at
```

### 8.12 `lifting_reviews`

Parser가 추출한 원천 데이터와 실제 Engineering Review 결과를 분리 저장한다.

```text
id
user_id
site_id
crane_id

source_document_hash
lifting_configuration_id
load_chart_id

input_snapshot JSONB
result_snapshot JSONB

parser_version
rule_engine_version

review_status
created_at
```

### 8.13 `review_evidence`

검토 당시 적용된 원문 근거를 재현하기 위한 Evidence를 저장한다.

```text
id
lifting_review_id

source_document_id
source_page
source_bbox

evidence_image_path
evidence_hash
created_at
```

목적:
- Parser 버전 변경 후에도 과거 검토결과 재현
- 적용 Load Chart 원문 확인
- 감사(Audit) 및 오류 추적

---

## 9. Parser Architecture

단순히 `제조사 → Parser 1개`로 처리하지 않는다.

권장 구조:

```text
PDF
 ↓
Document Inspector
 ↓
Manufacturer / Brand Detector
 ↓
Crane Type Detector
 ↓
Document Layout / Generation Detector
 ↓
Parser Profile Selector
 ↓
Page Classifier
 ↓
Configuration Header Parser
 ↓
Table Segmenter
 ↓
Load Chart Table Parser
 ↓
Unit Normalizer
 ↓
Canonical Schema
 ↓
Validation Engine
 ↓
Configuration Confirmation Gate
 ↓
Geometry / Reach Engine
 ↓
Capacity Engine
 ↓
Capacity Adjustment Rules
 ↓
Review Result
 ↓
Source Evidence + Audit Log
```

예상 Parser Profile 예시:

```text
LIEBHERR_MOBILE_MODERN
LIEBHERR_CRAWLER_MODERN

TADANO_AC_MODERN
TADANO_GR_KR

GROVE_GMK_MODERN
GROVE_LEGACY_PRODUCT_GUIDE

TEREX_TRT

KATO_RT

KOBELCO_CRAWLER

MANITOWOC_MLC

SANY_AT_PROFILE_A
SANY_AT_PROFILE_B
```

---

## 10. 페이지 분류

PDF 전체를 곧바로 고비용 파서에 넣지 않는다.

먼저 페이지를 분류한다.

```text
GENERAL_SPEC
DIMENSION
COUNTERWEIGHT
HOOK
RANGE_DIAGRAM
MAIN_BOOM_LOAD_CHART
JIB_LOAD_CHART
LUFFING_JIB_LOAD_CHART
RUNNER_LOAD_CHART
OUTRIGGER_CONFIG
CRAWLER_CONFIG
NOTES
OTHER
```

Load Chart로 판단된 페이지만 세부 Configuration 및 Table Parsing을 수행한다.

장점:
- 처리속도 개선
- 불필요 OCR/LLM 사용 감소
- 잘못된 표 파싱 감소

### Table Segmenter

한 페이지 안에 여러 개의 하중표 또는 서브헤더가 존재할 수 있으므로, Page 단위와 Chart 단위를 동일하게 취급하지 않는다.

```text
Page
 ├─ Segment A
 ├─ Segment B
 └─ Segment C
```

`load_charts`에는 다음 Source 정보가 필요하다.

```text
source_page
source_bbox
segment_index
```

각 Segment가 서로 다른 Working Area, Counterweight, Outrigger, Boom Condition을 가질 수 있으므로 Header와 Segment의 연결관계를 검증한다.

---

## 11. Configuration Header가 핵심

이 프로젝트에서 가장 중요한 데이터는 표 내부 숫자 자체보다 **그 숫자가 어떤 장비 Configuration에 해당하는가**이다.

예:

```json
{
  "counterweight_t": 134,
  "working_area": "360",
  "support": {
    "type": "outrigger",
    "width_m": 7
  },
  "boom": {
    "type": "main",
    "range_m": [16.1, 85.0]
  },
  "standard": "EN"
}
```

Header를 신뢰성 있게 추출한 뒤 그 Header에 Load Chart Cell을 연결해야 한다.

원칙:

> **Configuration Header가 불확실하면 해당 Load Chart 데이터는 자동 승인하지 않는다.**

### Configuration Confirmation Gate

자동 추출 성공 후에도 실제 장비상태와 제원표 Configuration의 일치를 사용자가 확인한다.

예:

```text
제원표에서 다음 조건을 인식했습니다.

Counterweight     134 t
Outrigger          7 m
Working Area       360°
Main Boom          16.1–85 m

[실제 장비 상태와 일치합니다]
```

이 단계의 목적은 책임 이전이 아니라 **실제 현장 장비 상태와 PDF상의 Configuration을 일치시키는 Verification**이다.

다음 상태에서는 검토 자체를 진행하지 않는다.

```text
LOW_CONFIDENCE
CONFIG_CONFLICT
UNIT_UNRESOLVED
TABLE_STRUCTURE_UNKNOWN
```

즉 V1의 기본 정책은 **Fail-Closed**다.

---

## 12. PDF 추출 전략

현재 자료를 보면 Native Text가 살아 있는 PDF가 많기 때문에 OCR-first 방식은 사용하지 않는다.

### 우선순위

```text
1. PyMuPDF / Native text extraction
2. Text coordinates / Layout reconstruction
3. Table reconstruction
4. Header ROI 및 Symbol recognition
5. OCR fallback
```

OCR은 다음 경우에만 사용한다.

- Native text 추출 실패
- 페이지가 raster scan
- 구형 스캔 문서
- Symbol/숫자가 이미지로만 존재

LLM은 숫자 값을 결정하는 주 파서로 사용하지 않는다.

---

## 13. LLM의 역할

### 사용 가능

- 문서 유형 분류 보조
- 제조사/모델 추출 보조
- 복잡한 Header 의미 해석
- 제조사 고유 약어 의미 정규화
- 사용자를 위한 결과 설명
- 예외 발생 시 검토 보조

### 사용하지 않을 영역

- Load Chart 숫자의 최종 결정
- 정격하중 계산
- Gross Load 계산
- 적합/부적합의 핵심 수치 판정

원칙:

```text
Calculation = Python
Search = PostgreSQL
Validation = Rule Engine
Explanation = LLM
```

---

## 14. Validation 전략

안전 관련 데이터이므로 단순 파싱 성공 여부만으로 DB에 승인하지 않는다.

### 상태

```text
AUTO_PARSED
AUTO_VALIDATED
DATA_VERIFIED
REJECTED
```

초기 Golden Dataset 및 내부 기준 데이터는 `DATA_VERIFIED` 상태를 실제 양중 검토의 기준으로 사용한다.

일반 사용자 업로드 Workflow에서는 모든 문서를 운영자가 사전 검증하기 어렵기 때문에 다음 하이브리드 방식을 사용한다.

```text
AUTO_PARSED
→ AUTO_VALIDATED
→ Source Highlight
→ User Configuration Confirmation
→ Engineering Review
```

단, Critical Error 가능성이 있거나 Confidence 기준 미달이면 자동 검토를 차단한다.

### 검증 항목 예시

- 모델/제조사 일치
- 페이지 Header Configuration 일치
- 단위 검증
- Radius 범위 검증
- Boom Length 범위 검증
- Nominal Capacity 초과값 검출
- Load Chart 내 비정상적인 수치 패턴 탐지
- 행/열 개수 일치
- 빈 셀과 0의 구분
- source page/bbox 연결 확인

주의:
- 일반적으로 Radius 증가 시 Capacity가 감소하는 경향이 있지만, 표 구조·Configuration에 따라 단순 단조성 규칙만으로 오류 판정을 확정하면 안 됨.
- Validation Rule은 제조사/Chart 유형별 보조 규칙으로 사용한다.

---

## 15. Source Traceability

모든 추출 데이터는 원문 근거로 되돌아갈 수 있어야 한다.

최소 저장 정보:

```text
source_document_id
source_page
source_bbox
parser_profile
parser_version
confidence
```

사용자 화면에서는 결과와 함께:

```text
[적용 Load Chart 원문 보기]
```

를 제공한다.

목표:
- 사용자가 판정 근거를 직접 확인 가능
- Parser 오류 추적 가능
- 안전 검토 이력 확보
- 향후 Human Verification 효율 향상

---

## 16. 검증 및 승인 상태 체계

Parser의 데이터 품질, 사용자의 현장 Configuration 확인, 전문 엔지니어의 승인 상태를 서로 다른 상태축으로 관리한다.

### 16.1 Parser Verification Status

현재 Parser PoC에서 실제 구현하는 상태축이다.

```text
AUTO_PARSED
AUTO_VALIDATED
LOW_CONFIDENCE
CONFIG_CONFLICT
UNIT_UNRESOLVED
TABLE_STRUCTURE_UNKNOWN
REJECTED
```

- `AUTO_PARSED`: 구조화 완료, 검증 전
- `AUTO_VALIDATED`: Golden Dataset / Rule 검증 통과
- `LOW_CONFIDENCE`: Header/Table/Cell 신뢰도 부족
- `CONFIG_CONFLICT`: Configuration 정보 충돌
- `UNIT_UNRESOLVED`: 단위 확정 불가
- `TABLE_STRUCTURE_UNKNOWN`: 행·열·Sub-header 구조 복원 불가
- `REJECTED`: Critical Error 또는 명백한 파싱 실패

현재 Parser PoC의 정상 종료 상태는 `AUTO_VALIDATED`까지다.

### 16.2 User Confirmation Status

향후 Engineering Review/UI 단계에서 사용한다.

```text
NOT_CONFIRMED
CONFIRMED
```

`CONFIRMED`는 사용자가 실제 현장 장비 상태와 시스템이 제시한 Configuration이 일치한다고 확인했다는 의미이며 Engineering Approval이 아니다.

현재 Parser PoC에서는 구현하지 않는다.

### 16.3 Engineer Approval Status

향후 전문 검토 Workflow에서만 사용한다.

```text
NOT_REVIEWED
APPROVED
REJECTED
```

현재 Parser PoC에서는 구현하지 않는다.

### 16.4 상태축 분리 원칙

다음처럼 하나의 상태로 혼합하지 않는다.

```text
DATA_VERIFIED
```

권장:

```text
parser_verification_status
user_confirmation_status
engineer_approval_status
```

---
---

## 17. 라이선스 및 데이터 전략

### 초기 원칙

- 제3자 사이트의 PDF를 대량 크롤링하여 상용 DB로 재배포하는 방식을 핵심 전략으로 사용하지 않는다.
- 사용자 또는 현장이 보유한 실제 제원표 PDF를 업로드하여 검토하는 Workflow를 우선한다.
- 제조사 공식 PDF는 Parser 연구/검증 및 허용 범위 내 사용을 우선 검토한다.
- 라이선스가 불명확한 데이터는 자체 역제안 DB의 Master Source로 사용하지 않는다.

### 원본 PDF / 캐시 / 근거 보존 원칙

원본 PDF를 무조건 영구 저장하는 방식과, 원본을 즉시 삭제하고 JSON만 남기는 방식 모두 피한다.

권장 구조:

```text
Original PDF
→ Project / Session scoped storage
→ Retention Policy 적용

Canonical JSON
→ SHA-256 기반 중복 캐시

Evidence Snapshot
→ 실제 판정에 사용한 Load Chart 영역만 별도 보존 가능
```

최소 Evidence:

```text
document_hash
page_number
bbox
evidence_image_hash
```

구체적인 원본 PDF 보존기간과 Evidence Snapshot 보존정책은 라이선스, 개인정보, 고객 계약조건 검토 후 확정한다.

### 향후

제조사 또는 데이터 제공자와 정식 라이선스 계약이 가능해지면:

```text
자체 Crane Database
        ↓
조건 기반 후보 추출
        ↓
적합 장비 역제안
```

기능을 Pro/Enterprise 기능으로 확장할 수 있다.

---

## 18. PoC 개발 순서

### PoC 1 — Terex TRT60

목표:
- PDF 자동 식별
- Load Chart 페이지 탐지
- Configuration Header 자동 추출
- Table Segment 분리
- Radius × Boom Length × Capacity JSON화
- Unit Normalization
- Source page/bbox 연결
- Validation
- 사용자 Configuration Confirmation
- Geometry / Reach Check
- Capacity Check
- Review Result + Evidence/Audit 저장

이유:
- 문서 규칙이 비교적 명확하고 반복적

---

### PoC 2 — Tadano AC 2.040-1

추가 검증:
- Counterweight 변화
- HA / HAV / MS
- 360° / Max / Over Rear 등 Working Area

---

### PoC 3 — Liebherr LTM1400-6.1

추가 검증:
- Symbol 기반 Header
- 아이콘
- 상단 배치
- 색/강조
- 복잡한 Configuration

---

### PoC 4 — Kobelco CKS3000

추가 검증:
- Crawler
- Upper Counterweight
- Carbody Weight
- Boom/Jib Configuration

---

### PoC 5 — Manitowoc MLC300

추가 검증:
- 다른 Crawler 제조사에서도 Common Schema가 유지되는지 확인
- Configuration Code / Boom Combination 처리

---

## 19. PoC 성공 기준

각 단계별로 정답 Dataset을 수동으로 만든 뒤 Parser 결과와 비교한다.

### 권장 검증 단위

```text
Manufacturer / Model Detection
Page Classification
Configuration Header Accuracy
Load Chart Cell Accuracy
Source Traceability Accuracy
```

### 목표

- 제조사/모델 판별: 사실상 100% 목표
- Configuration Header: 99% 이상 목표
- Load Chart 숫자: 실사용 승인 기준은 사실상 100%에 가까운 검증 필요
- 자동 파싱 데이터는 초기에는 Human Verification을 통과해야 실제 판정에 사용

단순 평균 정확도보다 **Critical Error = 0**을 목표로 한다.

Critical Error 예:
- Counterweight 잘못 매칭
- Outrigger 조건 잘못 매칭
- Radius/Capacity 행·열 뒤바뀜
- 다른 Load Chart 페이지의 Capacity를 잘못 연결
- 단위 판별/변환 오류
- Grid 사이 값을 임의 선형보간하여 허용하중 생성
- Geometry 조건을 만족하지 않는 Boom Configuration의 Capacity 적용

---

## 20. 향후 사용자 화면 초안

```text
[양중 검토]

1. 크레인 제원표
   [PDF 업로드]

2. 작업조건
   인양물 중량          18.0 t
   Sling / Wire          0.5 t
   Hook Block            0.8 t
   Spreader              0.3 t

   Gross Load           19.6 t

   작업반경              32 m
   필요 인양높이          45 m

3. 장비 Configuration
   모델                  자동 인식
   Counterweight         자동 인식/확인
   Outrigger/Crawler     자동 인식/확인
   Working Area          자동 인식/확인
   Boom Configuration    자동 인식/확인

   [실제 장비 상태와 일치합니다]

4. Geometry / Reach 검토
   작업반경 조건          충족 / 불충족
   필요 높이 조건         충족 / 불충족
   적용 Boom Config       XX.X m

5. Capacity 검토
   Rated Capacity        XX.X t
   Gross Load            19.6 t
   Utilization           XX.X %

   판정                  조건 충족 / 조건부 / 부적합

   [적용 Load Chart 원문 보기]

6. 추가 검토
   [줄걸이 검토]
   [안전기준 확인]
   [양중 작업계획서 생성]
```

---

## 21. 현재 핵심 차별점

범용 AI와의 차별점은 “PDF를 읽어주는 것”이 아니다.

### 범용 AI

```text
사용자가 PDF 업로드
→ 사용자가 질문을 잘 만들어야 함
→ AI가 매번 문서를 다시 해석
→ 결과의 Configuration·계산 절차가 일관되지 않을 수 있음
```

### MeerkatAI

```text
사용자가 PDF 업로드
→ 정형 입력폼
→ 제조사별 Parser Profile
→ Common Schema
→ deterministic 계산
→ Validation
→ 원문 근거
→ 검토 이력 저장
→ 줄걸이/법령/작업계획서로 Workflow 연결
```

따라서 핵심 자산은 다음이다.

> **Crane Configuration Schema + Manufacturer Parser Rules + Validation Engine + Lifting Review Workflow**

OCR, RAG, LLM은 이를 지원하는 보조 기술이다.

---

## 22. 현재 구현 계약 — TRT60 Parser PoC

현재 구현의 질문은 하나다.

> **“Terex TRT60 PDF의 정격하중 데이터를 Configuration을 잃지 않고 정확하고 재현 가능하게 Canonical Data로 구조화할 수 있는가?”**

### 22.1 현재 Parser PoC에 포함

```text
TRT60 PDF
→ Document Inspector
→ Manufacturer / Model Detection
→ Crane Type Detection
→ Page Classifier
→ Configuration Header Parser
→ Table Segmenter
→ Main Boom Load Chart Parser
→ Unit Normalizer
→ Canonical Schema
→ Validation
→ Source Traceability
→ Deterministic JSON Output
```

현재 Parser PoC 종료점:

```text
Validated Canonical Crane Data
+
Source Evidence
+
Deterministic Output
```

### 22.2 현재 Parser PoC에서 제외

```text
Required Height 사용
Reach Solver
Geometry Engine
Gross Load 계산
Capacity 판정
Utilization
User Confirmation
Engineer Approval
자연어 답변
평면도 / 단면도 UI
Crane Drag / Rotate
Capacity / Reach Envelope
Clearance / Collision Check
Jib / Luffing Jib Capacity Review
```

### 22.3 다음 단계 — Engineering Review PoC

Parser PoC 성공 후 별도 단계로 수행한다.

입력:

```text
Required Height     ← 사용자가 직접 입력
Radius
Load / Load Components
Actual Crane Configuration
```

흐름:

```text
Validated Crane Canonical Data
        +
User Inputs
        ↓
Reach / Geometry Check
        ↓
Capacity Check
        ↓
Engineering Review Result
```

> **Required Height는 사용자가 직접 입력하는 필수 작업조건이며 시스템이 자동 추론하거나 보정하지 않는다.**

### 22.4 Parser PoC 성공 기준

Critical Error 목표:

```text
0
```

Critical Error 예:

```text
잘못된 Counterweight 연결
잘못된 Outrigger Configuration 연결
잘못된 Working Area 연결
Radius / Boom 축 뒤바뀜
다른 Cell의 Capacity 연결
다른 Load Chart의 Cell 혼합
단위 오인
빈 셀을 Capacity 값으로 생성
금지/적용불가 Cell을 AVAILABLE로 생성
Synthetic Interpolation 발생
Source Page / Segment 잘못 연결
```

PDF 원문 수치 파싱에는 임의 허용오차를 두지 않는다.

```text
source_text = "12.5"
parsed_source_value = 12.5
→ PASS
```

단위 변환은 별도의 deterministic normalization 결과와 비교한다.

```text
source_text = "12,500 kg"
parsed_source_value = 12500
source_unit = "kg"
canonical_value_si = 12.5
canonical_unit = "metric_tonne"
```

`canonical_value_si`의 문자열이 원문과 같을 필요는 없다.  
검증 대상은 **원문의 숫자 의미를 정확하게 해석했는지와 변환이 정확한지**다.

Geometry 계산의 부동소수점 허용오차는 Engineering Review PoC에서 별도로 정의한다.

### 22.5 재현성

```text
Same PDF
+ Same Parser Profile
+ Same Parser Version
        ↓
Same Canonical Data
```

Canonical Data Content Hash 기반 deterministic output test를 둔다.

---
## 23. UI 및 Geometry Engine 장기 설계 방향

현재 PoC에서는 UI를 구현하지 않는다. 다만 향후 UI가 요구하는 Geometry 기능을 막지 않도록 Engine Boundary를 미리 정의한다.

### 23.1 UI Mode A — 입력 기반 자연어/정형 검토

사용자가 다음을 입력한다.

```text
크레인 제원표 PDF
인양물 중량
Rigging / Hook / Spreader 중량
작업반경
필요 인양높이
실제 장비 Configuration
```

중요 원칙:

> **Required Height는 사용자가 직접 입력하는 필수 작업조건이다.**

예:

```text
Required Height = 30 m
```

이면 시스템은 `30 m`를 그대로 Engineering Input으로 사용한다.

- 자동 추론하지 않는다.
- 도면에서 임의 산출하지 않는다.
- 시스템이 임의 보정하지 않는다.
- 단면도가 없다는 이유로 Height 입력값을 변경하지 않는다.

Required Height의 상세 현장 입력 가이드는 Engineering Review PoC에서 UI 문구와 함께 확정한다.

검토 흐름:

```text
User Inputs
   +
Crane Spec PDF
      ↓
Parser / Canonical Schema
      ↓
Configuration Confirmation
      ↓
Gross Load
      ↓
Reach / Geometry Check
      ↓
Capacity Check
      ↓
정형 결과 + 자연어 설명
      ↓
적용 Load Chart 원문
```

자연어 설명은 계산 결과를 설명할 뿐, 수치 판정을 LLM이 수행하지 않는다.

---

### 23.2 UI Mode B — Interactive Lifting Planner

장기적으로 사용자가 실제 평면도(PDF/PNG)를 업로드하고 도면 위에서 Crane을 배치·이동하면서 양중 가능성을 확인할 수 있도록 한다.

입력:

```text
Plan PDF / PNG
Crane Spec PDF
Payload / Gross Load 조건
Required Height
Crane Configuration
```

평면도에서 다룰 정보:

```text
X / Y
Crane 위치
Target 위치
Working Radius
Building / Obstacle Footprint
Crane Body Footprint
Outrigger / Crawler Footprint
```

도면에는 반드시 Scale이 필요하다.

초기 방식:

```text
두 점 선택
→ 실제 거리 입력
→ pixel-to-meter scale 계산
```

이후 Dimension 자동 인식으로 확장할 수 있다.

---

### 23.3 작업반경 기준

작업반경은 화면상의 장비 외곽이나 Outrigger 끝이 아니라 **해당 제조사 제원표가 정의하는 기준점(일반적으로 Slewing/Rotation Center 계열 기준)과 하중 중심의 수평거리**를 사용해야 한다.

따라서 Crane Drawing Object는 장기적으로 최소 다음 Geometry를 가져야 한다.

```text
reference_center
body_polygon
support_polygon
orientation
```

실제 기준점 정의는 제조사 문서와 해당 장비 Configuration을 근거로 확정한다.

---

### 23.4 Required Height의 의미

Required Height는 사용자가 직접 입력하며 시스템이 신뢰하는 필수 입력조건이다.

예:

```text
Payload          2.0 t
Required Height 30.0 m
Radius           20.0 m
```

시스템은 이 조건으로 가능한 Boom Geometry를 검토한다.

개념적 관계:

```text
Radius + Required Height
          ↓
Reach Solver
          ↓
가능한 Boom Length / Boom Angle
          ↓
해당 Boom Configuration의 Load Chart
          ↓
Capacity Check
```

단, 실제 계산에서는 단순 직각삼각형만 사용하지 않고 제조사 제원에서 제공하는 Boom Pivot, Head Geometry, Range Diagram 등의 기준을 반영할 수 있는 구조로 설계한다.

---

### 23.5 Geometry Engine 분리

Geometry Engine은 다음 구조로 확장 가능해야 한다.

```text
Geometry Engine
│
├─ Reach Solver                 [V1/초기]
│  ├─ Radius
│  ├─ Required Height
│  ├─ Main Boom Length
│  └─ Boom Angle
│
├─ Clearance Solver             [Future]
│  ├─ Building Geometry
│  ├─ Boom Geometry
│  └─ Collision / Clearance
│
├─ Luffing Geometry Solver      [Future]
│  ├─ Main Boom
│  ├─ Luffing Jib
│  ├─ Boom Angle
│  └─ Jib Angle
│
└─ Placement Solver             [Future]
   ├─ Plan Geometry
   ├─ Section Geometry
   ├─ Capacity
   ├─ Clearance
   └─ Equipment Footprint
```

Parser와 Geometry Engine은 분리한다.

```text
PDF Parser
→ "장비가 어떤 제원을 가지는가"

Geometry Engine
→ "이 작업 위치에 기하학적으로 도달 가능한가"

Capacity Engine
→ "그 Configuration과 Radius에서 하중을 허용하는가"
```

---

### 23.6 Hydraulic Main Boom의 Clearance 문제

Hydraulic/Telescopic Crane은 Main Boom을 주로 사용하는 조건에서 Crane을 건물에 가까이 배치하면 작업반경이 감소하여 Capacity 측면에서는 유리할 수 있다.

그러나 장비가 지나치게 건물에 가까우면 Boom Angle 및 Boom Line에 따라 건물 외벽 또는 상부 구조물과 간섭할 수 있다.

따라서 다음 명제는 성립하지 않는다.

```text
Radius가 작을수록 항상 더 좋은 Crane Placement다.
```

실제 검토는:

```text
Capacity
+
Reach
+
Clearance
+
Equipment Footprint
```

을 동시에 만족해야 한다.

예:

```text
위치 A
Radius       PASS
Capacity     PASS
Clearance    PASS

위치 B — 건물 쪽으로 이동
Radius       개선
Capacity     PASS
Clearance    FAIL

위치 C — 건물에서 멀리 이동
Clearance    PASS
Capacity     FAIL
```

따라서 장기적으로는 단순 최소 Radius가 아니라 **Feasible Placement Zone**을 찾는 것이 목표다.

---

### 23.7 Crawler + Luffing Jib의 Geometry 차이

Crawler Crane의 Main Boom + Luffing Jib 조합은 Hydraulic Main Boom과 별도의 Geometry Model이 필요하다.

개념적으로:

```text
             Luffing Jib
          ──────────────● Load
         /
        ● Boom Tip
       /
      /
     / Main Boom
    /
   ● Crane
```

Main Boom을 높은 각도로 세우고 Jib Geometry를 이용하여 구조물 너머의 Target에 접근할 수 있으므로, 건물과 장비의 배치조건이 Hydraulic Main Boom과 크게 다르다.

따라서 향후 Crawler Luffing 검토에서는 최소 다음을 별도 Configuration으로 다룬다.

```text
Main Boom Length
Main Boom Angle
Luffing Jib Length
Luffing Jib Angle
Counterweight / Derrick Configuration
Target Radius
Target Height
Building Clearance
```

이 기능은 현재 Main Boom PoC 범위에 포함하지 않는다.

---

### 23.8 단면도의 역할

단면도는 Required Height를 얻기 위한 필수 입력이 아니다.

사용자가 Required Height를 직접 입력했다면 해당 값을 사용한다.

단면도의 주요 목적은 향후 다음 Geometry를 확보하는 것이다.

```text
Crane ↔ Building horizontal distance
Building height/profile
Target position
Boom/Jib clearance
Over-building reach geometry
```

초기에는 단면도 없이 사용자가 다음 값을 직접 입력할 수 있다.

```text
Crane reference center ↔ Building 외벽 거리
Building 높이
Building 외벽 ↔ Target 수평거리
Target 높이
```

이 값으로 규칙 기반 Section Geometry를 구성하고 Boom/Building 교차 여부를 계산할 수 있다.

그 다음 단계에서:

```text
Section PDF / PNG
→ Scale Calibration
→ Building / Level / Target 선택
→ Geometry 생성
```

으로 발전시키고, 최종적으로 도면 객체 자동 인식을 검토한다.

---

### 23.9 Interactive Planner의 Capacity Envelope

초기 UI에서 단순히 사용자가 입력한 Radius의 원을 그리는 기능만으로 끝내지 않는다.

장기적으로는:

```text
Gross Load
+
Required Height
+
Crane Configuration
+
Load Chart
+
Geometry
      ↓
Capacity / Reach Envelope
```

를 계산하여 도면 위에 표시한다.

360° 동일 조건에서는 원형에 가까운 Envelope가 가능하지만, Working Area 또는 Configuration별 Capacity가 다르면 방향별 Envelope가 달라질 수 있다.

따라서 내부 데이터 모델에서는 단순 `circle_radius`가 아니라 향후 **Capacity Envelope**를 표현할 수 있도록 한다.

---

### 23.10 Outrigger / Crawler Footprint

도면 기반 Planner에서는 Load Capacity뿐 아니라 장비 설치 가능공간도 확인해야 한다.

표시 대상:

```text
Crane Body
Outrigger Footprint
Crawler Footprint
Rotation / Reference Center
Orientation
```

예를 들어 TRT60의 특정 Outrigger Configuration이 7.0 m × 7.3 m라면 Scale이 설정된 평면도 위에 해당 Footprint를 실제 크기로 표시할 수 있어야 한다.

이를 통해 사용자가 건물, 가설울타리, 도로, 구조물 등의 공간과 장비 설치공간의 충돌 여부를 확인할 수 있다.

향후 자동화 단계에서는 Polygon Collision Check로 확장할 수 있다.

---

### 23.11 실시간 Crane Placement 검토

장기 UI에서는 사용자가 Crane 객체를 Drag/Rotate하면 다음 값을 다시 계산할 수 있다.

```text
Crane Position
      │
      ├─ Radius
      ├─ Reach
      ├─ Capacity
      ├─ Clearance
      └─ Equipment Footprint
              ↓
         Feasibility
```

목표 출력 예:

```text
Radius              27.0 m
Required Height     30.0 m
Gross Load           2.5 t
Rated Capacity       3.4 t
Utilization         73.5 %
Reach               PASS
Clearance           PASS
Footprint           PASS

Result:
CONDITION_MET
```

하나라도 Critical Condition이 실패하면 해당 위치는 적합 위치로 표시하지 않는다.

---

### 23.12 두 UI는 하나의 Engineering Core를 공유

최종 구조:

```text
                    Crane Spec PDF
                          ↓
                    Parser Engine
                          ↓
                    Canonical Schema
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
        Capacity Engine         Geometry Engine
              ↓                       ↓
              └───────────┬───────────┘
                          ↓
                    Lifting Review
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
      Input / Natural Language    Drawing Planner
            Review UI               2D Canvas
```

따라서 UI Mode A와 Mode B를 별도 계산 시스템으로 개발하지 않는다.

**Parser / Canonical Schema / Validation / Capacity / Geometry를 공통 Engineering Core로 만들고 표현 계층만 분리한다.**

---

### 23.13 단계별 제품 확장

```text
Parser PoC
TRT60 PDF
→ Canonical Load Chart JSON

Engineering Review PoC
Gross Load + Radius + Required Height(사용자 입력)
→ Reach + Capacity 판정

Review MVP
PDF + 정형 입력
→ 정형 결과 + 자연어 설명 + Source Evidence

Interactive Planner PoC-A
Plan Scale Calibration

Interactive Planner PoC-B
Crane Drag / Rotate
+ Outrigger Footprint

Interactive Planner PoC-C
Capacity / Reach Envelope

Interactive Planner MVP
도면 기반 Interactive Lifting Planner

Future 1
Section Geometry
+ Boom / Building Clearance

Future 2
Crawler Main Boom + Luffing Jib Geometry

Future 3
Plan + Section 기반 Feasible Placement Zone

Future 4
라이선스가 확보된 Crane DB 기반 장비/Configuration 역제안
```

### 현재 개발범위와의 경계

위 장기설계가 추가되더라도 **현재 Terex TRT60 PoC의 구현범위는 변경하지 않는다.**

현재 PoC에서 구현할 것:

```text
TRT60 PDF
→ Parser
→ Main Boom Load Chart
→ Configuration
→ Table Segment
→ Unit Normalization
→ Canonical JSON
→ Validation
→ Source Traceability
```

현재 PoC에서 구현하지 않을 것:

```text
Plan Drawing Parser
Section Drawing Parser
Canvas
Crane Drag
Collision Detection
Capacity Envelope UI
Luffing Jib
Crawler Geometry
Automatic Placement
```

단, 현재 코드의 Parser/Canonical Model이 향후 Geometry Engine과 분리되어 연결될 수 있도록 모듈 경계를 유지한다.

---

## 24. 다음 개발 단계

### Phase A — Parser PoC (현재)

목표:

```text
Terex TRT60 PDF
→ Configuration-aware Canonical Load Chart Data
→ Validation
→ Source Traceability
→ Deterministic JSON
```

구현 순서:

```text
STEP 1  Common Schema v1 확정
STEP 2  Pydantic Canonical Model 정의
STEP 3  Parser Interface 정의
STEP 4  Terex TRT60 Document Inspector
STEP 5  Page Classifier
STEP 6  Configuration Header Parser
STEP 7  Table Segmenter
STEP 8  Main Boom Load Chart Parser
STEP 9  Unit Normalizer
STEP 10 Golden Dataset 생성
STEP 11 Validation / Fail-Closed Test
STEP 12 Deterministic Output Test
STEP 13 Source Traceability 검증
STEP 14 기존 MeerkatAI 전체 테스트 실행
```

### Phase B — Engineering Review PoC

Parser PoC 성공 후 진행한다.

```text
Required Height   ← 사용자가 직접 입력
Radius
Load / Load Components
Actual Crane Configuration
        ↓
Reach / Geometry
        ↓
Capacity
        ↓
Adjustment / Deduction
        ↓
Engineering Review Result
```

### Phase C — Review MVP

```text
PDF + 정형 입력
→ 검토결과
→ Source Evidence
→ 자연어 설명
```

### Phase D — Interactive Planner PoC

```text
Plan Scale Calibration
→ Crane Drag / Rotate
→ Outrigger/Crawler Footprint
→ Capacity / Reach Envelope
```

### Phase E — Section / Clearance 확장

```text
Section Geometry
→ Boom/Jib ↔ Building Clearance
→ Crawler Luffing Geometry
→ Feasible Placement Zone
```


## 25. 확정된 의사결정 및 잔여 검토사항

### 확정

1. 제품 기능명은 **`양중계획 검토 (Lifting Review)`**를 우선 사용한다.
2. V1은 **Main Boom 중심**으로 한정한다.
3. Parser가 인식한 Counterweight / Support / Working Area / Boom Configuration은 **사용자 확인 단계**를 거친다.
4. 판정 표현은 `조건 충족(정격하중 이내)` / `부적합(초과)` 등 한정적 표현을 사용한다.
5. 개발 Golden Dataset은 엔지니어가 검증하며, 실서비스는 Source Highlight + User Confirmation의 하이브리드 Verification을 사용한다.
6. 임의 선형보간을 기본적으로 금지한다.
7. Geometry / Reach Check와 Capacity Check를 분리한다.
8. 불확실한 Parsing / Unit / Configuration은 검토를 차단하는 Fail-Closed 정책을 사용한다.
9. Parser 결과와 Engineering Review 결과를 분리 저장하고 Version/Audit 정보를 남긴다.

### 잔여 검토

1. 실제 운영에서 원본 PDF의 보존기간은 얼마로 할 것인가?
2. Evidence Snapshot의 저장범위와 라이선스 정책은 어떻게 할 것인가?
3. User Confirmation으로 검토 가능한 Confidence Threshold를 제조사별로 어떻게 설정할 것인가?
4. Main Boom V1에서 Parts of Line / Hook Block 조건을 어느 수준까지 강제할 것인가?
5. Manufacturer-specific Capacity Adjustment Rule을 어떤 문서까지 근거로 허용할 것인가?
6. 장기적으로 제조사 라이선스 확보 후 역제안 기능까지 확장할 것인가?

---

## 26. 현재 결론

현재 확보한 27개 PDF는 Common Schema와 Parser Profile 구조를 설계하기에 충분하다.

기술적 핵심은 OCR 자체가 아니라:

> **각 Load Chart 숫자가 정확히 어떤 Crane Configuration에 속하는지를 오인 없이 구조화하는 것**

이다.

현재 구현은 오직 **Terex TRT60 Parser Vertical Slice PoC**다.

현재 종료점:

```text
TRT60 PDF
→ Configuration Header
→ Table Segment
→ Main Boom Load Chart
→ Unit Normalization
→ Canonical JSON
→ Validation
→ Source Page/BBox
→ Deterministic Output
```

현재 구현하지 않는 것:

```text
Required Height
Reach / Geometry
Capacity Review
Gross Load
User Confirmation
Engineer Approval
Natural Language UI
Plan / Section Planner
```

Parser PoC가 `Critical Error = 0`, Golden Dataset Exact Match, Deterministic Output 조건을 만족한 이후 별도의 **Engineering Review PoC**로 진입한다.

V0.5 핵심 구현 원칙:

> **Parser PoC Scope 고정 / Configuration First / Fail-Closed / No Interpolation / Exact Source Parsing / Deterministic Unit Normalization / Source Traceability / State Separation**

---
---

## 27. v0.5 구현 기준 최종 확정사항

1. **v0.5를 TRT60 Parser PoC의 최종 Implementation Baseline으로 사용한다.**
2. 현재 구현은 `TRT60 PDF → Canonical Data → Validation → Source Traceability`까지다.
3. `Required Height`, Geometry, Reach, Capacity Review는 현재 Parser PoC 범위가 아니다.
4. 향후 Engineering Review에서 **Required Height는 사용자가 직접 입력하는 필수값**이다.
5. 시스템은 Required Height를 자동 추론하거나 임의 보정하지 않는다.
6. 단면도는 향후 Height 산출용이 아니라 Boom/Jib와 구조물의 Clearance/Interference 검토용이다.
7. Load Chart 숫자는 반드시 정확한 Configuration과 연결되어야 한다.
8. Configuration 연결 오류는 Critical Error다.
9. `capacity_basis`는 `load_charts`의 실제 필드로 관리하고 원문 근거를 추적한다.
10. `capacity_basis = UNKNOWN`이면 향후 Engineering Review 자동판정을 차단한다.
11. Manufacturer Deduction/Adjustment는 원문 근거가 있을 때만 적용한다.
12. Chart-level Configuration을 모든 Cell에 중복 저장하지 않는다.
13. Cell의 빈 값/금지/적용불가/파싱오류를 `cell_status`로 구분한다.
14. 수치는 `source_text → parsed_source_value → canonical_value_si`로 관리한다.
15. Parser의 “정확 일치”는 원문 의미의 정확한 파싱을 의미한다.
16. 단위 변환은 deterministic conversion으로 별도 검증한다.
17. Parser Verification / User Confirmation / Engineer Approval은 서로 다른 상태축이다.
18. 현재 Parser PoC는 `parser_verification_status`만 구현한다.
19. Parser PoC Critical Error 허용 목표는 **0건**이다.
20. 동일 PDF + 동일 Parser Profile + 동일 Parser Version은 동일 Canonical Data를 생성해야 한다.
21. Parser PoC 성공 후에만 Engineering Review PoC로 이동한다.
