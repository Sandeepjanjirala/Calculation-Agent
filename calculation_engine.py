"""
Calculation Engine implementing the 8-Stage Business Logic Specification.

Features:
- Full extraction using the Second-Value Rule (A-B -> B)
- Stages 1 to 7 independent scoring
- Stage 8 final aggregation
- File reading support & CLI interface
"""

import argparse
from typing import List, Dict, Any, Union, Optional


import re

def parse_source_lines(lines_or_text: Union[str, List[str]]) -> List[int]:
    """
    Extracts the second values from any Excel copy-paste format:
    - Underscore: 1_2 or 1 _ 2 -> 2
    - Hyphen: 1-2 or 1 - 2 -> 2
    - Slash: 1/2 or 1 / 2 -> 2
    - Colon/Pipe: 1:2 or 1 | 2 -> 2
    - Separated by tabs, spaces, newlines, commas, or semicolons
    - Single numbers: 2 -> 2
    - 10 raw numbers (5 pairs of A B): takes 2nd value of each pair
    """
    if isinstance(lines_or_text, list):
        text = " ".join(str(x) for x in lines_or_text)
    else:
        text = str(lines_or_text)

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Input text is empty.")

    # 1. Normalize explicit pairs with spaces around delimiter (e.g., "2 _ 7" -> "2_7")
    cleaned = re.sub(r'(\d+)\s*[_\-\/\:\|]\s*(\d+)', r'\1_\2', cleaned)

    # 2. Split by any whitespace (tabs, newlines, spaces) or commas/semicolons
    tokens = re.split(r'[\s,;]+', cleaned)
    tokens = [t.strip('"\'') for t in tokens if t.strip('"\'')]

    extracted: List[int] = []
    for token in tokens:
        # Match normalized A_B
        match = re.search(r'^\d+[_\-\/\:\|](\d+)$', token)
        if match:
            extracted.append(int(match.group(1)))
        elif token.isdigit():
            extracted.append(int(token))
        else:
            sub_parts = re.split(r'[_\-\/\:\|]', token)
            if len(sub_parts) >= 2 and sub_parts[1].isdigit():
                extracted.append(int(sub_parts[1]))

    # Fallback/Future-proofing: If 10 raw numbers were extracted (e.g., 5 pairs of A B like "2 7 2 7 2 6 2 3 1 1")
    if len(extracted) == 10:
        extracted = [extracted[i] for i in range(1, 10, 2)]

    if len(extracted) != 5:
        raise ValueError(
            f"Expected exactly 5 values (a, b, c, d, e), but found {len(extracted)}: {extracted}. "
            f"Please check your Excel copied values."
        )

    return extracted


