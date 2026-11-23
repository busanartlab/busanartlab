(function(){
  const VENUE_URLS = {
    "정관박물관":"https://busan.go.kr",
    "포디움다이브":"https://instagram.com",
    "뮤지엄 원":"https://museum1.co.kr","뮤지엄원":"https://museum1.co.kr",
    "고은사진미술관":"https://goeunmuseum.kr",
    "KT&G상상마당 부산":"https://sangsangmadang.com","KT&G 상상마당 부산":"https://sangsangmadang.com","상상마당 부산":"https://sangsangmadang.com",
    "갤러리 인터페이스":"http://galleryinterface.kr",
    "청년창조발전소":"https://bsnamgu.go.kr",
    "스타필드 시티 명지":"https://starfield.co.kr",
    "해운대 바다 갤러리":"https://haeundaegallery.com","해운대바다갤러리":"https://haeundaegallery.com",
    "부산도서관":"https://busan.go.kr",
    "스페이스 하이":"https://instagram.com",
    "붐빌":"https://instagram.com","space bv":"https://instagram.com",
    "갤러리 재희":"https://instagram.com",
    "스페이스 원지":"https://instagram.com",
    "스페이스 위버멘쉬":"https://over-man.com",
    "리빈갤러리":"https://instagram.com",
    "데이트갤러리":"https://instagram.com",
    "부산갤러리":"https://busangallery.com",
    "스페이스 포포":"http://spacefofo.kr",
    "가온아트홀":"http://alltheway.kr",
    "부산시청전시실":"https://busan.go.kr","부산시청 전시실":"https://busan.go.kr",
    "레오앤 갤러리":"http://leowith.com","레오앤갤러리":"http://leowith.com",
    "18-1갤러리":"https://instagram.com",
    "해운대문화회관":"https://haeundae.go.kr",
    "낙동아트센터":"https://bsgangseo.go.kr",
    "동래문화회관":"https://dongnae.go.kr",
    "신세계센텀시티 9층 문화홀":"https://shinsegae.com","신세계백화점 센텀시티":"https://shinsegae.com",
    "다누림센터 다누림홀":"http://sasangculture.or.kr","다누림홀":"http://sasangculture.or.kr",
    "기장군청 차성아트홀":"https://gijang.go.kr","차성아트홀":"https://gijang.go.kr",
    "어댑터씨어터":"https://adapter.theater",
    "소향씨어터 신한카드홀":"http://sohyanglottehall.com","소향씨어터":"http://sohyanglottehall.com",
    "경성대학교 예노소극장":"https://ks.ac.kr","예노소극장":"https://ks.ac.kr",
    "을숙도문화회관":"https://saha.go.kr",
    "북구문화예술회관":"https://bsbukgu.go.kr",
    "정관에듀파크":"https://gijang.go.kr",
    "브릭홀":"https://spacecloud.kr",
    "북두칠성도서관":"http://book7library.co.kr",
    "부산시립예술단":"https://bscc.or.kr",
    "부산문화회관":"https://bscc.or.kr"
  };
  let DB = [];
  function vUrl(v, fb){
    if(!v) return fb || "";
    const c = v.trim();
    if(VENUE_URLS[c]) return VENUE_URLS[c];
    for(const [k, u] of Object.entries(VENUE_URLS)) if(c.includes(k)) return u;
    return fb || "";
  }
  function sTag(t){
    if(!t) return "문화칼럼";
    if(/ADFA|adfa/.test(t)) return "ADFA칼럼";
    if(t.includes("알고리즘")) return "알고리즘예술가";
    if(t.includes("초대석")) return "초대석";
    if(t.includes("미학칼럼")) return "미학칼럼";
    return "문화칼럼";
  }
  function masterRender(){
    const g = document.getElementById("cardGrid") || document.getElementById("cardsGrid") || document.querySelector(".card-grid, .cards-grid, [id*='Grid'], [id*='grid']");
    const ce = document.getElementById("resultCount") || document.getElementById("totalCount") || document.querySelector(".result-count, .count-text, [id*='Count']");
    if(!g || !DB.length) return;
    const cat = document.querySelector("[data-cat].active")?.getAttribute("data-cat") || "ALL";
    const st = document.querySelector("[data-status].active")?.getAttribute("data-status") || "ALL";
    const reg = document.getElementById("regionSelect")?.value || "ALL";
    const kw = (document.getElementById("keywordInput")?.value || "").trim().toLowerCase();
    const isColumnMode = (cat === "강경호 문화칼럼" || reg === "강경호 문화칼럼");

    const list = DB.filter(x => {
      const isC = x.category === "강경호 문화칼럼" || x.status === "칼럼";
      if(isColumnMode) return isC;
      if(cat !== "ALL" && x.category !== cat) return false;
      if(!isC && st !== "ALL"){
        const ok = (st === "예정" || st === "개막 예정") ? ["예정", "개막 예정"] : [st];
        if(!ok.includes(x.status)) return false;
      }
      if(reg !== "ALL"){
        if(reg === "부산 전체"){ if(!x.isBusan && !(x.region || "").includes("부산")) return false; }
        else if(reg === "전국 주요 권역"){ if(x.isBusan || (x.region || "").includes("부산")) return false; }
        else if(!(x.region || "").includes(reg)) return false;
      }
      if(kw && !`${x.title||""} ${x.venue||""} ${x.artist||""} ${x.region||""}`.toLowerCase().includes(kw)) return false;
      return true;
    });

    if(ce){
      if(ce.tagName === "STRONG" || ce.tagName === "SPAN") ce.textContent = list.length;
      else ce.innerHTML = `총 <strong>${list.length}</strong>건의 큐레이션 일정`;
    }
    g.innerHTML = list.map(x => {
      const isC = x.category === "강경호 문화칼럼" || x.status === "칼럼";
      if(isC){
        const u = x.newsUrl || x.officialUrl || "https://newsbusan.com";
        const sum = (x.title && x.title.includes(":")) ? x.title.split(":").slice(1).join(":").trim() : "부산·전국 문화예술 현장과 동시대 미학의 맥락을 짚는 심층 비평 칼럼";
        return `<article class="art-card" style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:22px;display:flex;flex-direction:column;justify-content:space-between;"><div><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;font-size:12px;"><div style="display:flex;align-items:center;gap:6px;"><span style="background:#dc2626;color:#fff;padding:3px 8px;border-radius:5px;font-weight:700;font-size:11px;">칼럼</span><span style="color:#2563eb;font-weight:700;">강경호 문화칼럼</span></div><span style="color:#374151;font-weight:600;background:#f1f5f9;padding:3px 8px;border-radius:5px;">${sTag(x.title)}</span></div><h3 style="font-size:17px;font-weight:700;color:#111827;line-height:1.45;margin-bottom:16px;">${x.title}</h3><div style="font-size:13px;color:#374151;display:flex;flex-direction:column;gap:6px;margin-bottom:20px;"><div style="display:flex;"><span style="width:62px;color:#6b7280;flex-shrink:0;">일정</span><span style="font-weight:600;color:#111827;">${x.period||""}</span></div><div style="display:flex;"><span style="width:62px;color:#6b7280;flex-shrink:0;">출처</span><span style="font-weight:600;color:#111827;">뉴스부산 (newsbusan.com)</span></div><div style="display:flex;"><span style="width:62px;color:#6b7280;flex-shrink:0;">필자</span><span style="font-weight:600;color:#111827;">강경호 | 문화기획자·문화평론가</span></div><div style="display:flex;"><span style="width:62px;color:#6b7280;flex-shrink:0;">핵심 요약</span><span style="color:#374151;line-height:1.45;">${sum}</span></div></div></div><div style="display:flex;gap:8px;align-items:center;"><a href="${u}" target="_blank" rel="noopener noreferrer" style="flex:1;text-align:center;padding:10px 12px;border-radius:8px;background:#14284b;color:#fff;font-size:13px;font-weight:700;text-decoration:none;">뉴스부산 비평·취재기사 보기 ↗</a><button type="button" onclick="navigator.clipboard.writeText('${u}');alert('기사 링크가 복사되었습니다.');" style="padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;background:#fff;color:#374151;font-size:13px;font-weight:600;cursor:pointer;">링크 복사</button></div></article>`;
      }
      const sc = x.status === "진행중" ? "#dc2626" : "#2563eb";
      const sl = (x.status === "개막 예정") ? "예정" : (x.status || "진행중");
      const vu = vUrl(x.venue, x.officialUrl);
      const vh = vu ? `<a href="${vu}" target="_blank" rel="noopener noreferrer" style="color:#111827;font-weight:700;text-decoration:underline;">${x.venue||""} ↗</a>` : `<span style="font-weight:600;color:#111827;">${x.venue||""}</span>`;
      const cf = (x.fee || "상세 안내 확인").replace(/↗/g, "").trim();
      const ar = (x.artist && x.artist.trim()) ? x.artist.trim() : "주최 측 공식 안내 참조";
      const cu = vu || x.newsUrl || "https://busanartlab.com";
