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
      const origValNum = adj.original_value;
      const addVal = adj.addition_result;
      const subVal = adj.subtraction_result;

      $("#orig-val-display").text(origValNum);
      $("#orig-adj-display").text(`±${adj.adjustment}`);

      // Answer 1: Addition Result
      $("#ans-addition-val").text(addVal.toFixed(2));
      $("#ans-addition-formula").text(`${origValNum} + ${adj.adjustment} = ${addVal.toFixed(2)}`);

      // Answer 2: Subtraction Result
      $("#ans-subtraction-val").text(subVal.toFixed(2));
      $("#ans-subtraction-formula").text(`${origValNum} - ${adj.adjustment} = ${subVal.toFixed(2)}`);

      // Dynamic Semantic Color Classes
      // Higher value than original -> RED
      const $cardAdd = $("#adj-card-add");
      const $valAdd = $("#ans-addition-val");
      const $badgeAdd = $("#adj-badge-add");
      if (addVal >= origValNum) {
        $cardAdd.addClass("adj-card-higher").removeClass("adj-card-lower");
        $valAdd.addClass("val-higher").removeClass("val-lower");
        $badgeAdd.attr("class", "adj-status-badge badge-higher").html("&uarr; Higher Value");
      } else {
        $cardAdd.addClass("adj-card-lower").removeClass("adj-card-higher");
        $valAdd.addClass("val-lower").removeClass("val-higher");
        $badgeAdd.attr("class", "adj-status-badge badge-lower").html("&darr; Lower Value");
      }

      // Lower value than original -> GREEN
      const $cardSub = $("#adj-card-sub");
      const $valSub = $("#ans-subtraction-val");
      const $badgeSub = $("#adj-badge-sub");
      if (subVal <= origValNum) {
        $cardSub.addClass("adj-card-lower").removeClass("adj-card-higher");
        $valSub.addClass("val-lower").removeClass("val-higher");
        $badgeSub.attr("class", "adj-status-badge badge-lower").html("&darr; Lower Value");
      } else {
        $cardSub.addClass("adj-card-higher").removeClass("adj-card-lower");
        $valSub.addClass("val-higher").removeClass("val-lower");
        $badgeSub.attr("class", "adj-status-badge badge-higher").html("&uarr; Higher Value");
      }

      $("#orig-val-results-card").fadeIn(200);
    } else {
      $("#orig-val-results-card").hide();
    }

    // Extracted values
    $("#extracted-main-vals").text(`a=${mv[0]}, b=${mv[1]}, c=${mv[2]}, d=${mv[3]}, e=${mv[4]}`);
    $("#extracted-calc-vals").text(`a=${cv[0]}, b=${cv[1]}, c=${cv[2]}, d=${cv[3]}, e=${cv[4]}`);

    // Final total hero
    $("#hero-total-score").text(data.final_total);

    // Hero quick breakdown chips
    const $chipsContainer = $("#hero-stages-pills");
    $chipsContainer.empty();
    data.stages.forEach(function (stage) {
      const chipClass = stage.points > 0 ? "chip-has-pts" : "";
      $chipsContainer.append(`
        <div class="hero-stage-chip ${chipClass}">
          <span class="chip-stage">S${stage.stage}</span>
          <span class="chip-pts">${stage.points} pt${stage.points === 1 ? '' : 's'}</span>
        </div>
      `);
    });

    // Render Stage Cards (Stages 1 through 7)
    const $grid = $("#stages-grid");
    $grid.empty();

    data.stages.forEach(function (stage) {
      const cardHtml = buildStageCard(stage);
      $grid.append(cardHtml);
    });

    // Render Stage 8 Equation (matches exact required format)
    const stageValues = data.stages.map(s => s.points).join(" + ");
    const equationText = `${stageValues} = ${data.final_total} POINTS`;
    $("#stage8-equation").text(equationText);
  }

  function buildStageCard(s) {
    const num = s.stage;
    const name = s.name;
    const pts = s.points;
    const hasPtsClass = pts > 0 ? "has-points" : "";

    let detailsHtml = "";
    let subtotalHtml = "";

    if (num === 1) {
      // Stage 1 — Combination Divisibility by 3 + Ratio Divisibility
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="audit-block">
          <div class="audit-block-header">Main File Values: [${m.vals.join(', ')}]</div>
          
          <div class="calc-group">
            <div class="calc-label">Combination 1: a + b + c</div>
            <div class="calc-formula">${m.s1_formula}</div>
            <div class="calc-formula">${m.s1} % 3 = ${m.s1_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${m.s1_div ? '<span class="status-pass-text">Divisible by 3</span>' : '<span class="status-fail-text">Not divisible by 3</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${m.s1_pts} pt</span>
            </div>
          </div>

          <div class="calc-group">
            <div class="calc-label">Combination 2: c + d + e</div>
            <div class="calc-formula">${m.s2_formula}</div>
            <div class="calc-formula">${m.s2} % 3 = ${m.s2_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${m.s2_div ? '<span class="status-pass-text">Divisible by 3</span>' : '<span class="status-fail-text">Not divisible by 3</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${m.s2_pts} pt</span>
            </div>
          </div>

          <div class="calc-group">
            <div class="calc-label">Ratio Check: S1 / S2</div>
            <div class="calc-formula">Ratio = ${m.ratio_str}${m.quotient !== null ? ' = ' + m.quotient : ''}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Condition:</strong> ${m.ratio_qualifies ? '<span class="status-pass-text">' + m.ratio_reasons.join(', ') + '</span>' : '<span class="status-fail-text">No qualifying condition</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${m.ratio_points} pt</span>
            </div>
          </div>

          <div class="block-subtotal">
            <span>Main Subtotal:</span>
            <strong>${m.comb_points} (Comb) + ${m.ratio_points} (Ratio) = ${m.points} pts</strong>
          </div>
        </div>

        <div class="audit-block">
          <div class="audit-block-header">Calculation File Values: [${c.vals.join(', ')}]</div>
          
          <div class="calc-group">
            <div class="calc-label">Combination 1: a + b + c</div>
            <div class="calc-formula">${c.s1_formula}</div>
            <div class="calc-formula">${c.s1} % 3 = ${c.s1_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${c.s1_div ? '<span class="status-pass-text">Divisible by 3</span>' : '<span class="status-fail-text">Not divisible by 3</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${c.s1_pts} pt</span>
            </div>
          </div>

          <div class="calc-group">
            <div class="calc-label">Combination 2: c + d + e</div>
            <div class="calc-formula">${c.s2_formula}</div>
            <div class="calc-formula">${c.s2} % 3 = ${c.s2_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${c.s2_div ? '<span class="status-pass-text">Divisible by 3</span>' : '<span class="status-fail-text">Not divisible by 3</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${c.s2_pts} pt</span>
            </div>
          </div>

          <div class="calc-group">
            <div class="calc-label">Ratio Check: S1 / S2</div>
            <div class="calc-formula">Ratio = ${c.ratio_str}${c.quotient !== null ? ' = ' + c.quotient : ''}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Condition:</strong> ${c.ratio_qualifies ? '<span class="status-pass-text">' + c.ratio_reasons.join(', ') + '</span>' : '<span class="status-fail-text">No qualifying condition</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${c.ratio_points} pt</span>
            </div>
          </div>

          <div class="block-subtotal">
            <span>Calc Subtotal:</span>
            <strong>${c.comb_points} (Comb) + ${c.ratio_points} (Ratio) = ${c.points} pts</strong>
          </div>
        </div>
      `;

      subtotalHtml = `${m.points} (Main) + ${c.points} (Calc) = <strong>${pts} pts</strong>`;
    } else if (num === 2) {
      // Stage 2 — Total Sum Divisibility by 2 and 3
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="audit-block">
          <div class="audit-block-header">Main File Values</div>
          <div class="calc-group">
            <div class="calc-label">Total Sum</div>
            <div class="calc-formula">${m.sum_formula}</div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Divisibility by 2</div>
            <div class="calc-formula">${m.sum} % 2 = ${m.div_by_2_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${m.div_by_2 ? '<span class="status-pass-text">Divisible by 2</span>' : '<span class="status-fail-text">Not divisible by 2</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${m.div_by_2_pts} pt</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Divisibility by 3</div>
            <div class="calc-formula">${m.sum} % 3 = ${m.div_by_3_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${m.div_by_3 ? '<span class="status-pass-text">Divisible by 3</span>' : '<span class="status-fail-text">Not divisible by 3</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${m.div_by_3_pts} pt</span>
            </div>
          </div>
          <div class="block-subtotal">
            <span>Main Subtotal:</span>
            <strong>${m.points} pts</strong>
          </div>
        </div>

        <div class="audit-block">
          <div class="audit-block-header">Calculation File Values</div>
          <div class="calc-group">
            <div class="calc-label">Total Sum</div>
            <div class="calc-formula">${c.sum_formula}</div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Divisibility by 2</div>
            <div class="calc-formula">${c.sum} % 2 = ${c.div_by_2_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${c.div_by_2 ? '<span class="status-pass-text">Divisible by 2</span>' : '<span class="status-fail-text">Not divisible by 2</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${c.div_by_2_pts} pt</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Divisibility by 3</div>
            <div class="calc-formula">${c.sum} % 3 = ${c.div_by_3_rem}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${c.div_by_3 ? '<span class="status-pass-text">Divisible by 3</span>' : '<span class="status-fail-text">Not divisible by 3</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${c.div_by_3_pts} pt</span>
            </div>
          </div>
          <div class="block-subtotal">
            <span>Calc Subtotal:</span>
            <strong>${c.points} pts</strong>
          </div>
        </div>
      `;

      subtotalHtml = `${m.points} (Main) + ${c.points} (Calc) = <strong>${pts} pts</strong>`;
    } else if (num === 3) {
      // Stage 3 — Threshold 5 Calculation + Pattern Comparison
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="audit-block">
          <div class="audit-block-header">Main File (Threshold 5)</div>
          <div class="calc-group">
            <div class="calc-label">Combination a + c</div>
            <div class="calc-formula">${m.ac_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${m['a+c']} ${m['a+c'] >= 5 ? '&ge;' : '<'} 5 &rarr; Pattern '<strong>${m.p1}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Combination c + e</div>
            <div class="calc-formula">${m.ce_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${m['c+e']} ${m['c+e'] >= 5 ? '&ge;' : '<'} 5 &rarr; Pattern '<strong>${m.p2}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Main Pattern:</strong> <span class="pattern-pill">${m.pattern}</span> (${m.pattern_type})</span>
            </div>
          </div>
        </div>

        <div class="audit-block">
          <div class="audit-block-header">Calculation File (Threshold 5)</div>
          <div class="calc-group">
            <div class="calc-label">Combination a + c</div>
            <div class="calc-formula">${c.ac_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${c['a+c']} ${c['a+c'] >= 5 ? '&ge;' : '<'} 5 &rarr; Pattern '<strong>${c.p1}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Combination c + e</div>
            <div class="calc-formula">${c.ce_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${c['c+e']} ${c['c+e'] >= 5 ? '&ge;' : '<'} 5 &rarr; Pattern '<strong>${c.p2}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Calc Pattern:</strong> <span class="pattern-pill">${c.pattern}</span> (${c.pattern_type})</span>
            </div>
          </div>
        </div>

        <div class="audit-block audit-comparison-block">
          <div class="audit-block-header">Pattern Comparison</div>
          <div class="calc-formula">${s.comparison}</div>
          <div class="calc-meta-row">
            <span class="calc-meta-item"><strong>Condition:</strong> ${pts === 1 ? '<span class="status-pass-text">Different types (Mixed vs Homogeneous)</span>' : '<span class="status-fail-text">Same pattern type</span>'}</span>
            <span class="calc-meta-item"><strong>Points awarded:</strong> ${pts} pt</span>
          </div>
        </div>
      `;

      subtotalHtml = `Stage 3 Total = <strong>${pts} pts</strong>`;
    } else if (num === 4) {
      // Stage 4 — Inner Calculation Using 10
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="audit-block">
          <div class="audit-block-header">Main File: (a + c) + (c + e) vs 10</div>
          <div class="calc-group">
            <div class="calc-label">Formula</div>
            <div class="calc-formula">${m.formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${m.combined} ${m.combined >= 10 ? '&ge;' : '<'} 10 &rarr; Sign '<strong>${m.result}</strong>'</span>
            </div>
          </div>
        </div>

        <div class="audit-block">
          <div class="audit-block-header">Calculation File: (a + c) + (c + e) vs 10</div>
          <div class="calc-group">
            <div class="calc-label">Formula</div>
            <div class="calc-formula">${c.formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${c.combined} ${c.combined >= 10 ? '&ge;' : '<'} 10 &rarr; Sign '<strong>${c.result}</strong>'</span>
            </div>
          </div>
        </div>

        <div class="audit-block audit-comparison-block">
          <div class="audit-block-header">Sign Comparison</div>
          <div class="calc-formula">Main '${m.result}' vs Calc '${c.result}'</div>
          <div class="calc-meta-row">
            <span class="calc-meta-item"><strong>Condition:</strong> ${pts === 1 ? '<span class="status-pass-text">Different signs</span>' : '<span class="status-fail-text">Same sign</span>'}</span>
            <span class="calc-meta-item"><strong>Points awarded:</strong> ${pts} pt</span>
          </div>
        </div>
      `;

      subtotalHtml = `Stage 4 Total = <strong>${pts} pts</strong>`;
    } else if (num === 5) {
      // Stage 5 — Individual Inner Calculation Against 10
      const m = s.main;
      const c = s.calc;

      detailsHtml = `
        <div class="audit-block">
          <div class="audit-block-header">Main File (Separate vs 10)</div>
          <div class="calc-group">
            <div class="calc-label">Combination a + c</div>
            <div class="calc-formula">${m.ac_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${m['a+c']} ${m['a+c'] >= 10 ? '&ge;' : '<'} 10 &rarr; '<strong>${m.p1}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Combination c + e</div>
            <div class="calc-formula">${m.ce_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${m['c+e']} ${m['c+e'] >= 10 ? '&ge;' : '<'} 10 &rarr; '<strong>${m.p2}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Main Pattern:</strong> <span class="pattern-pill">${m.pattern}</span> (${m.pattern_type})</span>
            </div>
          </div>
        </div>

        <div class="audit-block">
          <div class="audit-block-header">Calculation File (Separate vs 10)</div>
          <div class="calc-group">
            <div class="calc-label">Combination a + c</div>
            <div class="calc-formula">${c.ac_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${c['a+c']} ${c['a+c'] >= 10 ? '&ge;' : '<'} 10 &rarr; '<strong>${c.p1}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Combination c + e</div>
            <div class="calc-formula">${c.ce_formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Comparison:</strong> ${c['c+e']} ${c['c+e'] >= 10 ? '&ge;' : '<'} 10 &rarr; '<strong>${c.p2}</strong>'</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Calc Pattern:</strong> <span class="pattern-pill">${c.pattern}</span> (${c.pattern_type})</span>
            </div>
          </div>
        </div>

        <div class="audit-block audit-comparison-block">
          <div class="audit-block-header">Pattern Comparison</div>
          <div class="calc-formula">${s.comparison}</div>
          <div class="calc-meta-row">
            <span class="calc-meta-item"><strong>Condition:</strong> ${pts === 1 ? '<span class="status-pass-text">Different types (Mixed vs Homogeneous)</span>' : '<span class="status-fail-text">Same pattern type</span>'}</span>
            <span class="calc-meta-item"><strong>Points awarded:</strong> ${pts} pt</span>
          </div>
        </div>
      `;

      subtotalHtml = `Stage 5 Total = <strong>${pts} pts</strong>`;
    } else if (num === 6) {
      // Stage 6 — P1/P2 Digit Calculation + Pattern Comparison + Vertical Calculation
      const p1 = s.P1;
      const p2 = s.P2;
      const vert = s.vertical;

      detailsHtml = `
        <div class="audit-block">
          <div class="audit-block-header">Part A & B: P1 & P2 Digit Patterns</div>
          <div class="calc-group">
            <div class="calc-label">P1 (Main Sum)</div>
            <div class="calc-formula">${p1.sum_formula} &rarr; Digits: [${p1.digits.join(', ')}]</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Checks:</strong> ${p1.d1} ${p1.d1 >= 5 ? '&ge;' : '<'} 5, ${p1.d2} ${p1.d2 >= 5 ? '&ge;' : '<'} 5</span>
              <span class="calc-meta-item"><strong>Pattern:</strong> <span class="pattern-pill">${p1.pattern}</span> (${p1.pattern_type})</span>
            </div>
          </div>

          <div class="calc-group">
            <div class="calc-label">P2 (Calc Sum)</div>
            <div class="calc-formula">${p2.sum_formula} &rarr; Digits: [${p2.digits.join(', ')}]</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Checks:</strong> ${p2.d1} ${p2.d1 >= 5 ? '&ge;' : '<'} 5, ${p2.d2} ${p2.d2 >= 5 ? '&ge;' : '<'} 5</span>
              <span class="calc-meta-item"><strong>Pattern:</strong> <span class="pattern-pill">${p2.pattern}</span> (${p2.pattern_type})</span>
            </div>
          </div>

          <div class="calc-group">
            <div class="calc-formula">${s.pattern_comparison}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Condition:</strong> ${s.pattern_points === 1 ? '<span class="status-pass-text">Different types (Mixed vs Homogeneous)</span>' : '<span class="status-fail-text">Same pattern type</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${s.pattern_points} pt</span>
            </div>
          </div>
        </div>

        <div class="audit-block">
          <div class="audit-block-header">Part C: Vertical Calculation</div>
          <div class="calc-group">
            <div class="calc-label">Formula: |Main value - Calculation value|</div>
            <div class="calc-formula">${vert.formula}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> Absolute Difference = ${vert.points}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${vert.points} pts</span>
            </div>
          </div>
        </div>
      `;

      subtotalHtml = `${s.pattern_points} (Pattern) + ${vert.points} (Vertical) = <strong>${pts} pts</strong>`;
    } else if (num === 7) {
      // Stage 7 — P1/P2 Average Divisibility by 2
      detailsHtml = `
        <div class="audit-block">
          <div class="audit-block-header">P1 & P2 Totals & Sum</div>
          <div class="calc-group">
            <div class="calc-label">Input Sums</div>
            <div class="calc-formula">P1 = ${s.P1}, P2 = ${s.P2}</div>
            <div class="calc-formula">Total Sum: ${s.sum_formula}</div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Divisibility Test by 2</div>
            <div class="calc-formula">${s.sum} % 2 = ${s.remainder}</div>
            <div class="calc-meta-row">
              <span class="calc-meta-item"><strong>Result:</strong> ${s.div_by_2 ? '<span class="status-pass-text">Divisible by 2</span>' : '<span class="status-fail-text">Not divisible by 2 (Odd sum)</span>'}</span>
              <span class="calc-meta-item"><strong>Points awarded:</strong> ${s.points} pt</span>
            </div>
          </div>
          <div class="calc-group">
            <div class="calc-label">Calculated Average</div>
            <div class="calc-formula">(${s.P1} + ${s.P2}) / 2 = ${s.average_display}</div>
          </div>
        </div>
      `;

      subtotalHtml = `${s.div_by_2 ? 'Divisible by 2 &rarr; <strong>1 pt</strong>' : 'Non-integer average &rarr; <strong>0 pts</strong>'}`;
    }

    return `
      <div class="stage-card">
        <div class="stage-header">
          <div class="stage-header-title-wrap">
            <span class="stage-tag">Stage ${num}</span>
            <h3 class="stage-title">${name}</h3>
          </div>
          <div class="points-badge ${hasPtsClass}">
            <span class="pts-val">${pts}</span>
            <span class="pts-unit">pts</span>
          </div>
        </div>
        <div class="stage-body">
          ${detailsHtml}
        </div>
        <div class="stage-footer">
          <span class="stage-footer-label">Stage ${num} Subtotal</span>
          <span class="stage-footer-val">${subtotalHtml}</span>
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