def read_file(filepath: str) -> List[int]:
    """Reads a file from disk and parses 5 second-values."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_source_lines(content)


# =====================================================================
# STAGE 1 — Combination Divisibility by 3 + Ratio Divisibility
# =====================================================================
def stage_1(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Stage 1 — Combination Divisibility by 3 + Ratio Divisibility

    A. Combinations:
        S1 = a + b + c
        S2 = c + d + e
        Independently checked for divisibility by 3 (S1 % 3 == 0 -> 1 pt; S2 % 3 == 0 -> 1 pt).
        Combination points = S1 points + S2 points.

    B. Ratio calculation:
        S1 / S2 = (a + b + c) / (c + d + e)
        Checked for 3 qualifying conditions:
        1. Divisible by 2: (S2 != 0 and S1 % S2 == 0 and (S1 // S2) % 2 == 0)
        2. Divisible by 3: (S2 != 0 and S1 % S2 == 0 and (S1 // S2) % 3 == 0)
        3. Self/mutual match: (S2 != 0 and S1 == S2)
        Award 1 point if at least one condition is satisfied; otherwise 0 points.

    C. Total:
        Main Stage 1 = Main combination points + Main ratio points
        Calculation Stage 1 = Calculation combination points + Calculation ratio points
        Stage 1 Total = Main Stage 1 + Calculation Stage 1
    """
    def score_single(vals: List[int]):
        a, b, c, d, e = vals
        s1 = a + b + c
        s2 = c + d + e

        s1_div = (s1 % 3 == 0)
        s1_rem = s1 % 3
        s1_pts = 1 if s1_div else 0

        s2_div = (s2 % 3 == 0)
        s2_rem = s2 % 3
        s2_pts = 1 if s2_div else 0

        comb_pts = s1_pts + s2_pts

        # Ratio checks
        is_self_match = (s2 != 0 and s1 == s2)
        is_int_div = (s2 != 0 and s1 % s2 == 0)
        q = (s1 // s2) if is_int_div else None
        is_div_2 = (q is not None and q % 2 == 0)
        is_div_3 = (q is not None and q % 3 == 0)

        ratio_qualifies = is_self_match or is_div_2 or is_div_3
        ratio_pts = 1 if ratio_qualifies else 0

        ratio_reasons = []
        if is_self_match:
            ratio_reasons.append(f"Self/mutual match ({s1} = {s2})")
        if is_div_2:
            ratio_reasons.append(f"Quotient {q} % 2 = 0 (Divisible by 2)")
        if is_div_3:
            ratio_reasons.append(f"Quotient {q} % 3 = 0 (Divisible by 3)")

        if s2 == 0:
            ratio_audit = f"Ratio = {s1}/0 → Undefined (division by zero) ✗ (+0 points)"
        elif ratio_qualifies:
            q_str = f" = {q}" if q is not None else ""
            ratio_audit = f"Ratio = {s1}/{s2}{q_str} → {', '.join(ratio_reasons)} ✓ (+1 point)"
        else:
            q_str = f" = {q}" if q is not None else ""
            ratio_audit = f"Ratio = {s1}/{s2}{q_str} → Divisibility/self-match checks → No match ✗ (+0 points)"

        file_pts = comb_pts + ratio_pts

        return {
            "vals": vals,
            "s1": s1,
            "s1_formula": f"a+b+c = {a} + {b} + {c} = {s1}",
            "s1_div": s1_div,
            "s1_rem": s1_rem,
            "s1_pts": s1_pts,
            "s1_audit": f"a+b+c = {s1} → {s1} % 3 = {s1_rem} → {'Divisible by 3 ✓ (+1 point)' if s1_div else 'Not divisible by 3 ✗ (+0 points)'}",
            "s2": s2,
            "s2_formula": f"c+d+e = {c} + {d} + {e} = {s2}",
            "s2_div": s2_div,
            "s2_rem": s2_rem,
            "s2_pts": s2_pts,
            "s2_audit": f"c+d+e = {s2} → {s2} % 3 = {s2_rem} → {'Divisible by 3 ✓ (+1 point)' if s2_div else 'Not divisible by 3 ✗ (+0 points)'}",
            "comb_points": comb_pts,
            "comb1": s1,
            "comb1_div": s1_div,
            "comb2": s2,
            "comb2_div": s2_div,
            "ratio_str": f"{s1}/{s2}" if s2 != 0 else f"{s1}/0",
            "quotient": q,
            "is_self_match": is_self_match,
            "is_div_2": is_div_2,
            "is_div_3": is_div_3,
            "ratio_qualifies": ratio_qualifies,
            "ratio_reasons": ratio_reasons,
            "ratio_audit": ratio_audit,
            "ratio_points": ratio_pts,
            "points": file_pts
        }

    m_res = score_single(main_vals)
    c_res = score_single(calc_vals)
    total_pts = m_res["points"] + c_res["points"]

    return {
        "stage": 1,
        "name": "Combination Divisibility by 3 + Ratio Divisibility",
        "main": m_res,
        "calc": c_res,
        "points": total_pts
    }


# =====================================================================
# STAGE 2 — Total Sum Divisibility by 2 and 3
# =====================================================================
def stage_2(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Stage 2 — Total Sum Divisibility by 2 and 3
    Independently checked for:
        divisible by 2 -> 1 pt
        divisible by 3 -> 1 pt
    Total = Main points + Calculation points
    """
    def score_single(vals: List[int]):
        s = sum(vals)
        d2 = (s % 2 == 0)
        d3 = (s % 3 == 0)
        d2_rem = s % 2
        d3_rem = s % 3
        d2_pts = 1 if d2 else 0
        d3_pts = 1 if d3 else 0
        pts = d2_pts + d3_pts

        return {
            "vals": vals,
            "sum": s,
            "sum_formula": f"{' + '.join(str(x) for x in vals)} = {s}",
            "div_by_2": d2,
            "div_by_2_rem": d2_rem,
            "div_by_2_pts": d2_pts,
            "div_by_2_audit": f"{s} % 2 = {d2_rem} → {'Divisible by 2 ✓ (+1 point)' if d2 else 'Not divisible by 2 ✗ (+0 points)'}",
            "div_by_3": d3,
            "div_by_3_rem": d3_rem,
            "div_by_3_pts": d3_pts,
            "div_by_3_audit": f"{s} % 3 = {d3_rem} → {'Divisible by 3 ✓ (+1 point)' if d3 else 'Not divisible by 3 ✗ (+0 points)'}",
            "points": pts
        }

    m_res = score_single(main_vals)
    c_res = score_single(calc_vals)
    total_pts = m_res["points"] + c_res["points"]

    return {
        "stage": 2,
        "name": "Total Sum Divisibility by 2 and 3",
        "main": m_res,
        "calc": c_res,
        "points": total_pts
    }


# =====================================================================
# Helper comparison & pattern functions
# =====================================================================
def _threshold_sign(val: int, threshold: int) -> str:
    """
    Rule 7:
    value < threshold  -> '<'
    value >= threshold -> '>'
    """
    return ">" if val >= threshold else "<"


def _is_mixed(pattern: str) -> bool:
    """
    Rule 11 & Rule 12:
    Homogeneous: '>>', '<<'
    Mixed:       '><', '<>'
    """
    return pattern in ("><", "<>")


def _compare_patterns(p1: str, p2: str) -> int:
    """
    Rule 13:
    homogeneous + homogeneous -> 0
    mixed + mixed             -> 0
    homogeneous + mixed       -> 1
    mixed + homogeneous       -> 1
    """
    return 1 if _is_mixed(p1) != _is_mixed(p2) else 0


# =====================================================================
# STAGE 3 — Threshold 5 Calculation + Pattern Comparison
# =====================================================================
def stage_3(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Stage 3 — Threshold 5 Calculation + Pattern Comparison
    Calculates:
        a + c
        c + e
    Compares each with 5 (>= 5 -> '>', < 5 -> '<').
    Patterns are compared using Rule 13 (homogeneous vs mixed).
    """
    def get_pattern(vals: List[int]):
        a, b, c, d, e = vals
        ac = a + c
        ce = c + e
        p1 = _threshold_sign(ac, 5)
        p2 = _threshold_sign(ce, 5)
        pat = f"{p1}{p2}"
        is_mix = _is_mixed(pat)
        pat_type = "Mixed" if is_mix else "Homogeneous"
        return {
            "vals": vals,
            "a": a, "c": c, "e": e,
            "a+c": ac,
            "ac_formula": f"a+c = {a} + {c} = {ac}",
            "ac_threshold": f"{ac} {'>=' if ac >= 5 else '<'} 5 → '{p1}'",
            "c+e": ce,
            "ce_formula": f"c+e = {c} + {e} = {ce}",
            "ce_threshold": f"{ce} {'>=' if ce >= 5 else '<'} 5 → '{p2}'",
            "p1": p1,
            "p2": p2,
            "pattern": pat,
            "is_mixed": is_mix,
            "pattern_type": pat_type
        }

    m_res = get_pattern(main_vals)
    c_res = get_pattern(calc_vals)
    points = _compare_patterns(m_res["pattern"], c_res["pattern"])

    return {
        "stage": 3,
        "name": "Threshold 5 Calculation + Pattern Comparison",
        "main": m_res,
        "calc": c_res,
        "comparison": f"'{m_res['pattern']}' ({m_res['pattern_type']}) vs '{c_res['pattern']}' ({c_res['pattern_type']})",
        "comparison_result": "Different pattern types (Homogeneous vs Mixed) ✓" if points == 1 else "Same pattern type (Both Homogeneous or Both Mixed) ✗",
        "points": points
    }


# =====================================================================
# STAGE 4 — Inner Calculation Using 10
# =====================================================================
def stage_4(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Stage 4 — Inner Calculation Using 10
    Calculates: (a + c) + (c + e)
    Compares against 10 (>= 10 -> '>', < 10 -> '<').
    Comparison between Main and Calc:
        same sign ('> vs >' or '< vs <') -> 0 pts
        different sign                   -> 1 pt
    """
    def get_sign(vals: List[int]):
        a, b, c, d, e = vals
        ac = a + c
        ce = c + e
        combined = ac + ce
        sign = _threshold_sign(combined, 10)
        return {
            "vals": vals,
            "a": a, "b": b, "c": c, "d": d, "e": e,
            "a+c": ac,
            "c+e": ce,
            "combined": combined,
            "formula": f"({a}+{c}) + ({c}+{e}) = {ac} + {ce} = {combined}",
            "threshold": f"{combined} {'>=' if combined >= 10 else '<'} 10 → '{sign}'",
            "result": sign
        }

    m_res = get_sign(main_vals)
    c_res = get_sign(calc_vals)
    points = 0 if m_res["result"] == c_res["result"] else 1

    return {
        "stage": 4,
        "name": "Inner Calculation Using 10",
        "main": m_res,
        "calc": c_res,
        "comparison": f"'{m_res['result']}' vs '{c_res['result']}'",
        "comparison_result": "Different signs ✓" if points == 1 else "Same sign ✗",
        "points": points
    }


# =====================================================================
# STAGE 5 — Individual Inner Calculation Against 10
# =====================================================================
def stage_5(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Stage 5 — Individual Inner Calculation Against 10
    Calculates separately:
        a + c
        c + e
    Compares each against 10 (>= 10 -> '>', < 10 -> '<').
    Patterns are compared using Rule 13 (homogeneous vs mixed).
    """
    def get_pattern(vals: List[int]):
        a, b, c, d, e = vals
        ac = a + c
        ce = c + e
        p1 = _threshold_sign(ac, 10)
        p2 = _threshold_sign(ce, 10)
        pat = f"{p1}{p2}"
        is_mix = _is_mixed(pat)
        pat_type = "Mixed" if is_mix else "Homogeneous"
        return {
            "vals": vals,
            "a": a, "c": c, "e": e,
            "a+c": ac,
            "ac_formula": f"a+c = {a} + {c} = {ac}",
            "ac_threshold": f"{ac} {'>=' if ac >= 10 else '<'} 10 → '{p1}'",
            "c+e": ce,
            "ce_formula": f"c+e = {c} + {e} = {ce}",
            "ce_threshold": f"{ce} {'>=' if ce >= 10 else '<'} 10 → '{p2}'",
            "p1": p1,
            "p2": p2,
            "pattern": pat,
            "is_mixed": is_mix,
            "pattern_type": pat_type
        }

    m_res = get_pattern(main_vals)
    c_res = get_pattern(calc_vals)
    points = _compare_patterns(m_res["pattern"], c_res["pattern"])

    return {
        "stage": 5,
        "name": "Individual Inner Calculation Against 10",
        "main": m_res,
        "calc": c_res,
        "comparison": f"'{m_res['pattern']}' ({m_res['pattern_type']}) vs '{c_res['pattern']}' ({c_res['pattern_type']})",
        "comparison_result": "Different pattern types (Homogeneous vs Mixed) ✓" if points == 1 else "Same pattern type (Both Homogeneous or Both Mixed) ✗",
        "points": points
    }


# =====================================================================
# STAGE 6 — P1/P2 Digit Calculation + Pattern Comparison + Vertical Calculation
# =====================================================================
def stage_6(main_vals: List[int], calc_vals: List[int], main_val: int = 1, calc_val: int = 1) -> Dict[str, Any]:
    """
    Stage 6 — P1/P2 Digit Calculation + Pattern Comparison + Vertical Calculation
    Part A & B:
        P1 = sum(Main File second values)
        P2 = sum(Calculation File second values)
        If single digit, treated as 2-digit with leading zero (e.g. 7 -> '07').
        Each digit compared against 5 (>= 5 -> '>', < 5 -> '<').
        Patterns compared using Rule 13 (homogeneous vs mixed) -> 1 or 0 pt.
    Part C:
        Vertical calculation: |Main value - Calculation value|
    Part D:
        Stage 6 Total = Pattern points + Vertical points
    """
    def get_digits_and_pattern(total: int, vals: List[int]):
        s = f"{total:02d}"
        digits = [int(ch) for ch in s[:2]]
        d1, d2 = digits[0], digits[1]
        sign1 = _threshold_sign(d1, 5)
        sign2 = _threshold_sign(d2, 5)
        pattern = f"{sign1}{sign2}"
        is_mix = _is_mixed(pattern)
        pat_type = "Mixed" if is_mix else "Homogeneous"
        return {
            "total": total,
            "sum_formula": f"{' + '.join(str(x) for x in vals)} = {total}",
            "digits": digits,
            "d1": d1,
            "d2": d2,
            "d1_threshold": f"{d1} {'>=' if d1 >= 5 else '<'} 5 → '{sign1}'",
            "d2_threshold": f"{d2} {'>=' if d2 >= 5 else '<'} 5 → '{sign2}'",
            "pattern": pattern,
            "is_mixed": is_mix,
            "pattern_type": pat_type
        }

    p1 = sum(main_vals)
    p2 = sum(calc_vals)
    p1_info = get_digits_and_pattern(p1, main_vals)
    p2_info = get_digits_and_pattern(p2, calc_vals)
    pattern_points = _compare_patterns(p1_info["pattern"], p2_info["pattern"])

    # Part C: Vertical calculation
    diff = abs(main_val - calc_val)
    vertical_res = {
        "main_val": main_val,
        "calc_val": calc_val,
        "formula": f"|{main_val} - {calc_val}| = {diff}",
        "points": diff
    }

    # Part D: Subtotal
    subtotal = pattern_points + diff

    return {
        "stage": 6,
        "name": "P1/P2 Digit Calculation + Pattern Comparison + Vertical Calculation",
        "P1": p1_info,
        "P2": p2_info,
        "pattern_comparison": f"'{p1_info['pattern']}' ({p1_info['pattern_type']}) vs '{p2_info['pattern']}' ({p2_info['pattern_type']})",
        "pattern_comparison_result": "Different pattern types (Homogeneous vs Mixed) ✓ (+1 point)" if pattern_points == 1 else "Same pattern type (Both Homogeneous or Both Mixed) ✗ (+0 points)",
        "pattern_points": pattern_points,
        "vertical": vertical_res,
        "subtotal_formula": f"{pattern_points} (Pattern) + {diff} (Vertical) = {subtotal} pts",
        "points": subtotal
    }


# =====================================================================
# STAGE 7 — P1/P2 Average Divisibility by 2
# =====================================================================
def stage_7(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Stage 7 — P1/P2 Average Divisibility by 2
    Uses P1 and P2 totals from Stage 6:
        P1 = sum(Main)
        P2 = sum(Calc)
        Sum = P1 + P2
        If Sum % 2 == 0:
            Average = Sum // 2
            Award 1 point.
        Else:
            Not divisible by 2 (Odd sum, non-integer average).
            Award 0 points.
    """
    p1 = sum(main_vals)
    p2 = sum(calc_vals)
    p_sum = p1 + p2
    div_by_2 = (p_sum % 2 == 0)
    pts = 1 if div_by_2 else 0

    if div_by_2:
        avg = p_sum // 2
        avg_display = str(avg)
        audit_str = f"({p1} + {p2}) = {p_sum} → {p_sum} % 2 = 0 → Divisible by 2 ✓ → Average = {avg} → +1 point"
        status_text = "Divisible by 2 ✓"
    else:
        avg = p_sum / 2
        avg_display = f"{avg:.1f} (non-integer)"
        audit_str = f"({p1} + {p2}) = {p_sum} → {p_sum} % 2 = 1 → Not divisible by 2 (Odd sum, non-integer average: {avg:.1f}) ✗ → +0 points"
        status_text = "Not divisible by 2 (Odd sum) ✗"

    return {
        "stage": 7,
        "name": "P1/P2 Average Divisibility by 2",
        "P1": p1,
        "P2": p2,
        "sum": p_sum,
        "sum_formula": f"({p1} + {p2}) = {p_sum}",
        "div_by_2": div_by_2,
        "remainder": p_sum % 2,
        "average": avg,
        "average_display": avg_display,
        "status_text": status_text,
        "audit_str": audit_str,
        "points": pts
    }


def calculate_original_value_adjustment(val: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    Calculates 0.85% adjustment for an original value:
    Step 1 — Calculate 0.85% of value and round to 2 decimal places: round(val * 0.85%, 2)
    Step 2 — Addition Result = round(val + adjustment, 2)
    Step 3 — Subtraction Result = round(val - adjustment, 2)
    """
    if val is None:
        return None
    try:
        val = float(val)
    except (ValueError, TypeError):
        return None

    adjustment = round(val * 0.0085, 2)
    addition_result = round(val + adjustment, 2)
    subtraction_result = round(val - adjustment, 2)

    return {
        "original_value": val,
        "percentage": 0.85,
        "adjustment": adjustment,
        "addition_result": addition_result,
        "subtraction_result": subtraction_result,
        "formula_add": f"{val} + {adjustment} = {addition_result:.2f}",
        "formula_sub": f"{val} - {adjustment} = {subtraction_result:.2f}"
    }


# =====================================================================
# STAGE 8 — Final Total Equation
# =====================================================================
def run_all_stages(main_input: Union[str, List[str], List[int]],
                   calc_input: Union[str, List[str], List[int]],
                   stage6_main_val: int = 1,
                   stage6_calc_val: int = 1,
                   original_value: Optional[float] = None,
                   stage7_main: Optional[int] = None,
                   stage7_calc: Optional[int] = None) -> Dict[str, Any]:
    """
    Orchestrates Stages 1 through 7 and computes Stage 8 Final Total Equation.
    Also calculates Original Value 0.85% addition and subtraction results if provided.
    
    Supports stage7_main and stage7_calc arguments for backward compatibility
    (which map to the vertical calculation in Stage 6).
    """
    # Backward compatibility mapping for vertical calculation parameters
    v_main = stage7_main if stage7_main is not None else stage6_main_val
    v_calc = stage7_calc if stage7_calc is not None else stage6_calc_val

    if isinstance(main_input, (str, list)) and len(main_input) > 0 and isinstance(main_input[0], str):
        main_vals = parse_source_lines(main_input)
    else:
        main_vals = [int(x) for x in main_input]

    if isinstance(calc_input, (str, list)) and len(calc_input) > 0 and isinstance(calc_input[0], str):
        calc_vals = parse_source_lines(calc_input)
    else:
        calc_vals = [int(x) for x in calc_input]

    s1 = stage_1(main_vals, calc_vals)
    s2 = stage_2(main_vals, calc_vals)
    s3 = stage_3(main_vals, calc_vals)
    s4 = stage_4(main_vals, calc_vals)
    s5 = stage_5(main_vals, calc_vals)
    s6 = stage_6(main_vals, calc_vals, main_val=v_main, calc_val=v_calc)
    s7 = stage_7(main_vals, calc_vals)

    stages = [s1, s2, s3, s4, s5, s6, s7]
    final_total = sum(s["points"] for s in stages)
    orig_adj = calculate_original_value_adjustment(original_value)

    # Stage 8 Equation string
    stage8_equation = " + ".join(str(s["points"]) for s in stages) + f" = {final_total} POINTS"

    return {
        "main_vals": main_vals,
        "calc_vals": calc_vals,
        "stages": stages,
        "final_total": final_total,
        "stage8_equation": stage8_equation,
        "original_value_adj": orig_adj
    }


def print_detailed_breakdown(res: Dict[str, Any]):
    """Pretty prints the full calculation audit report."""
    print("=" * 72)
    print("                     CALCULATION AUDIT REPORT")
    print("=" * 72)
    mv = res["main_vals"]
    cv = res["calc_vals"]
    print(f"Main File Extracted Values:        a={mv[0]}, b={mv[1]}, c={mv[2]}, d={mv[3]}, e={mv[4]}")
    print(f"Calculation File Extracted Values: a={cv[0]}, b={cv[1]}, c={cv[2]}, d={cv[3]}, e={cv[4]}")
    print("-" * 72)

    for s in res["stages"]:
        idx = s["stage"]
        name = s["name"]
        pts = s["points"]
        print(f"Stage {idx}: {name:<54} = {pts} pts")

    print("-" * 72)
    print(f"STAGE 8 -- FINAL TOTAL EQUATION: {res['stage8_equation']}")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Calculation Engine (8 Stages)")
    parser.add_argument("--main-file", help="Path to main file")
    parser.add_argument("--calc-file", help="Path to calculation file")
    parser.add_argument("--s6-main", "--s7-main", dest="s6_main", type=int, default=1, help="Main value for vertical calculation (default: 1)")
    parser.add_argument("--s6-calc", "--s7-calc", dest="s6_calc", type=int, default=1, help="Calculation value for vertical calculation (default: 1)")
    parser.add_argument("--orig-val", type=float, default=None, help="Original value for 0.85% adjustment")
    args = parser.parse_args()

    if args.main_file and args.calc_file:
        main_vals = read_file(args.main_file)
        calc_vals = read_file(args.calc_file)
    else:
        # Use default reference test data from specification
        main_vals = ["1-2", "1-1", "2-6", "1-1", "1-2"]
        calc_vals = ["1-2", "1-1", "2-8", "1-3", "1-2"]

    results = run_all_stages(main_vals, calc_vals, stage6_main_val=args.s6_main, stage6_calc_val=args.s6_calc, original_value=args.orig_val)
    print_detailed_breakdown(results)


if __name__ == "__main__":
    main()

