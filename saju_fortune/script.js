// ---------------------------------------------------------------------------
// 사주(四柱) 계산 엔진
//
// 일주(日柱) 기준일: 2019-01-27 = 갑자일(甲子日), JD(태양시 정오 UT) = 2458511
//   (60갑자는 날짜가 바뀔 때마다 하루도 빠짐없이 순환하므로, 기준일과의
//    날짜 차이를 60으로 나눈 나머지로 계산한다.)
// 연주(年柱) 기준연도: 1984년 = 갑자년(甲子年)
// 월주/절기 경계: 태양의 겉보기 황경(apparent ecliptic longitude)이
//   315°(입춘), 345°(경칩) ... 각 30°마다 바뀌는 절입(節入) 시각을 기준으로
//   달(월지)이 바뀐다. (저정밀 태양좌표 공식, Meeus 저정밀 공식 기반)
// ---------------------------------------------------------------------------

const STEMS = [
  { han: "갑", hanja: "甲", element: "wood" },
  { han: "을", hanja: "乙", element: "wood" },
  { han: "병", hanja: "丙", element: "fire" },
  { han: "정", hanja: "丁", element: "fire" },
  { han: "무", hanja: "戊", element: "earth" },
  { han: "기", hanja: "己", element: "earth" },
  { han: "경", hanja: "庚", element: "metal" },
  { han: "신", hanja: "辛", element: "metal" },
  { han: "임", hanja: "壬", element: "water" },
  { han: "계", hanja: "癸", element: "water" },
];

const BRANCHES = [
  { han: "자", hanja: "子", element: "water", animal: "쥐" },
  { han: "축", hanja: "丑", element: "earth", animal: "소" },
  { han: "인", hanja: "寅", element: "wood", animal: "호랑이" },
  { han: "묘", hanja: "卯", element: "wood", animal: "토끼" },
  { han: "진", hanja: "辰", element: "earth", animal: "용" },
  { han: "사", hanja: "巳", element: "fire", animal: "뱀" },
  { han: "오", hanja: "午", element: "fire", animal: "말" },
  { han: "미", hanja: "未", element: "earth", animal: "양" },
  { han: "신", hanja: "申", element: "metal", animal: "원숭이" },
  { han: "유", hanja: "酉", element: "metal", animal: "닭" },
  { han: "술", hanja: "戌", element: "earth", animal: "개" },
  { han: "해", hanja: "亥", element: "water", animal: "돼지" },
];

const ELEMENT_INFO = {
  wood: { label: "목(木)", cls: "wood" },
  fire: { label: "화(火)", cls: "fire" },
  earth: { label: "토(土)", cls: "earth" },
  metal: { label: "금(金)", cls: "metal" },
  water: { label: "수(水)", cls: "water" },
};

const DAY_STEM_ANCHOR_JD = 2458511; // 2019-01-27 = 갑자일
const YEAR_STEM_ANCHOR = 1984; // 1984년 = 갑자년

// ---- 날짜/시간 유틸 -------------------------------------------------------

// 그 날짜(달력상의 날짜, 시각과 무관)의 JDN을 구한다. UTC 정오 기준 JD와 동일.
function jdnOfDate(y, m, d) {
  return Math.round(Date.UTC(y, m - 1, d, 12, 0, 0) / 86400000 + 2440587.5);
}

// 한국 표준시(KST, UTC+9)로 주어진 일시를 소수점 포함 Julian Day(UT 기준)로 변환.
function julianDayFromKST(y, m, d, hh, mm) {
  const ms = Date.UTC(y, m - 1, d, hh - 9, mm, 0);
  return ms / 86400000 + 2440587.5;
}

function mod(n, m) {
  return ((n % m) + m) % m;
}

