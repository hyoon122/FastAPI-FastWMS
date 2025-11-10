// 전역 유틸 초기 스크립트
// 목적: 공통 이벤트 바인딩 시 대상 요소가 없을 때도 안전하게 동작하도록 함

document.addEventListener("DOMContentLoaded", () => {
  console.log("app/static/js/app.js 로드 완료");

  // #ping 버튼이 페이지에 없을 수 있음 → 널 가드 처리
  const pingBtn = document.querySelector("#ping");
  if (pingBtn) {
    // 버튼이 있을 때만 이벤트 바인딩함
    pingBtn.addEventListener("click", async () => {
      try {
        // 간단한 핑 테스트 (엔드포인트는 프로젝트에 맞게 추후 변경 가능)
        const res = await fetch("/api/stocks");
        console.log("ping ok:", res.status);
      } catch (e) {
        console.warn("ping 실패:", e);
      }
    });
  }
  // 버튼이 없으면 아무 것도 하지 않음(경고 출력 안 함)
});
