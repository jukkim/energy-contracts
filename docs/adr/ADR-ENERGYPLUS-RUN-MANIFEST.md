# ADR: 표준 HVAC EnergyPlus 실행 manifest

설비가 확인되지 않은 건물은 하나의 HVAC를 사실처럼 선택하지 않는다. 건물 원형과 호환되는
복수 HVAC 가설을 각각 독립 EnergyPlus 실행 묶음으로 발행하고, 소비자가 동일 설정온도끼리
분포를 계산한다.

`energyplus_run_manifest.json`은 Bxx×H_x×도시 하나와 24/25/26°C 실행 세 건을 고정한다.
verified run은 EnergyPlus 버전, IDF·EPW·결과 해시, Severe 0, 연료별 시설 에너지와 쾌적
경계를 모두 가져야 한다. `is_observed=false`이므로 실제 설비 확인·현장 적용·M&V 증거가 아니다.

원시 IDF·CSV 경로는 계약에 넣지 않는다. manifest는 내용 지문을 전달하며, 소비자는 setpoint
집합과 baseline 역할을 추가 검증한다. `facility_total`은 네 에너지원 합계와 허용 오차 안에서
일치해야 한다. JSON Schema가 산술 관계를 표현하지 못하므로 생산자와 소비자 양쪽이 이 불변식을
검사한다. HVAC별 기간·기상·원형이 다르면 한 범위로 합치지 않는다.
