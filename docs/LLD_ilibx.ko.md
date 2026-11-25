# (LLD) ilibx

| 날짜 | 변경 내용 |
|---|---|
| 2026-11-25 | 초안. 개요(§1~§4)와 구조(§5)를 기존 설계 문서에서 옮겨 채움. 측정값·검증·미정 항목은 TBD. 로케일 데이터 원본 형태(flutter_ilib / iLib JS)는 미정으로 표시 |
| 2026-11-25 | 아직 구현하지 않은 부분(§5.1.2, §5.2.2~§5.2.8, §5.4 사용 예, §5.5)을 비우고 TBD로 둠. 구현하면서 채워 나감 |
| 2026-11-25 | §5를 정해진 컨셉(ilibx-core, ilibx-ffi, ilibx-rust 세 패키지의 존재와 호출 관계)까지만 남기고 나머지(§5.1.3, §5.3, §5.4 포함)를 TBD로 둠 |

> **이 초안에 대해**: [LLD_flutter_ilib](https://github.com/iLib-js/flutter_ilib/blob/develop/doc/design/LLD_flutter_ilib.md)과 같은 형식을 따른다. ilibx는 아직 구현 전이라 측정값, 테스트 링크, 일부 설계 항목은 **TBD**로 둔다. 근거가 되는 결정은 [초기 설계](initial-design.ko.md)와 [데이터 형식과 런타임 구현](data-and-runtime.ko.md)에 있다.
>
> **로케일 데이터 처리 방식은 미정이다(TBD, [§8 #17](#8-미결-사항))**. 원본을 flutter_ilib 형태(로케일별 파일 하나에 모든 데이터 종류)로 쓸지, iLib JS 형태(로케일 디렉터리 아래 데이터 종류별 파일)로 쓸지 검토와 추가 조사가 필요하다. 데이터 원본, 섹션 선택, 조회 규칙, 생성 단계에 관한 서술은 flutter_ilib 형태를 가정한 안이며, 해당 부분에 따로 표시했다.

## 1. 문서 설명 (Document Descriptions)

### 1.1 문서의 목적

ilibx는 webOS Native 앱(Rust, C/LVGL 등)용 i18n 라이브러리다. webOS의 Enact·QML·Node.js·Flutter 앱이 iLib 계열 라이브러리로 얻는 날짜·숫자·시간대 등의 로케일별 결과를 Native 앱에서도 똑같이 얻게 한다. flutter_ilib v2.0(순수 Dart)의 로직을 Rust로 옮기고, 기기에 공용 `.so` 하나와 데이터 파일 하나만 두어 모든 앱이 공유한다.

이 문서는 ilibx의 구현·검증·리뷰에서 공통으로 참조하는 저수준 설계를 정리한다.

### 1.2 문서의 범위

대상: ilibx 초기 버전(v0.1.0 예정). 로케일 데이터 원본의 형태(flutter_ilib `assets/locale/` / iLib JS `js/data/locale/`)는 TBD다(§8 #17). 기존 검토는 flutter_ilib `assets/locale/`(오픈소스 2.0.0 `de16084`, webOS판 `9470596`)을 기준으로 했다.

**포함**

- 공개 인터페이스: C ABI(`libilibx.so`, `ilibx.h`)와 Rust 앱용 호출 코드(ilibx-rust)
- 코어 로직(ilibx-core): 포맷, 달력, 시간대, 복수형, 로케일 데이터 조회
- 데이터 파일 `locale.bin`의 형식과 생성 도구(datagen), 덤프 도구(ilibx-dump)
- 런타임 동작(mmap 로딩, 로케일 체인 조회)
- 저장소·패키지 구조, 빌드·배포 형태, 테스트·CI 구조

**제외**

- iLib JS와 flutter_ilib의 내부 구현 (결과 일치의 기준으로만 참조)
- CLDR과 ilib-assemble의 내부 동작
- ilibx를 쓰는 개별 앱, LVGL 자체, webOS 플랫폼과 Yocto 빌드 시스템
- 번역 문자열(ResBundle) 처리. webOS에서는 libwebosi18n이 맡는다

> **참고**: 구현 언어(C vs Rust)와 공유 구성을 고른 근거, 검토한 대안은 [초기 설계](initial-design.ko.md)에 있다. 이 문서는 그 결정을 전제로 한다.

### 1.3 문서의 구성

| 장 | 제목 | 내용 |
|---|---|---|
| 1 | 문서 설명 | 목적, 범위, 구성, 용어 |
| 2 | 프로젝트 개요 | 이해관계자 |
| 3 | 아키텍처 동인 | 제약 사항, 기능 요구사항, 품질 속성 |
| 4 | 시스템 컨텍스트 | 시스템 경계와 외부 엔티티 |
| 5 | 아키텍처 설계 | 정적(모듈), 동적(C&C), 물리(배치) 관점, 인터페이스와 데이터 형식 |
| 6 | FMEA 리뷰 | 고장 모드와 런타임 대응 |
| 7 | 제품군 고려 사항 | 제품군에 미치는 영향 |
| 8 | 미결 사항 | 정하지 않은 항목 |
| 9 | 참고 자료 | 참고 문서 |

flutter_ilib LLD 구성에 §5.4(인터페이스 명세), §5.5(데이터 형식), §8(미결 사항)을 더했다. ilibx는 C ABI가 앱과의 계약이고 데이터 파일 형식을 직접 정의하기 때문이다.

### 1.4 용어와 정의

| 용어 | 설명 |
|---|---|
| iLib | webOS의 JS i18n 라이브러리. CLDR 데이터를 가공한 로케일 데이터와 포맷 로직을 가진다 |
| flutter_ilib | iLib을 Dart로 옮긴 Flutter용 i18n 패키지. ilibx의 결과 일치 기준 |
| webOS판 (flutter_ilib_webos) | webOS 커스텀 데이터 오버레이를 적용한 flutter_ilib |
| CLDR | Unicode Common Locale Data Repository. iLib 로케일 데이터의 원천 |
| BCP-47 | 로케일 태그 표준 (예: `ko-KR`, `zh-Hant-TW`) |
| C ABI | C 언어 방식의 함수 호출 규약. 거의 모든 언어가 이 방식으로 다른 라이브러리를 부를 수 있어 공용 라이브러리의 입구로 쓴다 |
| crate / Cargo 패키지 | Rust 빌드 도구(Cargo)가 한 번에 빌드하는 코드 묶음 |
| cdylib | C ABI로 공개되는 Rust 공유 라이브러리 형태. `libilibx.so`가 이 형태다 |
| soname | 공유 라이브러리의 ABI 버전이 붙은 이름 (`libilibx.so.1`) |
| `no_std` | Rust 표준 라이브러리 중 OS가 필요한 부분(파일, 시간, 스레드 등)을 쓰지 않는다는 선언 |
| alloc | `no_std`에서도 쓸 수 있는 힙 할당 기능(`String`, `Vec` 등) |
| mmap | 파일을 메모리 주소 공간에 매핑하는 OS 기능. 같은 파일을 매핑한 프로세스끼리 물리 페이지를 공유한다 |
| `locale.bin` | 로케일 JSON을 빌드 때 변환한 바이너리 데이터 파일. 기기에 한 벌 |
| 문서 (document) | `locale.bin` 안에서 원본 JSON 파일 하나에 해당하는 값 트리 (`root`, `ko`, `und-KR` 등) |
| 로케일 체인 | 한 로케일의 데이터를 찾을 때 거치는 문서 목록 (root → lang → … → lang-script-region) |
| 값 참조 | `locale.bin`에서 값 하나를 가리키는 32비트 정수 (하위 3비트 종류 + 29비트 값·위치) |
| 허용 목록 | 생성기가 `locale.bin`에 넣는 데이터 섹션 목록 |
| PSS | Proportional Set Size. 공유 메모리를 공유 프로세스 수로 나눠 계산한 메모리 사용량 |
| FMEA | Failure Mode and Effects Analysis. 고장 모드와 영향 분석 |

## 2. 프로젝트 개요 (Project Overview)

ilibx는 다음 여섯 조건을 모두 만족하는 Native i18n 라이브러리를 목표로 한다(상세: [초기 설계 "목적과 조건"](initial-design.ko.md#목적과-조건)).

1. 확장성: Rust, LVGL 등 새 Native 플랫폼에 쉽게 대응. OS 없는 MCU 가능성도 고려
2. 커스텀 데이터: webOS 커스텀 데이터를 빌드 때 합침
3. 공유: 기기에 라이브러리와 데이터를 한 벌만 두고 모든 앱이 공유
4. 메모리: 사용량이 적고 관리가 안전함
5. ICU 의존 0: ICU4C, ICU4X 계열 crate, ICU 바인딩 모두 쓰지 않음
6. 단일 버전: 모든 앱이 같은 버전의 라이브러리와 데이터를 씀

이 조건에서 나온 구성은 **공용 `.so` 하나 + C ABI + 공용 데이터 파일 한 벌 + 빌드 때 webOS 커스텀을 합친 데이터**이고, 구현 언어는 Rust다(11-19 결정).

### 2.1 이해관계자

| 역할 | 이해관계자 |
|---|---|
| 프로젝트 리더 | TBD |
| 아키텍트 | TBD |
| 개발자 | TBD |
| SDET | TBD |
| 사용자 (앱 개발자) | webOS Native 앱(Rust, C/LVGL) 개발자. 나중에 Flutter(Dart FFI) 등 |

## 3. 아키텍처 동인 (Architectural Drivers)

### 3.1 제약 사항

#### 3.1.1 비즈니스 제약

**[표 3-1]** 비즈니스 제약

| ID | 제약 | 설명 |
|---|---|---|
| BC01 | 오픈소스 라이선스 (Apache-2.0) | 저장소는 Apache License 2.0으로 배포한다. 기여와 재배포는 라이선스를 따른다 |
| BC02 | iLib·flutter_ilib과 결과 일치 | 같은 로케일·같은 입력에 iLib·flutter_ilib과 같은 결과를 낸다. 정확도보다 일치가 우선이다(예: 과거 날짜 서머타임도 iLib과 같게). 판단 기준은 flutter_ilib 테스트 기대값(21,527건) |
| BC03 | webOS 커스텀 데이터 반영 | flutter_ilib webOS판과 결과가 같아야 한다. 커스텀은 빌드 때 합치며, 앱별 런타임 오버라이드는 두지 않는다 |
| BC04 | webOS 지원 로케일 | flutter_ilib과 같은 로케일을 지원한다. 데이터 파일 252개(webOS판 265개). 로케일 목록 확정 TBD |
| BC05 | 업스트림 버전 정렬 | 로직은 flutter_ilib v2.0(iLib JS v15.0.0, CLDR 48.2 기준)에서 옮긴다. 데이터 원본(flutter_ilib `assets/locale/` / iLib JS `js/data/locale/`)은 TBD(§8 #17). 로직과 데이터는 함께 갱신한다 |

\*BC: Business Constraint

#### 3.1.2 기술 제약

**[표 3-2]** 기술 제약

| ID | 제약 | 설명 |
|---|---|---|
| TC01 | Rust 구현, ICU 의존 0 | 주 언어는 Rust. ICU4C, ICU4X 계열 crate(zerovec, yoke 등 범용 유틸리티 포함), ICU 바인딩을 빌드·링크·데이터 어디에도 쓰지 않는다. cargo-deny와 `readelf`로 검사 |
| TC02 | C ABI로 공개 | 공개 인터페이스는 C ABI 하나다. Rust 앱도 ilibx-rust를 거쳐 C ABI를 부른다 |
| TC03 | 공유 라이브러리 + 공용 데이터 한 벌 | `libilibx.so`(cdylib)와 `/usr/share/ilibx/locale.bin`을 기기에 한 벌씩 둔다. 둘은 같은 릴리스·같은 패키지로 배포한다 |
| TC04 | 단일 버전 | 앱이 코어 로직을 정적으로 포함하지 않는다. ilibx-rust는 ilibx-core·ilibx-ffi를 의존하지 않는다 |
| TC05 | 코어는 `no_std` + alloc | ilibx-core는 OS 기능을 쓰지 않는다. 데이터는 `&[u8]`로만 받고, 파일·mmap·시간 조회는 입구 패키지가 맡는다 |
| TC06 | 최소 Rust 버전 | webOS Yocto의 rustc 버전에 맞춘다. 버전과 edition TBD |
| TC07 | 대상 플랫폼 | webOS Linux (armv7). 개발·테스트는 x86_64 Linux. MCU는 가능성만 고려 |
| TC08 | 최소 의존 | 외부 crate는 최소로 둔다(libm 등). 추가 시 `no_std` 지원과 ICU 의존 0을 먼저 확인하고 `Cargo.lock`을 고정한다 |
| TC09 | 기기에 JSON 파서 없음 | JSON은 빌드 머신의 생성기에서만 읽는다. 기기의 `.so`는 `locale.bin`만 읽는다 |

\*TC: Technical Constraint

### 3.2 기능 요구사항

flutter_ilib LLD의 FR ID(FR1~FR13)를 그대로 써서 두 라이브러리의 요구사항을 1:1로 맞춰 볼 수 있게 한다. ilibx에만 있는 요구사항은 FR14부터 둔다. Native API 범위는 아직 확정하지 않았으므로(§8 #1) 아래 표는 후보 목록이다.

**[표 3-3]** 기능 요구사항

| 그룹 | ID | 기능 | 설명 | 테스트 시나리오 |
|---|---|---|---|---|
| 데이터 로딩 | FR1-1 | 초기 데이터 로딩 | 첫 API 호출 때 `locale.bin`을 mmap하고 헤더를 검사한다. 동기 방식이며 "준비 완료" 상태가 없다 (flutter_ilib은 비동기 로딩 후 알림) | TBD |
| | FR1-2 | 로케일 변경 | 라이브러리는 현재 로케일을 기억하지 않는다. 로케일이 바뀌면 앱(또는 플랫폼별 계층)이 포맷터를 새로 만든다 | TBD |
| | FR1-3 | 기본 로케일 | C ABI가 상태를 갖지 않으므로 기본 로케일 처리 방식 TBD (호출마다 명시 / 시스템 로케일 조회) | TBD |
| | FR1-4 | 로케일 데이터 조회 | 로케일 체인을 따라 구체적인 데이터부터 찾아 iLib·flutter_ilib의 병합과 같은 결과를 낸다. 세부 방식은 데이터 원본 형태에 따라 TBD (§5.2.5, §8 #17) | TBD |
| | FR1-5 | 로케일 데이터 해제 | 해당 없음. 매핑은 프로세스가 끝날 때까지 유지하고 해제하지 않는다 | — |
| 로케일 | FR2-1 | BCP-47 파싱 | 로케일 태그를 파싱·정규화·검증한다 | TBD |
| | FR2-2 | 사용 가능한 로케일 | `locale.bin`에 있는 로케일 목록을 돌려준다 | TBD |
| 로케일 정보 | FR3-1 | 로케일 메타데이터 | 시계, 달력, 시간대, 통화, 구분 기호, 숫자 등 로케일 관례를 돌려준다 | TBD |
| 날짜 포맷 | FR4-1 | 날짜·시간 포맷 | 로케일 패턴과 옵션으로 시각을 문자열로 바꾼다 | TBD |
| | FR4-2 | 달력별 포맷 | 포맷 전에 포맷터의 달력으로 날짜를 바꾼다 (예: fa-IR 페르시아력) | TBD |
| | FR4-3 | 이름과 숫자 현지화 | 월·요일·연호·오전오후 이름과 현지 숫자를 쓴다 | TBD |
| | FR4-4 | 포맷 메타데이터 | 패턴, 시계, 달력, 구성 요소 순서 등을 돌려준다 | TBD |
| 달력 | FR5-1 | 달력 규칙 | flutter_ilib이 지원하는 달력의 월 수, 월 길이, 윤년 규칙 | TBD |
| | FR5-2 | 달력 간 변환 | Rata Die / Julian Day를 거쳐 달력 간 날짜를 바꾼다 | TBD |
| | FR5-3 | 지원하지 않는 달력 | 오류 코드로 알린다 (flutter_ilib의 `UnimplementedError`·`ArgumentError`에 해당) | TBD |
| 시간대 | FR6-1 | 오프셋과 서머타임 | iLib zoneinfo 데이터로 오프셋, 서머타임, 표시 이름을 계산한다. ICU에 위임하지 않는다 | TBD |
| | FR6-2 | 시스템 시간대 | `local`은 ilibx-ffi가 libc(`localtime_r`) 또는 `/etc/localtime`으로 읽는다 | TBD |
| | FR6-3 | 시간대 목록 | 시간대 ID 목록을 돌려준다(국가별 선택 가능) | TBD |
| 숫자 포맷 | FR7-1 | 숫자 포맷 | 구분 기호, 그룹, 숫자, 반올림 등 옵션으로 숫자를 포맷한다 | TBD |
| | FR7-2 | 백분율 포맷 | 로케일 백분율 패턴을 쓴다 | TBD |
| | FR7-3 | 통화 포맷 | 통화 기호·코드와 소수 자릿수를 쓴다. 통화 코드가 없거나 모르면 오류 | TBD |
| 통화 | FR8-1 | 통화 메타데이터 | 코드, 이름, 기호, 소수 자릿수 | TBD |
| 기간 포맷 | FR9-1 | 기간 포맷 (텍스트) | 로케일 복수형 규칙으로 기간을 포맷한다 | TBD |
| | FR9-2 | 기간 포맷 (시계) | 시:분:초 형식 | TBD |
| | FR9-3 | RTL 출력 | RTL 로케일에 U+200F를 붙인다 | TBD |
| 국가 | FR10-1 | 국가 조회 | 국가 코드 ↔ 현지화된 이름, 목록 | TBD |
| 스크립트 | FR11-1 | 스크립트 메타데이터 | ISO 15924 코드, 번호, 이름, 방향, IME 필요 여부, 대소문자 유무 | TBD |
| 대소문자 | FR12-1 | 대소문자 변환 | 언어별 예외(터키어 i, 독일어 ß, 그리스어 마지막 시그마)는 iLib 데이터, 나머지는 Rust `core`로 처리 (§8 #8) | TBD |
| 버전 | FR13-1 | 버전 정보 | 라이브러리 버전과 `locale.bin` 헤더의 원본 정보(flutter_ilib 커밋, CLDR 버전, 생성기 버전)를 돌려준다 | TBD |
| C ABI | FR14-1 | 포맷터 수명 | 포맷터는 만들기·쓰기·해제 세 함수로 다룬다 | TBD |
| | FR14-2 | 결과 전달 | 결과는 호출한 쪽 버퍼에 UTF-8로 쓴다. 버퍼가 부족할 때의 동작 TBD | TBD |
| | FR14-3 | 오류 전달 | 오류는 숫자 코드로 알린다. panic은 C ABI 경계를 넘지 않는다 | TBD |
| Rust 앱 | FR15-1 | ilibx-rust | Rust 앱이 포인터·버퍼·해제를 다루지 않고 ilibx를 쓴다 (`DateFmt::new`, `format`, `Drop`에서 해제) | TBD |
| 데이터 도구 | FR16-1 | 데이터 생성 | 허용 목록의 섹션만 골라 JSON → `locale.bin`으로 변환한다 | TBD |
| | FR16-2 | 데이터 덤프 | `locale.bin`의 헤더, 체인, 경로별 값을 출력한다 (`ilibx-dump`) | TBD |

### 3.3 품질 속성

각 품질 속성의 목표값과, 목표값을 정하는 기준은 아직 정하지 않았다(TBD, §8 #15). 표의 "참고" 값은 비교용으로 적은 것이며 목표값이 아니다.

**[표 3-4]** 품질 속성

| ID | 속성 | 시나리오 | 테스트 케이스 | 난이도 | 중요도 |
|---|---|---|---|---|---|
| QA01 | 메모리 (공유 효과) | 같은 기능의 앱 1개·2개를 띄웠을 때 PSS 합계 증가가 JSON 방식보다 작다. 목표값 TBD | TC-QA01 | TBD | TBD |
| QA02 | 성능 (첫 호출) | 첫 API 호출(매핑 + 헤더 검사)까지 걸리는 시간. 목표값 TBD | TC-QA02 | TBD | TBD |
| QA03 | 성능 (날짜 포맷) | 재사용하는 포맷터의 `format()` 평균 시간. 목표값 TBD (참고: flutter_ilib v2.0 O26 309 µs/op) | TC-QA03 | TBD | TBD |
| QA04 | 크기 | `libilibx.so`와 `locale.bin` 크기. 목표값 TBD (참고: 공통 데이터는 섹션 선택으로 0.72 MB → 약 0.12 MB) | TC-QA04 | TBD | TBD |
| QA05 | 안전성 | `unsafe`는 C ABI 경계와 mmap 로더에만 둔다. 잘못된 데이터·입력에서 panic 없이 오류 코드를 돌려준다 | TC-QA05 | TBD | TBD |

#### 3.3.1 벤치마크 테스트 케이스

TBD. 측정 방법(PSS)은 [데이터 형식과 런타임 구현 §7.1](data-and-runtime.ko.md#71-메모리-효과-측정-pss)을 따른다.

## 4. 시스템 컨텍스트 (System Context)

ilibx는 빌드 시점과 기기 런타임 두 영역에 걸쳐 있다. 빌드 시점에는 로케일 데이터 원본(형태 TBD, §8 #17)을 `locale.bin`으로 바꾸고, 기기에서는 여러 언어의 앱이 같은 `libilibx.so`를 C ABI로 부른다.

**[그림 4-1]** 시스템 컨텍스트 다이어그램

```mermaid
graph LR
    subgraph build["빌드 시점 (빌드 머신·CI)"]
        SRC["로케일 데이터 원본 (TBD)<br/>flutter_ilib 형태 / iLib JS 형태<br/>+ webOS 커스텀"]
        GEN["ilibx datagen"]
        SRC --> GEN
    end

    subgraph device["기기 (webOS Linux)"]
        RUST["Rust 앱<br/>(ilibx-rust)"]
        CAPP["C / LVGL 앱<br/>(ilibx.h)"]
        FLUT["Flutter 앱<br/>(Dart FFI, 나중에)"]
        OTHER["Python·Node 등<br/>(나중에)"]
        SO["libilibx.so<br/>(ilibx)"]
        BIN[("/usr/share/ilibx/<br/>locale.bin")]
        LIBC["libc<br/>/etc/localtime"]

        RUST --> SO
        CAPP --> SO
        FLUT -.-> SO
        OTHER -.-> SO
        SO -->|mmap| BIN
        SO -->|시스템 시간대| LIBC
    end

    GEN -->|패키지로 설치| BIN
```

> **표기**: 실선은 초기 버전의 관계, 점선은 나중에 생길 수 있는 관계다.

**[표 4-1]** 엔티티

| 엔티티 | 책임 |
|---|---|
| ilibx (`libilibx.so`) | 이 문서의 대상. C ABI로 날짜·숫자·시간대 등 로케일별 포맷과 정보를 제공한다 |
| `locale.bin` | 빌드 때 만든 로케일 데이터. 읽기 전용, 기기에 한 벌 |
| 로케일 데이터 원본 | webOS 커스텀이 적용된 로케일 JSON. flutter_ilib_webos `assets/locale/`(로케일별 파일) 또는 iLib JS `js/data/locale/`(로케일 디렉터리 아래 데이터 종류별 파일) 중 TBD |
| datagen | JSON을 `locale.bin`으로 바꾸는 생성기. 빌드 머신에서만 실행 |
| Rust 앱 | ilibx-rust로 ilibx를 쓰는 webOS Native 앱 |
| C / LVGL 앱 | `ilibx.h`를 보고 C 함수를 바로 부르는 앱 |
| Flutter 앱, 기타 언어 앱 | 나중에 언어별 호출 코드로 ilibx를 쓸 수 있는 앱 |
| libc | 시스템 시간대(`localtime_r`, `/etc/localtime`)를 제공 |

**[표 4-2]** 관계

| 관계 | 책임 |
|---|---|
| 앱 → `libilibx.so` | C ABI 함수 호출. 같은 프로세스 안의 동적 링크이며 IPC가 없다 |
| `libilibx.so` → `locale.bin` | 읽기 전용 mmap. 여러 프로세스가 페이지 캐시를 공유한다 |
| `libilibx.so` → libc | 시스템 시간대 조회 |
| 데이터 원본 → datagen → `locale.bin` | 빌드 때 데이터 선택, 중복 제거, 인코딩. 기기에서는 데이터만 따로 갱신하지 않는다 |

## 5. 아키텍처 설계 (Architecture Design)

### 5.1 정적 관점 (Static Perspectives)

#### 5.1.1 1차 분해 다이어그램

> **상태**: 지금 정해진 것은 패키지 세 개(ilibx-core, ilibx-ffi, ilibx-rust)가 있다는 컨셉까지다. 패키지별 세부(crate-type, 의존 규칙, 도구·테스트 구성)는 TBD이며, 지금까지 검토한 안은 [초기 설계 §3.1](initial-design.ko.md#31-패키지-구성과-rust-앱의-사용-방식)과 [데이터 형식과 런타임 구현 §1](data-and-runtime.ko.md#1-저장소와-패키지-구조)에 있다.

**[그림 5-1]** 1차 분해 (패키지 컨셉)

```mermaid
graph TD
    RS["ilibx-rust<br/>Rust 앱용 호출 코드"]
    FFI["ilibx-ffi<br/>C ABI 레이어"]
    CORE["ilibx-core<br/>실제 동작 코드"]
    CAPP["C / LVGL 앱"]
    RAPP["Rust 앱"]

    RAPP --> RS
    RS -->|C ABI| FFI
    CAPP -->|C ABI| FFI
    FFI --> CORE
```

**[표 5-1]** 1차 분해 요소 책임

| 요소 | 책임 |
|---|---|
| ilibx-core | 실제 동작 코드(포맷, 달력, 시간대 등 로케일별 로직) |
| ilibx-ffi | C ABI 레이어. 모든 앱이 부르는 입구이며, 기기에서 공유하는 라이브러리가 된다 |
| ilibx-rust | Rust 앱이 C ABI를 직접 다루지 않고 ilibx를 쓰게 하는 호출 코드 |

*관련 그림: [그림 5-1]* · 관점: 정적

#### 5.1.2 2차 분해 다이어그램 (ilibx-core 내부)

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 채운다. 지금까지 검토한 안은 [데이터 형식과 런타임 구현 §1](data-and-runtime.ko.md#1-저장소와-패키지-구조)(패키지 구조), [§2.1](data-and-runtime.ko.md#21-사용-섹션과-미사용-섹션)(모듈별 사용 데이터)에 있다.

#### 5.1.3 저장소 구조

TBD. 패키지 세 개를 한 저장소에 두는 것 외에는 정하지 않았다. 지금까지 검토한 안은 [데이터 형식과 런타임 구현 §1](data-and-runtime.ko.md#1-저장소와-패키지-구조)에 있다.

### 5.2 동적 관점 (Dynamic Perspectives)

#### 5.2.1 런타임 구성 요소

**[그림 5-2]** 호출 흐름 (컨셉)

```mermaid
graph LR
    RAPP["Rust 앱"] --> RS["ilibx-rust"]
    RS -->|C ABI| FFI["ilibx-ffi"]
    CAPP["C / LVGL 앱"] -->|C ABI| FFI
    FFI --> CORE["ilibx-core"]
```

**[표 5-2]** 연결 책임

| 연결 | 책임 |
|---|---|
| Rust 앱 → ilibx-rust → ilibx-ffi | Rust 앱은 ilibx-rust를 거쳐 C ABI를 부른다 |
| C / LVGL 앱 → ilibx-ffi | C 앱은 C ABI를 바로 부른다 |
| ilibx-ffi → ilibx-core | C ABI로 받은 요청을 코어 로직으로 넘긴다 |

*관련 그림: [그림 5-2]* · 관점: 동적

데이터 로딩, 값 변환, 오류 처리, 스레드 안전성 등 세부 동작은 TBD.

#### 5.2.2 초기화 시퀀스

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 채운다. 지금까지 검토한 안은 [데이터 형식과 런타임 구현 §5.1](data-and-runtime.ko.md#51-단계)에 있다.

#### 5.2.3 로케일 변경 시퀀스

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 채운다. 지금까지 검토한 안은 [데이터 형식과 런타임 구현 §5.4](data-and-runtime.ko.md#54-로케일-변경-알림)에 있다.

#### 5.2.4 날짜 포맷 시퀀스

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 시퀀스 그림과 단계 표를 채운다.

#### 5.2.5 로케일 데이터 조회

TBD. 아직 구현하지 않았고, 로케일 데이터 처리 방식(§8 #17)도 정해지지 않아 비워 둔다. 지금까지 검토한 안(파일 단위 문서 + 조회 때 겹쳐 보기)은 [데이터 형식과 런타임 구현 §3.4](data-and-runtime.ko.md#34-로케일-병합-방식-파일-단위-문서--조회-때-겹쳐-보기)에 있다.

#### 5.2.6 숫자·기간 포맷

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 시퀀스 그림과 단계 표를 채운다.

#### 5.2.7 매핑 상태

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 채운다. 지금까지 검토한 안은 [데이터 형식과 런타임 구현 §5.1](data-and-runtime.ko.md#51-단계)에 있다.

#### 5.2.8 데이터 생성 파이프라인 (빌드 시점)

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 채운다. 지금까지 검토한 안은 [데이터 형식과 런타임 구현 §4](data-and-runtime.ko.md#4-생성-파이프라인-빌드-시점)에 있다.

### 5.3 물리 관점 (Physical Perspectives)

TBD. 아직 구현하지 않아 비워 둔다. 기기에 라이브러리와 데이터를 한 벌씩 두고 공유한다는 구성 방향은 [초기 설계 §3](initial-design.ko.md#3-권장-구성)에 있고, 배포·패키징 세부는 정하지 않았다.

### 5.4 인터페이스 명세 (C ABI)

TBD. 아직 구현하지 않아 비워 둔다. 지금까지 검토한 C 함수 설계 원칙(만들기·쓰기·해제, UTF-8, 호출자 버퍼, 숫자 오류 코드, 콜백 없음)은 [초기 설계 §3.1](initial-design.ko.md#31-패키지-구성과-rust-앱의-사용-방식)에 있다.

### 5.5 데이터 형식 (`locale.bin`)

TBD. 아직 구현하지 않아 비워 둔다. 구현하면서 채운다. 지금까지 검토한 안은 [데이터 형식과 런타임 구현 §3](data-and-runtime.ko.md#3-localebin-형식)에 있다.

## 6. FMEA 리뷰 (FMEA Review)

> **안내**: 고장 모드는 이 모듈을 쓰는 쪽이 고장으로 느끼는 현상이다.
> 1. 이 모듈의 오류나 다른 모듈 때문에 생기는 고장 모드와 증상을 찾는다.
> 2. 그것을 막거나 피하는 런타임 대응을 정한다.
> 3. 대응을 검증하는 테스트 케이스를 정한다(필수).

> **상태**: 고장 모드와 대응은 기존 설계 문서에서 뽑은 후보다. 심각도와 검증 테스트는 TBD.

**[표 6-1]** ilibx 자체로 인한 고장 모드

| 고장 모드 | 증상 | 원인 | 심각도 | 대응 (런타임) | 검증 (TC) |
|---|---|---|---|---|---|
| 앱 프로세스 종료 | 포맷 호출 중 앱이 죽음 | Rust panic이 C ABI 경계를 넘음 | TBD | 경계에서 `catch_unwind`, 코어를 panic 없이 작성, 오류 코드 반환 | TBD |
| 잘못된 메모리 접근 | 앱 크래시 또는 잘못된 문자열 | `locale.bin` 오프셋·길이 해석 오류 | TBD | 모든 읽기를 `slice.get(..)`로 경계 검사, 실패 시 오류 | TBD |
| flutter_ilib과 결과 다름 | 같은 로케일에서 앱 스택마다 다른 표시 | 이식 오류, 조회 규칙 차이 | TBD | 기대값 21,527건을 JsonLoader·MmapLoader 양쪽으로 CI 검사 | TBD |
| 대소문자 결과 다름 | 일부 문자의 대소문자가 flutter_ilib과 다름 | Dart와 Rust의 Unicode 버전 차이 | TBD | TBD (§8 #8: 대소문자 표를 iLib 데이터로 만들지) | TBD |
| 페르시아력 날짜 다름 | fa-IR 날짜가 하루 어긋남 등 | libm 삼각함수 결과가 Dart와 다름 | TBD | TBD (§8 #9) | TBD |
| 버퍼 부족 | 결과가 잘리거나 빈 문자열 | 호출자 버퍼가 결과보다 작음 | TBD | TBD (필요 길이 반환 등) | TBD |

**[표 6-2]** 다른 모듈·환경으로 인한 고장 모드

| 고장 모드 | 증상 | 원인 | 심각도 | 대응 (런타임) | 검증 (TC) |
|---|---|---|---|---|---|
| 데이터 파일 없음·손상 | 모든 포맷 호출 실패 | 설치 누락, 파일 손상 | TBD | 매핑 때 헤더 검사(매직, 형식 버전, 크기). 이후 처리 TBD(§8 #6) | TBD |
| `.so`와 데이터 버전 불일치 | 오류 또는 잘못된 결과 | 둘을 따로 배포·갱신 | TBD | 같은 패키지로 배포, 헤더의 형식 버전 검사 | TBD |
| 구버전 앱 동작 불가 | 앱 시작 실패(심볼 없음) | C 함수 이름·인자 변경 | TBD | 함수 추가만 허용, 변경·삭제 시 soname 변경, `struct_size` | TBD |
| 잘못된 로케일·시간대 입력 | 기대와 다른 결과 | 앱이 잘못된 태그나 시간대 ID를 넘김 | TBD | `_new`에서 오류 코드 반환 | TBD |
| 시스템 시간대 읽기 실패 | `local` 시간대 결과가 틀림 | `/etc/localtime` 없음 등 | TBD | TBD (flutter_ilib은 모르는 시간대를 Etc/UTC로 대체) | TBD |
| ICU 의존 유입 | 조건 5 위반, 결과 차이 가능 | 간접 의존 crate가 ICU4X 계열을 끌어옴 | TBD | (빌드 시점) cargo-deny 금지 목록, `icu_` 접두어 검사, `readelf -d`로 `libicu*` 참조 확인 | TBD |
| 해제 후 사용 | 앱 크래시 | C 앱이 `_free` 뒤 핸들을 다시 씀 | TBD | Rust 앱은 ilibx-rust의 `Drop`으로 방지. C 앱은 API 문서로 안내 | TBD |

DRBFM: TBD.

## 7. 제품군 고려 사항 (Product-Line Considerations)

**[표 7-1]** 제품군 점검

| No | 점검 항목 | 내용과 관련 자료 |
|---|---|---|
| 7.1 | 대상 제품군을 파악했는가 | webOS TV의 Native 앱(Rust, C/LVGL). 나중에 Flutter 앱(Dart FFI). LVGL을 쓰는 MCU 제품은 계획은 없지만 가능성을 고려한다 |
| 7.2 | 제품군별 요구 차이를 파악했는가 | webOS 안에서는 제품군별 분기가 없다. 결과는 로케일 데이터와 넘긴 옵션으로만 정해진다. MCU는 입구(ilibx-mcu, `libilibx.a`)와 데이터 구성(생성기 MCU 프로파일)만 다르고 코어는 같다 |
| 7.3 | 다른 제품군에 미치는 영향을 고려했는가 | 공용 라이브러리라 변경이 기기의 모든 앱에 영향을 준다. flutter_ilib 기대값 테스트, ABI 호환 규칙(soname), CI의 `no_std` 빌드로 회귀를 막는다 |

## 8. 미결 사항

| # | 내용 | 관련 절 |
|---|---|---|
| 1 | Native API 범위 확정 (FR 목록) | §3.2 |
| 2 | 생성기 구현 언어 (Rust / Python) | §5.2.8 |
| 3 | 생성 시점 (빌드할 때 / 릴리스할 때) | §5.2.8 |
| 4 | 키 번호 폭 (u16 / u32) | §5.5 |
| 5 | 매핑 때 CRC32 검사 여부 | §5.2.2 |
| 6 | `locale.bin`이 없거나 깨졌을 때 처리 | §5.2.2, §5.2.7 |
| 7 | 섹션 허용 목록 확정 | §5.1.2 |
| 8 | 기본 대소문자 변환을 Rust `core`에 맡길지, iLib 데이터로 표를 만들지 | FR12-1, §6 |
| 9 | libm 삼각함수 결과가 Dart와 같은지 | §6 |
| 10 | 기본 로케일 처리 방식 | FR1-3 |
| 11 | 핸들의 스레드 안전성 보장 범위 (`Send`/`Sync`) | §5.2.1 |
| 12 | C 함수 목록, 오류 코드, 버퍼 부족 처리 | §5.4 |
| 13 | 체인 전역 캐시를 둘지 | §5.2.4 (TBD) |
| 14 | webOS Yocto의 rustc 버전 → 최소 지원 Rust 버전과 edition | TC06 |
| 15 | 품질 속성 목표값, 목표값을 정하는 기준, 벤치마크 절차 | §3.3 |
| 16 | 데이터 원본·기대값을 저장소에 가져오는 방식 | §5.1.3 |
| 17 | **로케일 데이터 처리 방식: flutter_ilib 형태(로케일별 파일 하나에 모든 데이터 종류) / iLib JS 형태(로케일 디렉터리 아래 데이터 종류별 파일).** 검토와 추가 조사 필요 | §1.2, BC05, FR1-4, §4, §5.1.2, §5.2.5, §5.2.8, §5.5 |
| 18 | MCU에서 제공할 기능 범위 | §7 |
| 19 | Rust 공유 구성 PoC: cdylib + ilibx-rust + 앱 2개로 NEEDED·심볼·매핑 확인 | §5.3, TC03 |
| 20 | ilibx 이름 중복(npm·crates.io·사내 저장소)과 C 심볼 접두어 `ilibx_` 충돌 확인 | §5.4 |

## 9. 참고 자료 (Reference)

| 자료 | 링크 |
|---|---|
| ilibx 초기 설계 | [initial-design.ko.md](initial-design.ko.md) |
| ilibx 데이터 형식과 런타임 구현 | [data-and-runtime.ko.md](data-and-runtime.ko.md) |
| flutter_ilib | https://github.com/iLib-js/flutter_ilib |
| LLD flutter_ilib | https://github.com/iLib-js/flutter_ilib/blob/develop/doc/design/LLD_flutter_ilib.md |
| iLib | https://github.com/iLib-js/iLib |
| CLDR | https://cldr.unicode.org/ |
