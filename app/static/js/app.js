// app/static/js/app.js
// 정적 스크립트 테스트 - UTF-8 고정

// 페이지 로드 완료 시 실행
document.addEventListener("DOMContentLoaded", () => {
  console.log("app/static/js/app.js 로드 완료");

  // 테스트 버튼 핸들러
  const pingButton = document.getElementById("ping");
  if (pingButton) {
    pingButton.addEventListener("click", () => {
      console.log("버튼 클릭 감지됨: 정적 JS 정상 작동 중");
      alert("정적 리소스 연결 성공!");
    });
  } else {
    console.warn("'ping' 버튼을 찾을 수 없음 (index.html 확인 필요)");
  }
});

