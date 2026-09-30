/**
 * Calculation Engine Client Application
 * Optimized for Excel Copy-Paste Formats (1_2, 1-2, etc.)
 */

$(document).ready(function () {
  let latestResultData = null;

  // Parse Excel / Text tokens and extract 2nd value (B from A_B or A-B)
  function parseTokens(text) {
    if (!text || !text.trim()) return [];
    // Split by whitespace (including tabs, newlines, spaces) or commas
    const rawTokens = text.trim().split(/[\s,]+/);
    const extracted = [];

    for (let raw of rawTokens) {
      if (!raw) continue;
      const t = raw.replace(/^["']|["']$/g, ''); // strip quotes
      if (!t) continue;

      // Match A_B, A-B, or A/B
      const m = t.match(/^\d+[_\-\/](\d+)$/);
      if (m) {
        extracted.push(parseInt(m[1], 10));
      } else if (/^\d+$/.test(t)) {
        extracted.push(parseInt(t, 10));
      } else {
        const parts = t.split(/[_\-\/]/);
        if (parts.length >= 2 && /^\d+$/.test(parts[1])) {
          extracted.push(parseInt(parts[1], 10));
        }
      }
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
        `<span style="color:#34d399; font-weight:600;">✓ Extracted 2nd Values:</span> ` +
        `<span style="color:#f1f5f9; background:rgba(16, 185, 129, 0.15); padding:2px 8px; border-radius:4px; border:1px solid rgba(16, 185, 129, 0.3); font-weight:700;">` +
        `a=${vals[0]}, b=${vals[1]}, c=${vals[2]}, d=${vals[3]}, e=${vals[4]}</span>`
      );
    } else {
      $prev.html(
        `<span style="color:#fbbf24;">Found ${vals.length} of 5 values: [${vals.join(", ")}]</span>`
      );
    }
  }

  // Setup live preview on inputs
  $("#main_input").on("input paste keyup change", function () {
    setTimeout(function () {
      updateLivePreview("#main_input", "#main-preview");
    }, 30);
  });

  $("#calc_input").on("input paste keyup change", function () {
    setTimeout(function () {
      updateLivePreview("#calc_input", "#calc-preview");
    }, 30);
  });

  // Handle .txt file picker inputs
  function setupFilePicker(pickerId, targetTextareaId) {
    $(pickerId).on("change", function (e) {
      const file = e.target.files && e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (evt) {
          $(targetTextareaId).val(evt.target.result);
          $(targetTextareaId).trigger("input");
          showToast(`Loaded ${file.name}`);
        };
        reader.readAsText(file);
      }
    });
  }
  setupFilePicker("#main_file_picker", "#main_input");
  setupFilePicker("#calc_file_picker", "#calc_input");

  // Drag and drop support on textareas
  function setupDragDrop(textareaId) {
    const $el = $(textareaId);
    $el.on("dragover dragenter", function (e) {
      e.preventDefault();
      e.stopPropagation();
      $el.css("border-color", "#6366f1");
    });
    $el.on("dragleave drop", function (e) {
      e.preventDefault();
      e.stopPropagation();
      $el.css("border-color", "");
    });
    $el.on("drop", function (e) {
      const files = e.originalEvent.dataTransfer && e.originalEvent.dataTransfer.files;
      if (files && files.length > 0) {
        const file = files[0];
        const reader = new FileReader();
        reader.onload = function (evt) {
          $el.val(evt.target.result);
          $el.trigger("input");
          showToast(`Loaded ${file.name}`);
        };
        reader.readAsText(file);
      }
    });
  }
  setupDragDrop("#main_input");
  setupDragDrop("#calc_input");

  // Download Text Files (.txt) helper
  function downloadTextFile(filename, content) {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  $("#btn-download-files").on("click", function () {
    const mainText = $("#main_input").val().trim();
    const calcText = $("#calc_input").val().trim();

    if (!mainText && !calcText) {
      showError("No values entered to download.");
      return;
    }

    if (mainText) {
      downloadTextFile("main_file.txt", mainText);
    }
    if (calcText) {
      setTimeout(function () {
        downloadTextFile("calc_file.txt", calcText);
      }, 300);
    }
    showToast("Downloaded text files (main_file.txt, calc_file.txt)!");
  });

  // Clear inputs
  $("#btn-clear").on("click", function () {
    $("#main_input").val("");
    $("#calc_input").val("");
    $("#main_file_picker").val("");
    $("#calc_file_picker").val("");
    $("#main-preview").html("");
    $("#calc-preview").html("");
    $("#results-section").fadeOut();
    $("#error-alert").fadeOut();
    showToast("Fields cleared");
  });

  // Submit calculation form
  $("#calc-form").on("submit", function (e) {
    e.preventDefault();
    $("#error-alert").fadeOut();

    const mainText = $("#main_input").val().trim();
    const calcText = $("#calc_input").val().trim();

    if (!mainText || !calcText) {
      showError("Please paste values for both Main File and Calculation File.");
      return;
    }

    const payload = {
      main_input: mainText,
      calc_input: calcText,
      stage7_main: parseInt($("#stage7_main").val(), 10) || 1,
      stage7_calc: parseInt($("#stage7_calc").val(), 10) || 1
    };

    // Show loading state
    const $btn = $("#btn-calculate");
    $btn.prop("disabled", true).html('<span class="spinner"></span> Calculating...');

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
          $("#results-section").fadeIn();
          $("html, body").animate({
            scrollTop: $("#results-section").offset().top - 40
          }, 400);
        } else {
          showError(response.error || "Calculation failed.");
        }
      },
      error: function (xhr) {
        let msg = "An error occurred while calculating.";
        if (xhr.responseJSON && xhr.responseJSON.error) {
          msg = xhr.responseJSON.error;
        }
        showError(msg);
      },
      complete: function () {
        $btn.prop("disabled", false).html(
          `<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Run 8-Stage Calculation`
        );
      }
    });
  });

  // Render results
  function renderResults(data) {
    const mv = data.main_vals;
    const cv = data.calc_vals;

    // Extracted pills
    $("#extracted-main-vals").text(`a=${mv[0]}, b=${mv[1]}, c=${mv[2]}, d=${mv[3]}, e=${mv[4]}`);
    $("#extracted-calc-vals").text(`a=${cv[0]}, b=${cv[1]}, c=${cv[2]}, d=${cv[3]}, e=${cv[4]}`);

    // Final total hero
    $("#hero-total-score").text(data.final_total);

    // Render Stage Cards
    const $grid = $("#stages-grid");
    $grid.empty();

    data.stages.forEach(function (stage) {
      const cardHtml = buildStageCard(stage);
      $grid.append(cardHtml);
    });

    // Render Stage 8 Equation
    const equationParts = data.stages.map(s => s.points).join(" + ");
    $("#stage8-equation").text(`${equationParts} = ${data.final_total} POINTS`);
  }

  function buildStageCard(s) {
    const num = s.stage;
    const name = s.name;
    const pts = s.points;
    const hasPtsClass = pts > 0 ? "has-points" : "";

    let detailsHtml = "";

    if (num === 1) {
      detailsHtml = `
        <div class="detail-row">
          <span class="detail-label">Main (a+b+c, c+d+e):</span>
          <span class="detail-val">${s.main.comb1} ${s.main.comb1_div ? '<span class="check-pill check-pass">÷3</span>' : '<span class="check-pill check-fail">✕</span>'} | ${s.main.comb2} ${s.main.comb2_div ? '<span class="check-pill check-pass">÷3</span>' : '<span class="check-pill check-fail">✕</span>'} (${s.main.points} pts)</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Calculation (a+b+c, c+d+e):</span>
          <span class="detail-val">${s.calc.comb1} ${s.calc.comb1_div ? '<span class="check-pill check-pass">÷3</span>' : '<span class="check-pill check-fail">✕</span>'} | ${s.calc.comb2} ${s.calc.comb2_div ? '<span class="check-pill check-pass">÷3</span>' : '<span class="check-pill check-fail">✕</span>'} (${s.calc.points} pts)</span>
        </div>
      `;
    } else if (num === 2) {
      detailsHtml = `
        <div class="detail-row">
          <span class="detail-label">Main Sum (${s.main.sum}):</span>
          <span class="detail-val">÷2 ${s.main.div_by_2 ? '<span class="check-pill check-pass">✓</span>' : '<span class="check-pill check-fail">✕</span>'} &nbsp; ÷3 ${s.main.div_by_3 ? '<span class="check-pill check-pass">✓</span>' : '<span class="check-pill check-fail">✕</span>'} (${s.main.points} pts)</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Calc Sum (${s.calc.sum}):</span>
          <span class="detail-val">÷2 ${s.calc.div_by_2 ? '<span class="check-pill check-pass">✓</span>' : '<span class="check-pill check-fail">✕</span>'} &nbsp; ÷3 ${s.calc.div_by_3 ? '<span class="check-pill check-pass">✓</span>' : '<span class="check-pill check-fail">✕</span>'} (${s.calc.points} pts)</span>
        </div>
      `;
    } else if (num === 3) {
      detailsHtml = `
        <div class="detail-row">
          <span class="detail-label">Main (a+c, c+e vs 5):</span>
          <span class="detail-val">${s.main["a+c"]}, ${s.main["c+e"]} → <span class="pattern-chip">${s.main.pattern}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Calc (a+c, c+e vs 5):</span>
          <span class="detail-val">${s.calc["a+c"]}, ${s.calc["c+e"]} → <span class="pattern-chip">${s.calc.pattern}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Pattern Comparison:</span>
          <span class="detail-val font-mono">${s.comparison} → <strong>${pts} pt</strong></span>
        </div>
      `;
    } else if (num === 4) {
      detailsHtml = `
        <div class="detail-row">
          <span class="detail-label">Main (a+c)+(c+e) vs 10:</span>
          <span class="detail-val">${s.main.combined} → <span class="pattern-chip">${s.main.result}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Calc (a+c)+(c+e) vs 10:</span>
          <span class="detail-val">${s.calc.combined} → <span class="pattern-chip">${s.calc.result}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Comparison:</span>
          <span class="detail-val font-mono">${s.comparison} → <strong>${pts} pt</strong></span>
        </div>
      `;
    } else if (num === 5) {
      detailsHtml = `
        <div class="detail-row">
          <span class="detail-label">Main (separate vs 10):</span>
          <span class="detail-val">${s.main["a+c"]}, ${s.main["c+e"]} → <span class="pattern-chip">${s.main.pattern}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Calc (separate vs 10):</span>
          <span class="detail-val">${s.calc["a+c"]}, ${s.calc["c+e"]} → <span class="pattern-chip">${s.calc.pattern}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Pattern Comparison:</span>
          <span class="detail-val font-mono">${s.comparison} → <strong>${pts} pt</strong></span>
        </div>
      `;
    } else if (num === 6) {
      detailsHtml = `
        <div class="detail-row">
          <span class="detail-label">P1 (${s.P1.total} → [${s.P1.digits.join(', ')}]):</span>
          <span class="detail-val"><span class="pattern-chip">${s.P1.pattern}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">P2 (${s.P2.total} → [${s.P2.digits.join(', ')}]):</span>
          <span class="detail-val"><span class="pattern-chip">${s.P2.pattern}</span></span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Comparison:</span>
          <span class="detail-val font-mono">${s.comparison} → <strong>${pts} pt</strong></span>
        </div>
      `;
    } else if (num === 7) {
      detailsHtml = `
        <div class="detail-row">
          <span class="detail-label">Main Value:</span>
          <span class="detail-val font-mono">${s.main_val}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Calculation Value:</span>
          <span class="detail-val font-mono">${s.calc_val}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Formula:</span>
          <span class="detail-val font-mono">${s.formula} → <strong>${pts} pts</strong></span>
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
    let txt = `==================================================================\n`;
    txt += `                8-STAGE CALCULATION AUDIT REPORT\n`;
    txt += `==================================================================\n`;
    txt += `Main File Extracted Values:        ${JSON.stringify(data.main_vals)}\n`;
    txt += `Calculation File Extracted Values: ${JSON.stringify(data.calc_vals)}\n`;
    txt += `------------------------------------------------------------------\n`;
    data.stages.forEach(function (s) {
      txt += `Stage ${s.stage}: ${s.name.padEnd(46)} = ${s.points} pts\n`;
    });
    txt += `------------------------------------------------------------------\n`;
    txt += `STAGE 8 -- FINAL TOTAL SCORE: ${data.final_total} POINTS\n`;
    txt += `==================================================================\n`;

    navigator.clipboard.writeText(txt).then(function () {
      showToast("Audit report copied to clipboard!");
    });
  });

  function showError(msg) {
    $("#error-alert").text(msg).fadeIn();
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