// ---- 태양 황경(黃經) 계산 --------------------------------------------------
// 저정밀 태양좌표 공식 (오차 약 0.01도 이내, 1900~2100년 범위에서 충분히 정확)
function solarLongitude(jd) {
  const T = (jd - 2451545.0) / 36525;
  const deg2rad = Math.PI / 180;

  const L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  const M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  const Mrad = mod(M, 360) * deg2rad;

  const C =
    (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(Mrad) +
    (0.019993 - 0.000101 * T) * Math.sin(2 * Mrad) +
    0.000289 * Math.sin(3 * Mrad);

  const trueLong = L0 + C;
  const omega = 125.04 - 1934.136 * T;
  let lambda = trueLong - 0.00569 - 0.00478 * Math.sin(omega * deg2rad);

  return mod(lambda, 360);
}

// targetLambda(도) 근처(approxJD ± searchDays일)에서 태양 황경이 targetLambda를
// 지나는 정확한 시각(JD)을 이분탐색으로 구한다. (해당 구간에서 월경 없음을 전제)
function findSolarTermJD(targetLambda, approxJD, searchDays) {
  let lo = approxJD - searchDays;
  let hi = approxJD + searchDays;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    const val = solarLongitude(mid);
    if (val < targetLambda) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

// 해당 연도의 입춘(立春, 황경 315도) 시각(JD)을 구한다.
function getIpchunJD(year) {
  const approx = Date.UTC(year, 1, 4, 12, 0, 0) / 86400000 + 2440587.5; // 대략 2월 4일 정오
  return findSolarTermJD(315, approx, 15);
}

// ---- 사주 계산 ------------------------------------------------------------

function calcDayPillar(y, m, d) {
  const jdn = jdnOfDate(y, m, d);
  const idx = mod(jdn - DAY_STEM_ANCHOR_JD, 60);
  return { stemIndex: idx % 10, branchIndex: idx % 12 };
}

function calcYearPillar(sajuYear) {
  const idx = mod(sajuYear - YEAR_STEM_ANCHOR, 60);
  return { stemIndex: idx % 10, branchIndex: idx % 12 };
}

function calcMonthPillar(yearStemIndex, lambda) {
  // 절기 구간을 12지지로 매핑: 대설(255도)=자월(0) 부터 30도씩 증가
  const monthBranchIndex = Math.floor(mod(lambda - 255, 360) / 30) % 12;

  // 월두법(오호둔): 연간에 따라 인월(寅月)의 천간이 정해지고,
  // 이후 달마다 순서대로 천간이 진행된다.
  const monthStemOfYin = mod(2 * mod(yearStemIndex, 5) + 2, 10);
  const stepsFromYin = mod(monthBranchIndex - 2, 12);
  const monthStemIndex = mod(monthStemOfYin + stepsFromYin, 10);

  return { stemIndex: monthStemIndex, branchIndex: monthBranchIndex };
}

function calcHourPillar(dayStemIndex, hour) {
  const hourBranchIndex = Math.floor(mod(hour + 1, 24) / 2);
  // 시두법(오자시둔): 일간에 따라 자시(子時)의 천간이 정해지고,
  // 이후 시진마다 순서대로 천간이 진행된다.
  const hourStemOfJa = mod(2 * mod(dayStemIndex, 5), 10);
  const hourStemIndex = mod(hourStemOfJa + hourBranchIndex, 10);
  return { stemIndex: hourStemIndex, branchIndex: hourBranchIndex };
}

function calcSaju({ year, month, day, hour, minute, timeKnown }) {
  const day_ = calcDayPillar(year, month, day);

  const birthJD = julianDayFromKST(year, month, day, timeKnown ? hour : 12, timeKnown ? minute : 0);
  const ipchunThisYear = getIpchunJD(year);
  const sajuYear = birthJD >= ipchunThisYear ? year : year - 1;

  const year_ = calcYearPillar(sajuYear);
  const lambda = solarLongitude(birthJD);
  const month_ = calcMonthPillar(year_.stemIndex, lambda);

  const hour_ = timeKnown ? calcHourPillar(day_.stemIndex, hour) : null;

  return { year: year_, month: month_, day: day_, hour: hour_, sajuYear };
}

// ---- 오행 집계 및 해석 -----------------------------------------------------

function tallyElements(saju) {
  const counts = { wood: 0, fire: 0, earth: 0, metal: 0, water: 0 };
  const pillars = [saju.year, saju.month, saju.day, saju.hour].filter(Boolean);
  pillars.forEach((p) => {
    counts[STEMS[p.stemIndex].element]++;
    counts[BRANCHES[p.branchIndex].element]++;
  });
  return counts;
}

const ELEMENT_STRONG_TEXT = {
  wood: "목(木) 기운이 두드러져 성장과 확장, 추진력을 중시하는 성향이 강하게 나타납니다. 새로운 일을 벌이는 데 적극적이지만, 때로는 여유를 갖고 속도를 조절하는 것이 도움이 됩니다.",
  fire: "화(火) 기운이 강해 열정적이고 표현력이 풍부하며 주위를 밝히는 에너지를 지니고 있습니다. 추진력은 좋으나 감정 기복이나 조급함을 다스리는 것이 관건입니다.",
  earth: "토(土) 기운이 두드러져 신중하고 안정적이며 중심을 잡아주는 역할을 잘 해냅니다. 다만 변화에 더디게 반응하거나 고집스러워지지 않도록 유연함을 더하면 좋습니다.",
  metal: "금(金) 기운이 강해 원칙적이고 결단력이 있으며 맺고 끊음이 분명합니다. 추진력과 의리가 강점이나, 지나치게 날카로워지지 않도록 배려하는 태도가 필요합니다.",
  water: "수(水) 기운이 두드러져 지혜롭고 융통성이 있으며 상황을 유연하게 받아들이는 힘이 있습니다. 생각이 많아 결정이 늦어질 수 있으니 때로는 과감한 선택도 필요합니다.",
};

const ELEMENT_WEAK_TEXT = {
  wood: "목(木) 기운이 약해 새로운 시도나 확장에 대한 추진력이 다소 부족할 수 있습니다. 계획을 세우고 한 걸음씩 실행하는 습관을 들이면 좋습니다.",
  fire: "화(火) 기운이 약해 감정 표현이나 적극성이 다소 소극적일 수 있습니다. 자신의 의견과 열정을 표현하는 연습이 도움이 됩니다.",
  earth: "토(土) 기운이 약해 안정감이나 지구력이 다소 부족하게 느껴질 수 있습니다. 꾸준함을 기르고 기반을 다지는 데 신경 쓰면 좋습니다.",
  metal: "금(金) 기운이 약해 결단력이나 맺고 끊는 힘이 다소 약할 수 있습니다. 우선순위를 정하고 단호하게 실행하는 연습이 필요합니다.",
  water: "수(水) 기운이 약해 융통성이나 지혜로운 대처가 다소 부족하게 느껴질 수 있습니다. 다양한 시각에서 생각해보는 습관이 도움이 됩니다.",
};

const DAY_STEM_PERSONALITY = {
  0: "큰 나무(甲木)처럼 곧고 진취적이며 리더십이 강한 성향입니다. 목표를 향해 뚝심 있게 밀고 나가지만, 자존심이 강해 고집으로 비칠 수 있으니 주변의 의견에 귀 기울이면 더욱 좋습니다.",
  1: "화초와 넝쿨(乙木)처럼 유연하고 적응력이 뛰어난 성향입니다. 사람들과 두루 잘 어울리고 상황에 맞춰 처신하지만, 결단이 필요한 순간 우유부단해지지 않도록 주의가 필요합니다.",
  2: "태양(丙火)처럼 밝고 정열적이며 사교성이 뛰어난 성향입니다. 주위를 환하게 밝히는 에너지가 있지만, 감정이 앞서 다혈질로 흐르지 않도록 스스로를 다독이는 여유가 필요합니다.",
  3: "은은한 촛불(丁火)처럼 섬세하고 따뜻한 마음을 지닌 성향입니다. 예술적 감각과 세심한 배려가 돋보이지만, 속으로만 담아두지 말고 자신의 생각을 표현하는 연습이 도움이 됩니다.",
  4: "높은 산과 대지(戊土)처럼 믿음직하고 포용력이 큰 성향입니다. 어떤 상황에서도 중심을 잃지 않는 안정감이 강점이지만, 지나치게 고집스러워지지 않도록 유연함을 더하면 좋습니다.",
  5: "기름진 논밭(己土)처럼 온화하고 실용적인 성향입니다. 주변을 세심하게 챙기는 배려심이 돋보이지만, 자기 주장을 내세우는 데 소극적이지 않도록 조금 더 자신감을 가져도 좋습니다.",
  6: "무쇠와 원석(庚金)처럼 강직하고 결단력이 있는 성향입니다. 의리를 중시하고 맡은 일을 확실히 해내지만, 융통성을 조금 더 발휘하면 대인관계가 한결 부드러워질 것입니다.",
  7: "보석과 장신구(辛金)처럼 섬세하고 예리한 감각을 지닌 성향입니다. 자존심이 강하고 완벽을 추구하지만, 스스로에게 조금 관대해지는 것도 필요합니다.",
  8: "넓은 바다(壬水)처럼 지혜롭고 포용력이 큰 성향입니다. 큰 그림을 보는 통솔력이 강점이지만, 마음이 자주 바뀌지 않도록 중심을 잡는 노력이 도움이 됩니다.",
  9: "맑은 샘물과 이슬(癸水)처럼 섬세하고 순수한 성향입니다. 뛰어난 직관력으로 상황을 잘 파악하지만, 소극적으로 물러서기보다 한 걸음 더 나서보는 용기도 필요합니다.",
};

function buildElementInterpretation(counts) {
  const entries = Object.entries(counts);
  const max = Math.max(...entries.map(([, v]) => v));
  const min = Math.min(...entries.map(([, v]) => v));
  const strongest = entries.filter(([, v]) => v === max && v > 0).map(([k]) => k);
  const weakest = entries.filter(([, v]) => v === min).map(([k]) => k);

  const paras = [];

  if (max - min <= 1) {
    paras.push("사주 여덟 글자에 오행이 비교적 고르게 분포되어 있어, 어느 한쪽으로 치우치지 않은 균형 잡힌 기운을 가지고 있습니다.");
  } else {
    strongest.forEach((el) => paras.push(ELEMENT_STRONG_TEXT[el]));
  }

  const missing = entries.filter(([, v]) => v === 0).map(([k]) => k);
  if (missing.length > 0) {
    missing.forEach((el) => paras.push(ELEMENT_WEAK_TEXT[el]));
  } else if (max - min > 1) {
    weakest.forEach((el) => paras.push(ELEMENT_WEAK_TEXT[el]));
  }

  return paras;
}

// ---- 렌더링 ---------------------------------------------------------------

function elCls(element) {
  return "el-" + element;
}

function pillarHTML(label, pillar) {
  if (!pillar) {
    return `
      <div class="pillar">
        <div class="pillar-label">${label}</div>
        <span class="ganji-hanja">-</span>
        <span class="ganji-char" style="color:var(--text-dim)">시간 미상</span>
      </div>`;
  }
  const stem = STEMS[pillar.stemIndex];
  const branch = BRANCHES[pillar.branchIndex];
  return `
    <div class="pillar">
      <div class="pillar-label">${label}</div>
      <span class="ganji-hanja">${stem.hanja}${branch.hanja}</span>
      <span class="ganji-char ${elCls(stem.element)}">${stem.han}</span>
      <span class="ganji-char ${elCls(branch.element)}">${branch.han}</span>
    </div>`;
}

function elementBarsHTML(counts) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  return Object.entries(ELEMENT_INFO)
    .map(([key, info]) => {
      const value = counts[key];
      const pct = Math.round((value / total) * 100);
      return `
        <div class="element-row">
          <span>${info.label}</span>
          <div class="bar-track"><div class="bar-fill fill-${info.cls}" style="width:${pct}%"></div></div>
          <span>${value}</span>
        </div>`;
    })
    .join("");
}

function renderResult(saju, meta) {
  const counts = tallyElements(saju);
  const dayStem = STEMS[saju.day.stemIndex];
  const personality = DAY_STEM_PERSONALITY[saju.day.stemIndex];
  const elementParas = buildElementInterpretation(counts);

  const nameLabel = meta.name ? `${meta.name}님의` : "입력하신 생년월일의";

  const html = `
    <div class="card">
      <h2>${nameLabel} 사주 명식</h2>
      <div class="pillars">
        ${pillarHTML("년주(年柱)", saju.year)}
        ${pillarHTML("월주(月柱)", saju.month)}
        ${pillarHTML("일주(日柱)", saju.day)}
        ${pillarHTML("시주(時柱)", saju.hour)}
      </div>
    </div>

    <div class="card">
      <h2>오행(五行) 분포</h2>
      <div class="element-bars">${elementBarsHTML(counts)}</div>
    </div>

    <div class="card reading">
      <h2>일간(日干) - 나를 나타내는 글자: ${dayStem.han}(${dayStem.hanja})</h2>
      <p>${personality}</p>
    </div>

    <div class="card reading">
      <h2>오행으로 보는 전체적인 기운</h2>
      ${elementParas.map((p) => `<p>${p}</p>`).join("")}
    </div>
  `;

  const result = document.getElementById("result");
  result.innerHTML = html;
  result.classList.remove("hidden");
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---- 폼 처리 ---------------------------------------------------------------

const form = document.getElementById("sajuForm");
const timeUnknownCheckbox = document.getElementById("timeUnknown");
const birthTimeInput = document.getElementById("birthTime");

timeUnknownCheckbox.addEventListener("change", () => {
  birthTimeInput.disabled = timeUnknownCheckbox.checked;
});

form.addEventListener("submit", (e) => {
  e.preventDefault();

  const existingError = form.querySelector(".error-msg");
  if (existingError) existingError.remove();

  const dateVal = document.getElementById("birthDate").value;
  if (!dateVal) {
    showError("생년월일을 입력해주세요.");
    return;
  }

  const [year, month, day] = dateVal.split("-").map(Number);
  const timeKnown = !timeUnknownCheckbox.checked;
  let hour = 12, minute = 0;
  if (timeKnown) {
    const timeVal = birthTimeInput.value || "12:00";
    [hour, minute] = timeVal.split(":").map(Number);
  }

  const name = document.getElementById("name").value.trim();

  try {
    const saju = calcSaju({ year, month, day, hour, minute, timeKnown });
    renderResult(saju, { name });
  } catch (err) {
    showError("계산 중 오류가 발생했습니다. 날짜를 확인해주세요.");
    console.error(err);
  }
});

function showError(message) {
  const p = document.createElement("p");
  p.className = "error-msg";
  p.textContent = message;
  form.insertBefore(p, form.querySelector(".submit-btn"));
}
