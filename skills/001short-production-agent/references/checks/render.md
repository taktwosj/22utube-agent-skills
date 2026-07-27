# 렌더 검증

render 입력을 validator가 CapCut 검증 증거의 경로·SHA-256과 연결해 존재·크기·video stream·decode·duration 증거로 검사한다. package 자기신고는 증거가 아니다. asset 누락·손상은 FAIL, render가 없으면 WAIT다. 통과해도 업로드는 `WAIT_UPLOAD_APPROVAL`이다.
