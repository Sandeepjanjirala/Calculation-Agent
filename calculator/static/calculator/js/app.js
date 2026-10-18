/**
 * Calculation Engine Client Application
 * Automatic real-time calculation & 8-Stage audit display
 */

$(document).ready(function () {
  let latestResultData = null;
  let autoCalcTimer = null;

  // Parse Excel / Text tokens and extract 2nd value (B from A_B, A-B, A _ B, etc.)
  function parseTokens(text) {
    if (!text || !text.trim()) return [];

    let cleaned = text.trim();

    // 1. Normalize explicit pairs with spaces around delimiter (e.g., "2 _ 7" -> "2_7")
    cleaned = cleaned.replace(/(\d+)\s*[_\-\/\:\|]\s*(\d+)/g, '$1_$2');

    // 2. Split by whitespace (including tabs, newlines, spaces) or commas/semicolons
    const rawTokens = cleaned.split(/[\s,;]+/);
    const extracted = [];

    for (let raw of rawTokens) {
      if (!raw) continue;
      const t = raw.replace(/^["']|["']$/g, '').trim(); // strip quotes
      if (!t) continue;

      // Match A_B (or A-B, etc. normalized to A_B)
      const m = t.match(/^\d+[_\-\/\:\|](\d+)$/);
      if (m) {
        extracted.push(parseInt(m[1], 10));
      } else if (/^\d+$/.test(t)) {
        extracted.push(parseInt(t, 10));
      } else {
        const parts = t.split(/[_\-\/\:\|]/);
        if (parts.length >= 2 && /^\d+$/.test(parts[1])) {
          extracted.push(parseInt(parts[1], 10));
        }
      }
    }

    // Fallback/Future-proofing: If 10 raw numbers were extracted (e.g., 5 pairs of A B like "2 7 2 7 2 6 2 3 1 1")
    if (extracted.length === 10) {
      const pair2nd = [];
      for (let i = 1; i < 10; i += 2) {
        pair2nd.push(extracted[i]);
      }
      return pair2nd;
    }

    return extracted;
  }

  function updateLivePreview(inputId, previewId) {
    const text = $(inputId).val();
    const vals = parseTokens(text);
    const $prev = $(previewId);

    if (vals.length === 0) {
      $prev.html("");
    } else if (vals.length === 5) {
      $prev.html(
        `<span class="preview-success-title">✓ Extracted 2nd Values:</span> ` +
        `<span class="preview-success-pill">` +
        `a=${vals[0]}, b=${vals[1]}, c=${vals[2]}, d=${vals[3]}, e=${vals[4]}</span>`
      );
    } else {
      $prev.html(
        `<span class="preview-warning-text">Found ${vals.length} of 5 values: [${vals.join(", ")}]</span>`
      );
    }
  }

  // Theme Switcher Logic (Default: Light/White Theme)
  const savedTheme = localStorage.getItem("theme") || "light";
  setTheme(savedTheme);

  $("#theme-toggle").on("click", function () {
    const currentTheme = $("html").attr("data-theme") === "dark" ? "dark" : "light";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    setTheme(newTheme);
  });

  function setTheme(theme) {
    if (theme === "dark") {
      $("html").attr("data-theme", "dark");
    } else {
      $("html").attr("data-theme", "light");
    }
    localStorage.setItem("theme", theme);
  }

  // Automatic Calculation Logic
  function triggerAutoCalculate() {
    const mainText = $("#main_input").val().trim();
    const calcText = $("#calc_input").val().trim();
    const origVal = $("#original_value_input").val().trim();

    // If both fields are empty, hide results and error banner
    if (!mainText && !calcText) {
      $("#results-section").fadeOut(150);
      $("#error-alert").fadeOut(150);
      latestResultData = null;
      updateIndicator("ready", "Automatic Calculation Active");
      return;
    }

    const mainVals = parseTokens(mainText);
    const calcVals = parseTokens(calcText);

    // If either input does not have exactly 5 values, hide stale results!
    if (mainVals.length !== 5 || calcVals.length !== 5) {
      $("#results-section").fadeOut(150);
      latestResultData = null;
      if (mainText && calcText) {
        updateIndicator("waiting", `Waiting for 5 values in both fields (${mainVals.length}/5 Main, ${calcVals.length}/5 Calc)...`);
      } else {
        updateIndicator("waiting", "Waiting for both inputs...");
      }
      return;
    }

    // Both fields have exactly 5 values -> execute automatic calculation
    updateIndicator("calculating", "Calculating...");
    $("#error-alert").fadeOut(100);

    const payload = {
      main_input: mainText,
      calc_input: calcText,
      original_value: origVal || null,
      stage6_main: 1,
      stage6_calc: 1
    };

    $.ajax({
      url: "/api/calculate/",
      type: "POST",
      data: JSON.stringify(payload),
      contentType: "application/json",
      headers: {
        "X-CSRFToken": getCsrfToken()
      },
      success: function (response) {
        if (response.success) {
          latestResultData = response.data;
          renderResults(response.data);
          $("#results-section").fadeIn(200);
          updateIndicator("success", "Calculated Successfully ✓");
        } else {
          showError(response.error || "Calculation failed.");
          $("#results-section").fadeOut(150);
          updateIndicator("error", "Calculation Error");
        }
      },
      error: function (xhr) {
        let msg = "An error occurred while calculating.";
        if (xhr.responseJSON && xhr.responseJSON.error) {
          msg = xhr.responseJSON.error;
        }
        showError(msg);
        $("#results-section").fadeOut(150);
        updateIndicator("error", "Calculation Error");
      }
    });
  }

  function scheduleAutoCalculate(delay = 180) {
    clearTimeout(autoCalcTimer);
    autoCalcTimer = setTimeout(triggerAutoCalculate, delay);
  }

  function updateIndicator(state, text) {
    const $text = $("#auto-calc-text");
    const $badge = $("#auto-calc-indicator");
    if (!$text.length) return;

    $text.text(text);
    if (state === "calculating") {
      $badge.css("color", "var(--accent-primary)");
    } else if (state === "success") {
      $badge.css("color", "var(--accent-success)");
    } else if (state === "error") {
      $badge.css("color", "var(--accent-danger)");
    } else {
      $badge.css("color", "var(--text-secondary)");
    }
  }

  // Setup input listeners for instant live preview and auto calculation
  $("#main_input").on("input keyup change", function () {
    updateLivePreview("#main_input", "#main-preview");
    scheduleAutoCalculate(150);
  });
  $("#main_input").on("paste", function () {
    setTimeout(function () {
      updateLivePreview("#main_input", "#main-preview");
      scheduleAutoCalculate(30);
    }, 30);
  });

  $("#calc_input").on("input keyup change", function () {
    updateLivePreview("#calc_input", "#calc-preview");
    scheduleAutoCalculate(150);
  });
  $("#calc_input").on("paste", function () {
    setTimeout(function () {
      updateLivePreview("#calc_input", "#calc-preview");
      scheduleAutoCalculate(30);
    }, 30);
  });

  $("#original_value_input").on("input keyup change paste", function () {
    scheduleAutoCalculate(150);
  });

  // Clear inputs and reset all state
  $("#btn-clear").on("click", function () {
    $("#main_input").val("");
    $("#calc_input").val("");
    $("#original_value_input").val("");
    $("#main-preview").html("");
    $("#calc-preview").html("");
    $("#results-section").fadeOut(150);
    $("#error-alert").fadeOut(150);
    latestResultData = null;
    updateIndicator("ready", "Automatic Calculation Active");
    showToast("Fields cleared");
  });

  // Prevent default form submission
  $("#calc-form").on("submit", function (e) {
    e.preventDefault();
    triggerAutoCalculate();
  });

  // Render results
  function renderResults(data) {
    const mv = data.main_vals;
    const cv = data.calc_vals;

    // Render Original Value 0.85% Adjustment Card (The Two Answers)
    if (data.original_value_adj) {
      const adj = data.original_value_adj;
      $("#orig-val-display").text(adj.original_value);
      $("#orig-adj-display").text(`±${adj.adjustment}`);

      $("#ans-addition-val").text(adj.addition_result.toFixed(2));
      $("#ans-addition-formula").text(`${adj.original_value} + ${adj.adjustment} = ${adj.addition_result.toFixed(2)}`);

      $("#ans-subtraction-val").text(adj.subtraction_result.toFixed(2));
      $("#ans-subtraction-formula").text(`${adj.original_value} - ${adj.adjustment} = ${adj.subtraction_result.toFixed(2)}`);

      $("#orig-val-results-card").fadeIn(200);
    } else {
      $("#orig-val-results-card").hide();
    }

    // Extracted pills
    $("#extracted-main-vals").text(`a=${mv[0]}, b=${mv[1]}, c=${mv[2]}, d=${mv[3]}, e=${mv[4]}`);
    $("#extracted-calc-vals").text(`a=${cv[0]}, b=${cv[1]}, c=${cv[2]}, d=${cv[3]}, e=${cv[4]}`);

    // Final total hero
    $("#hero-total-score").text(data.final_total);

    // Render Stage Cards (Stages 1 through 7)
    const $grid = $("#stages-grid");
    $grid.empty();

    data.stages.forEach(function (stage) {
      const cardHtml = buildStageCard(stage);
      $grid.append(cardHtml);
    });

    // Render Stage 8 Equation
    const equationText = data.stage8_equation || (data.stages.map(s => s.points).join(" + ") + ` = ${data.final_total} POINTS`);
    $("#stage8-equation").text(equationText);
  }

  function buildStageCard(s) {
    const num = s.stage;
    const name = s.name;
    const pts = s.points;
    const hasPtsClass = pts > 0 ? "has-points" : "";

    let detailsHtml = "";

    if (num === 1) {
      // Stage 1 — Combination Divisibility by 3 + Ratio Divisibility
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="calc-section-title">📄 Main File Values [${m.vals.join(', ')}]</div>
        <div class="calc-step-line">
          <strong>a+b+c:</strong> ${m.s1_formula} → ${m.s1} % 3 = <strong>${m.s1_rem}</strong> → 
          ${m.s1_div ? '<span class="status-badge pass">Divisible by 3 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 3 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-step-line">
          <strong>c+d+e:</strong> ${m.s2_formula} → ${m.s2} % 3 = <strong>${m.s2_rem}</strong> → 
          ${m.s2_div ? '<span class="status-badge pass">Divisible by 3 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 3 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-step-line">
          <strong>Ratio (S1/S2):</strong> ${m.ratio_str}${m.quotient !== null ? ' = <strong>' + m.quotient + '</strong>' : ''} → 
          ${m.ratio_qualifies ? '<span class="status-badge pass">' + m.ratio_reasons.join(', ') + ' ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">No qualifying condition ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-subtotal-row">
          <span>Main Subtotal:</span>
          <span>${m.comb_points} (Comb) + ${m.ratio_points} (Ratio) = <strong>${m.points} pts</strong></span>
        </div>

        <div class="calc-section-title" style="margin-top:0.85rem;">📊 Calculation File Values [${c.vals.join(', ')}]</div>
        <div class="calc-step-line">
          <strong>a+b+c:</strong> ${c.s1_formula} → ${c.s1} % 3 = <strong>${c.s1_rem}</strong> → 
          ${c.s1_div ? '<span class="status-badge pass">Divisible by 3 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 3 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-step-line">
          <strong>c+d+e:</strong> ${c.s2_formula} → ${c.s2} % 3 = <strong>${c.s2_rem}</strong> → 
          ${c.s2_div ? '<span class="status-badge pass">Divisible by 3 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 3 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-step-line">
          <strong>Ratio (S1/S2):</strong> ${c.ratio_str}${c.quotient !== null ? ' = <strong>' + c.quotient + '</strong>' : ''} → 
          ${c.ratio_qualifies ? '<span class="status-badge pass">' + c.ratio_reasons.join(', ') + ' ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">No qualifying condition ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-subtotal-row">
          <span>Calc Subtotal:</span>
          <span>${c.comb_points} (Comb) + ${c.ratio_points} (Ratio) = <strong>${c.points} pts</strong></span>
        </div>

        <div class="calc-subtotal-row" style="margin-top:0.75rem; border-top:2px solid var(--border-active); font-size:0.95rem;">
          <span>Stage 1 Total:</span>
          <span>${m.points} (Main) + ${c.points} (Calc) = <strong>${pts} pts</strong></span>
        </div>
      `;
    } else if (num === 2) {
      // Stage 2 — Total Sum Divisibility by 2 and 3
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="calc-section-title">📄 Main File Values</div>
        <div class="calc-step-line"><strong>Sum:</strong> ${m.sum_formula}</div>
        <div class="calc-step-line">
          <strong>Divisible by 2:</strong> ${m.sum} % 2 = <strong>${m.div_by_2_rem}</strong> → 
          ${m.div_by_2 ? '<span class="status-badge pass">Divisible by 2 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 2 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-step-line">
          <strong>Divisible by 3:</strong> ${m.sum} % 3 = <strong>${m.div_by_3_rem}</strong> → 
          ${m.div_by_3 ? '<span class="status-badge pass">Divisible by 3 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 3 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-subtotal-row">
          <span>Main Subtotal:</span>
          <span><strong>${m.points} pts</strong></span>
        </div>

        <div class="calc-section-title" style="margin-top:0.85rem;">📊 Calculation File Values</div>
        <div class="calc-step-line"><strong>Sum:</strong> ${c.sum_formula}</div>
        <div class="calc-step-line">
          <strong>Divisible by 2:</strong> ${c.sum} % 2 = <strong>${c.div_by_2_rem}</strong> → 
          ${c.div_by_2 ? '<span class="status-badge pass">Divisible by 2 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 2 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-step-line">
          <strong>Divisible by 3:</strong> ${c.sum} % 3 = <strong>${c.div_by_3_rem}</strong> → 
          ${c.div_by_3 ? '<span class="status-badge pass">Divisible by 3 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Not divisible by 3 ✗</span> <strong>+0 pts</strong>'}
        </div>
        <div class="calc-subtotal-row">
          <span>Calc Subtotal:</span>
          <span><strong>${c.points} pts</strong></span>
        </div>

        <div class="calc-subtotal-row" style="margin-top:0.75rem; border-top:2px solid var(--border-active); font-size:0.95rem;">
          <span>Stage 2 Total:</span>
          <span>${m.points} (Main) + ${c.points} (Calc) = <strong>${pts} pts</strong></span>
        </div>
      `;
    } else if (num === 3) {
      // Stage 3 — Threshold 5 Calculation + Pattern Comparison
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="calc-section-title">📄 Main File (Threshold 5)</div>
        <div class="calc-step-line"><strong>a+c:</strong> ${m.ac_formula} → <strong>${m.ac_threshold}</strong></div>
        <div class="calc-step-line"><strong>c+e:</strong> ${m.ce_formula} → <strong>${m.ce_threshold}</strong></div>
        <div class="calc-step-line"><strong>Main Pattern:</strong> <span class="pattern-chip">${m.pattern}</span> (${m.pattern_type})</div>

        <div class="calc-section-title" style="margin-top:0.85rem;">📊 Calculation File (Threshold 5)</div>
        <div class="calc-step-line"><strong>a+c:</strong> ${c.ac_formula} → <strong>${c.ac_threshold}</strong></div>
        <div class="calc-step-line"><strong>c+e:</strong> ${c.ce_formula} → <strong>${c.ce_threshold}</strong></div>
        <div class="calc-step-line"><strong>Calc Pattern:</strong> <span class="pattern-chip">${c.pattern}</span> (${c.pattern_type})</div>

        <div class="calc-subtotal-row" style="margin-top:0.75rem; border-top:2px solid var(--border-active);">
          <span>Pattern Comparison:</span>
          <span>${s.comparison} → ${pts === 1 ? '<span class="status-badge pass">Different types (Mixed vs Homogeneous) ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Same type ✗</span> <strong>+0 pts</strong>'}</span>
        </div>
      `;
    } else if (num === 4) {
      // Stage 4 — Inner Calculation Using 10
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="calc-section-title">📄 Main File (a+c) + (c+e) vs 10</div>
        <div class="calc-step-line"><strong>Formula:</strong> ${m.formula} → <strong>${m.threshold}</strong></div>

        <div class="calc-section-title" style="margin-top:0.85rem;">📊 Calculation File (a+c) + (c+e) vs 10</div>
        <div class="calc-step-line"><strong>Formula:</strong> ${c.formula} → <strong>${c.threshold}</strong></div>

        <div class="calc-subtotal-row" style="margin-top:0.75rem; border-top:2px solid var(--border-active);">
          <span>Sign Comparison:</span>
          <span>${s.comparison} → ${pts === 1 ? '<span class="status-badge pass">Different signs ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Same sign ✗</span> <strong>+0 pts</strong>'}</span>
        </div>
      `;
    } else if (num === 5) {
      // Stage 5 — Individual Inner Calculation Against 10
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="calc-section-title">📄 Main File (Separate vs 10)</div>
        <div class="calc-step-line"><strong>a+c:</strong> ${m.ac_formula} → <strong>${m.ac_threshold}</strong></div>
        <div class="calc-step-line"><strong>c+e:</strong> ${m.ce_formula} → <strong>${m.ce_threshold}</strong></div>
        <div class="calc-step-line"><strong>Main Pattern:</strong> <span class="pattern-chip">${m.pattern}</span> (${m.pattern_type})</div>

        <div class="calc-section-title" style="margin-top:0.85rem;">📊 Calculation File (Separate vs 10)</div>
        <div class="calc-step-line"><strong>a+c:</strong> ${c.ac_formula} → <strong>${c.ac_threshold}</strong></div>
        <div class="calc-step-line"><strong>c+e:</strong> ${c.ce_formula} → <strong>${c.ce_threshold}</strong></div>
        <div class="calc-step-line"><strong>Calc Pattern:</strong> <span class="pattern-chip">${c.pattern}</span> (${c.pattern_type})</div>

        <div class="calc-subtotal-row" style="margin-top:0.75rem; border-top:2px solid var(--border-active);">
          <span>Pattern Comparison:</span>
          <span>${s.comparison} → ${pts === 1 ? '<span class="status-badge pass">Different types (Mixed vs Homogeneous) ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Same type ✗</span> <strong>+0 pts</strong>'}</span>
        </div>
      `;
    } else if (num === 6) {
      // Stage 6 — P1/P2 Digit Calculation + Pattern Comparison + Vertical Calculation
      const p1 = s.P1;
      const p2 = s.P2;
      const vert = s.vertical;

      detailsHtml = `
        <div class="calc-section-title">Part A & B: P1 & P2 Digit Pattern Comparison</div>
        <div class="calc-step-line">
          <strong>P1 (Main Sum):</strong> ${p1.sum_formula} → Digits: [<strong>${p1.digits.join(', ')}</strong>]
        </div>
        <div class="calc-step-line">
          <strong>P1 Digit Checks:</strong> ${p1.d1_threshold}, ${p1.d2_threshold} → Pattern: <span class="pattern-chip">${p1.pattern}</span> (${p1.pattern_type})
        </div>
        <div class="calc-step-line" style="margin-top:0.5rem;">
          <strong>P2 (Calc Sum):</strong> ${p2.sum_formula} → Digits: [<strong>${p2.digits.join(', ')}</strong>]
        </div>
        <div class="calc-step-line">
          <strong>P2 Digit Checks:</strong> ${p2.d1_threshold}, ${p2.d2_threshold} → Pattern: <span class="pattern-chip">${p2.pattern}</span> (${p2.pattern_type})
        </div>
        <div class="calc-subtotal-row" style="margin-top:0.4rem;">
          <span>Pattern Comparison:</span>
          <span>${s.pattern_comparison} → ${s.pattern_points === 1 ? '<span class="status-badge pass">Different types ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Same type ✗</span> <strong>+0 pts</strong>'}</span>
        </div>

        <div class="calc-section-title" style="margin-top:0.85rem;">Part C: Vertical Calculation</div>
        <div class="calc-step-line">
          <strong>Formula:</strong> |Main value - Calculation value| = <strong>${vert.formula}</strong> → <strong>+${vert.points} pts</strong>
        </div>

        <div class="calc-subtotal-row" style="margin-top:0.75rem; border-top:2px solid var(--border-active); font-size:0.95rem;">
          <span>Stage 6 Subtotal:</span>
          <span>${s.pattern_points} (Pattern) + ${vert.points} (Vertical) = <strong>${pts} pts</strong></span>
        </div>
      `;
    } else if (num === 7) {
      // Stage 7 — P1/P2 Average Divisibility by 2
      detailsHtml = `
        <div class="calc-section-title">P1 & P2 Average Divisibility Calculation</div>
        <div class="calc-step-line">
          <strong>Input Totals:</strong> P1 = <strong>${s.P1}</strong>, P2 = <strong>${s.P2}</strong>
        </div>
        <div class="calc-step-line">
          <strong>Sum:</strong> ${s.sum_formula}
        </div>
        <div class="calc-step-line">
          <strong>Divisibility Test:</strong> ${s.sum} % 2 = <strong>${s.remainder}</strong> → 
          ${s.div_by_2 ? '<span class="status-badge pass">Divisible by 2 ✓</span>' : '<span class="status-badge fail">Not divisible by 2 (Odd sum) ✗</span>'}
        </div>
        <div class="calc-step-line">
          <strong>Calculated Average:</strong> (${s.P1} + ${s.P2}) / 2 = <strong>${s.average_display}</strong>
        </div>

        <div class="calc-subtotal-row" style="margin-top:0.75rem; border-top:2px solid var(--border-active); font-size:0.95rem;">
          <span>Stage 7 Total:</span>
          <span>${s.div_by_2 ? '<span class="status-badge pass">Divisible by 2 ✓</span> <strong>+1 pt</strong>' : '<span class="status-badge fail">Odd sum, non-integer average ✗</span> <strong>+0 pts</strong>'}</span>
        </div>
      `;
    }

    return `
      <div class="stage-card">
        <div class="stage-header">
          <div>
            <span class="stage-number">Stage ${num}</span>
            <div class="stage-title">${name}</div>
          </div>
          <div class="points-badge ${hasPtsClass}">
            ${pts} <span style="font-size:0.75rem; font-weight:500;">pts</span>
          </div>
        </div>
        <div class="stage-details">
          ${detailsHtml}
        </div>
      </div>
    `;
  }

  // Copy full audit report
  $("#btn-copy-report").on("click", function () {
    if (!latestResultData) return;

    const data = latestResultData;
    let txt = `========================================================================\n`;
    txt += `                    8-STAGE CALCULATION AUDIT REPORT\n`;
    txt += `========================================================================\n`;
    txt += `Main File Extracted Values:        ${JSON.stringify(data.main_vals)}\n`;
    txt += `Calculation File Extracted Values: ${JSON.stringify(data.calc_vals)}\n`;
    if (data.original_value_adj) {
      txt += `Original Value Adjustment:         ${data.original_value_adj.original_value} (0.85% = ±${data.original_value_adj.adjustment})\n`;
      txt += `  - Addition Result:               ${data.original_value_adj.formula_add}\n`;
      txt += `  - Subtraction Result:            ${data.original_value_adj.formula_sub}\n`;
    }
    txt += `------------------------------------------------------------------------\n`;
    data.stages.forEach(function (s) {
      txt += `Stage ${s.stage}: ${s.name.padEnd(54)} = ${s.points} pts\n`;
    });
    txt += `------------------------------------------------------------------------\n`;
    txt += `STAGE 8 -- FINAL TOTAL EQUATION: ${data.stage8_equation || data.final_total + ' POINTS'}\n`;
    txt += `========================================================================\n`;

    navigator.clipboard.writeText(txt).then(function () {
      showToast("Audit report copied to clipboard!");
    });
  });

  function showError(msg) {
    $("#error-alert").text(msg).fadeIn(150);
  }

  function showToast(msg) {
    const $toast = $("#toast-notification");
    $toast.text(msg).fadeIn();
    setTimeout(function () {
      $toast.fadeOut();
    }, 2500);
  }

  function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === "csrftoken=") {
          cookieValue = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return cookieValue || "";
  }
});
