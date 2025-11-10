// 상품 목록 페이지 JS 컨트롤러
// 역할: API 연동, 검색·필터·페이지 이동, 정렬, 토스트 호출

document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.getElementById("stocksTbody");
  const categorySelect = document.getElementById("categorySelect");
  const keywordInput = document.getElementById("keywordInput");
  const searchBtn = document.getElementById("searchBtn");
  const resetBtn = document.getElementById("resetBtn");
  const pagination = document.getElementById("pagination");
  const pageInfo = document.getElementById("pageInfo");

  const table = document.getElementById("stocksTable");
  const baseUrl = table.dataset.endpointList;
  const searchUrl = table.dataset.endpointSearch;

  // 페이지 상태
  let currentPage = 1;
  const pageSize = 20;
  let totalPages = 1;
  let currentSort = { field: "id", order: "desc" };

  // ==============================
  // API 호출 (목록/검색)
  // ==============================
  async function fetchStocks(page = 1) {
    const params = new URLSearchParams({
      page,
      size: pageSize,
      sort: `${currentSort.field}:${currentSort.order}`,
    });

    const categoryId = categorySelect.value;
    const keyword = keywordInput.value.trim();
    let endpoint = baseUrl;

    if (categoryId || keyword) {
      endpoint = searchUrl;
      if (categoryId) params.append("categoryId", categoryId);
      if (keyword) params.append("keyword", keyword);
    }

    try {
      const res = await fetch(`${endpoint}?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderTable(data.items || []);
      updatePagination(data.page, data.total_pages);
    } catch (err) {
      console.error("목록 조회 실패:", err);
      showToast("데이터를 불러오지 못했습니다.", "error");
    }
  }

  // ==============================
  // 테이블 렌더링
  // ==============================
  function renderTable(items) {
    tableBody.innerHTML = "";
    if (!items.length) {
      tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;">데이터 없음</td></tr>`;
      return;
    }

    for (const s of items) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${s.id}</td>
        <td>${escapeHtml(s.name)}</td>
        <td>${s.inventory}</td>
        <td>${escapeHtml(s.category_name || "-")}</td>
        <td>
          <button data-id="${s.id}" class="btn-edit">수정</button>
          <button data-id="${s.id}" class="btn-delete">삭제</button>
        </td>
      `;
      tableBody.appendChild(row);
    }
  }

  // ==============================
  // 페이지네이션 업데이트
  // ==============================
  function updatePagination(page, total) {
    currentPage = page;
    totalPages = total;
    pageInfo.textContent = `${page} / ${total}`;
    document.getElementById("firstPage").disabled = page <= 1;
    document.getElementById("prevPage").disabled = page <= 1;
    document.getElementById("nextPage").disabled = page >= total;
    document.getElementById("lastPage").disabled = page >= total;
  }

  // ==============================
  // 이벤트: 검색 / 초기화
  // ==============================
  // 검색
  searchBtn.addEventListener("click", () => {
    const sortStr = `${currentSort.field}:${currentSort.order}`;
    updateUrl({
      categoryId: categorySelect.value || "",
      keyword: keywordInput.value.trim(),
      page: 1,
      sort: sortStr,
    });
    fetchStocks(1);
  });

  // 초기화
  resetBtn.addEventListener("click", () => {
    categorySelect.value = "";
    keywordInput.value = "";
    const sortStr = `${currentSort.field}:${currentSort.order}`;
    updateUrl({ categoryId: "", keyword: "", page: 1, sort: sortStr });
    fetchStocks(1);
  });

  // ==============================
  // 이벤트: 페이지 이동
  // ==============================
  // 페이지 이동을 한곳에서 처리함
  const goPage = (p) => {
    const sortStr = `${currentSort.field}:${currentSort.order}`;
    updateUrl({
      categoryId: categorySelect.value || "",
      keyword: keywordInput.value.trim(),
      page: p,
      sort: sortStr,
    });
    fetchStocks(p);
  };

  document.getElementById("firstPage").onclick = () => goPage(1);
  document.getElementById("prevPage").onclick  = () => goPage(Math.max(1, currentPage - 1));
  document.getElementById("nextPage").onclick  = () => goPage(Math.min(totalPages, currentPage + 1));
  document.getElementById("lastPage").onclick  = () => goPage(totalPages);

  // ==============================
  // 이벤트: 정렬 클릭
  // ==============================
  table.querySelectorAll("th[data-sort]").forEach(th => {
    th.addEventListener("click", () => {
      const field = th.dataset.sort;

      // 정렬 토글 로직
      if (currentSort.field === field) {
        currentSort.order = currentSort.order === "asc" ? "desc" : "asc";
      } else {
        currentSort = { field, order: "asc" };
      }

      // URL 쿼리 갱신 후 첫 페이지로 이동
      const sortStr = `${currentSort.field}:${currentSort.order}`;
      updateUrl({
        categoryId: categorySelect.value || "",
        keyword: keywordInput.value.trim(),
        page: 1,
        sort: sortStr,
      });

      fetchStocks(1);
    });
  });


  // ==============================
  // HTML 이스케이프 (XSS 방지)
  // ==============================
  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, s => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[s]));
  }

  // ==============================
  // 토스트 표시 (경고/성공/정보)
  // - 별도의 CSS 파일 없이 자체 스타일 주입
  // - #toast-root 컨테이너에 카드 쌓임
  // ==============================
  ;(() => {
    // 스타일 한 번만 주입
    const STYLE_ID = "toast-inline-style";
    if (!document.getElementById(STYLE_ID)) {
      const style = document.createElement("style");
      style.id = STYLE_ID;
      style.textContent = `
        #toast-root { z-index: 9999; }
        .toast-card {
          min-width: 240px;
          max-width: 420px;
          margin-top: 8px;
          padding: 12px 14px;
          border-radius: 10px;
          box-shadow: 0 6px 20px rgba(0,0,0,0.12);
          background: #ffffff;
          display: flex;
          align-items: center;
          gap: 10px;
          opacity: 0;
          transform: translateY(-6px);
          transition: opacity .2s ease, transform .2s ease;
          border-left: 5px solid #888;
          font-size: 14px;
          line-height: 1.35;
        }
        .toast-card.show { opacity: 1; transform: translateY(0); }
        .toast-card .toast-title { font-weight: 700; margin-right: 6px; }
        .toast-card.info { border-left-color: #3b82f6; }     /* 파랑 */
        .toast-card.success { border-left-color: #22c55e; }  /* 초록 */
        .toast-card.error { border-left-color: #ef4444; }    /* 빨강 */
        .toast-close {
          margin-left: auto;
          cursor: pointer;
          border: none;
          background: transparent;
          font-size: 16px;
        }
      `;
      document.head.appendChild(style);
    }
  })();

  function showToast(message, type = "info", title) {
    const root = document.getElementById("toast-root");
    if (!root) return console.log(`[${type}] ${message}`);

    const card = document.createElement("div");
    card.className = `toast-card ${type}`;

    const strong = document.createElement("span");
    strong.className = "toast-title";
    strong.textContent = title || (type === "success" ? "완료" : type === "error" ? "오류" : "알림");

    const text = document.createElement("span");
    text.textContent = String(message);

    const btn = document.createElement("button");
    btn.className = "toast-close";
    btn.setAttribute("aria-label", "닫기");
    btn.textContent = "×";
    btn.onclick = () => root.removeChild(card);

    card.appendChild(strong);
    card.appendChild(text);
    card.appendChild(btn);
    root.appendChild(card);

    // 등장 애니메이션
    requestAnimationFrame(() => card.classList.add("show"));

    // 자동 제거
    setTimeout(() => {
      if (!card.isConnected) return;
      card.classList.remove("show");
      setTimeout(() => card.isConnected && root.removeChild(card), 200);
    }, 2500);
  }
  // ==============================
  // API helpers: 삭제 / 수정
  // ==============================
  async function apiDeleteStock(id) {
    const res = await fetch(`/api/stocks/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`DELETE /api/stocks/${id} -> ${res.status}`);
  }

  async function apiUpdateStock(id, payload) {
    const res = await fetch(`/api/stocks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`PUT /api/stocks/${id} -> ${res.status}`);
    return await res.json();
  }

  // ==============================
  // 이벤트 위임: 수정 / 삭제 버튼
  //  - .btn-edit, .btn-delete
  // ==============================
  tableBody.addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    const id = btn.dataset.id;
    if (!id) return;

    // 삭제
    if (btn.classList.contains("btn-delete")) {
      const ok = confirm("정말 삭제할까요?");
      if (!ok) return;

      try {
        await apiDeleteStock(id);
        showToast("삭제 완료", "success");
        await fetchStocks(currentPage); // 현재 페이지 갱신
      } catch (err) {
        console.error(err);
        showToast("삭제 실패", "error");
      }
      return;
    }

    // 수정
    if (btn.classList.contains("btn-edit")) {
      try {
        // 간단 프롬프트 기반 편집(MVP)
        const newName = prompt("상품명(미입력 시 변경 없음):");
        const newInvRaw = prompt("재고 수량(정수, 미입력 시 변경 없음):");
        const newCatRaw = prompt("카테고리 ID(정수, 미입력 시 변경 없음):");

        // 부분 업데이트 payload 구성
        const payload = {};
        if (newName && newName.trim()) payload.name = newName.trim();

        if (newInvRaw && newInvRaw.trim() !== "") {
          const inv = Number(newInvRaw);
          if (!Number.isInteger(inv)) {
            showToast("재고는 정수여야 함", "error");
            return;
          }
          payload.inventory = inv;
        }

        if (newCatRaw && newCatRaw.trim() !== "") {
          const cid = Number(newCatRaw);
          if (!Number.isInteger(cid)) {
            showToast("카테고리 ID는 정수여야 함", "error");
            return;
          }
          payload.category_id = cid;
        }

        if (Object.keys(payload).length === 0) {
          showToast("변경 사항 없음", "info");
          return;
        }

        await apiUpdateStock(id, payload);
        showToast("수정 완료", "success");
        await fetchStocks(currentPage);
      } catch (err) {
        console.error(err);
        showToast("수정 실패", "error");
      }
      return;
    }
  });

    // ==============================
  // API helper: 생성(POST)
  // ==============================
  async function apiCreateStock(payload) {
    const res = await fetch(`/api/stocks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`POST /api/stocks -> ${res.status}`);
    return await res.json();
  }

  // ==============================
  // 등록 버튼 동적 생성 + 클릭 핸들러
  // - 템플릿 수정 없이 JS에서 주입
  // ==============================
  (function ensureCreateButton() {
    const toolbar = document.getElementById("toolbar");
    if (!toolbar) return;

    let btn = document.getElementById("createBtn");
    if (!btn) {
      btn = document.createElement("button");
      btn.id = "createBtn";
      btn.type = "button";
      btn.textContent = "등록";
      // 검색/초기화 버튼 뒤에 붙임
      toolbar.appendChild(btn);
    }

    btn.addEventListener("click", async () => {
      try {
        const name = prompt("상품명:");
        if (!name || !name.trim()) {
          showToast("상품명이 비어 있음", "error");
          return;
        }
        // 재고 입력 (프롬프트 대신 기본값 사용 가능)
        const invRaw = prompt("재고 수량(정수):", "0");
        if (invRaw === null) return; // 취소
        const inv = Number(invRaw);
        if (!Number.isInteger(inv)) {
          showToast("재고는 정수여야 함", "error");
          return;
        }

        // 수정: 드롭다운의 실제 값을 사용 (프롬프트 제거)
        const cidStr = categorySelect.value;          // select의 value가 DB의 c.id로 세팅되어 있음
        if (!cidStr) {                                // 빈값(전체 등) 방지
          showToast("카테고리를 먼저 선택하세요.", "error");
          return;
        }
        const cid = Number(cidStr);
        if (!Number.isInteger(cid)) {
          showToast("카테고리 ID가 올바르지 않습니다.", "error");
          return;
        }


        const created = await apiCreateStock({
          name: name.trim(),
          inventory: inv,
          category_id: cid,
        });


        showToast(`등록 완료 (#${created.id})`, "success");
        // 현재 필터/정렬 유지한 채 첫 페이지로 갱신 (UX 안정)
        await fetchStocks(1);
      } catch (err) {
        console.error(err);
        showToast("등록 실패", "error");
      }
    });
  })();

  // ==============================
  // URL 상태 동기화 헬퍼
  // ==============================
  function readQuery() {
    const u = new URL(window.location.href);
    return {
      categoryId: u.searchParams.get("categoryId") || "",
      keyword: u.searchParams.get("keyword") || "",
      page: parseInt(u.searchParams.get("page") || "1", 10),
      sort: u.searchParams.get("sort") || "id:desc",
    };
  }

  function applyStateFromUrl() {
    const q = readQuery();

    // 카테고리 값이 옵션에 없을 수 있어 보호 처리함
    if ([...categorySelect.options].some(o => o.value === q.categoryId)) {
      categorySelect.value = q.categoryId;
    } else {
      categorySelect.value = "";
    }
    keywordInput.value = q.keyword;

    const [f, o] = q.sort.split(":");
    currentSort = { field: f || "id", order: o === "asc" ? "asc" : "desc" };

    return Math.max(1, q.page || 1);
  }

  function updateUrl({ categoryId, keyword, page, sort }) {
    const u = new URL(window.location.href);
    if (categoryId !== undefined) {
      if (categoryId) u.searchParams.set("categoryId", categoryId);
      else u.searchParams.delete("categoryId");
    }
    if (keyword !== undefined) {
      if (keyword) u.searchParams.set("keyword", keyword);
      else u.searchParams.delete("keyword");
    }
    if (page !== undefined) u.searchParams.set("page", String(page));
    if (sort !== undefined) u.searchParams.set("sort", sort);
    history.pushState({ page }, "", u);
  }

  // 히스토리 뒤/앞으로 가기 시 재조회
  window.addEventListener("popstate", () => {
    const p = applyStateFromUrl();
    fetchStocks(p);
  });


  // 초기 목록 로드: URL 상태 먼저 반영 후 조회
  const initialPage = applyStateFromUrl();
  fetchStocks(initialPage);
});
