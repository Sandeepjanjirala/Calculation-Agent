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
# STAGE 1 — Combination Divisibility by 3
# =====================================================================
def stage_1(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Combinations:
        a + b + c
        c + d + e
    Independently checked for divisibility by 3.
    0 divisible -> 0 pts
    1 divisible -> 1 pt
    2 divisible -> 2 pts
    Total = Main points + Calculation points
    """
    def score_single(vals: List[int]):
        a, b, c, d, e = vals
        c1 = a + b + c
        c2 = c + d + e
        div1 = 1 if (c1 % 3 == 0) else 0
        div2 = 1 if (c2 % 3 == 0) else 0
        return {
            "comb1": c1, "comb1_div": div1 == 1,
            "comb2": c2, "comb2_div": div2 == 1,
            "points": div1 + div2
        }

    m_res = score_single(main_vals)
    c_res = score_single(calc_vals)
    total_pts = m_res["points"] + c_res["points"]

    return {
        "stage": 1,
        "name": "Combination Divisibility by 3",
        "main": m_res,
        "calc": c_res,
        "points": total_pts
    }


# =====================================================================
# STAGE 2 — Total Sum Divisibility by 2 and 3
# =====================================================================
def stage_2(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Total sum of extracted second values.
    Independently checked for:
        divisible by 2 -> 1 pt
        divisible by 3 -> 1 pt
    Total = Main points + Calculation points
    """
    def score_single(vals: List[int]):
        s = sum(vals)
        d2 = 1 if (s % 2 == 0) else 0
        d3 = 1 if (s % 3 == 0) else 0
        return {
            "sum": s,
            "div_by_2": d2 == 1,
            "div_by_3": d3 == 1,
            "points": d2 + d3
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
    Calculates:
        a + c
        c + e
    Compares each with 5 (>= 5 -> '>', < 5 -> '<').
    Patterns are compared using Rule 13.
    """
    def get_pattern(vals: List[int]):
        a, b, c, d, e = vals
        ac = a + c
        ce = c + e
        p1 = _threshold_sign(ac, 5)
        p2 = _threshold_sign(ce, 5)
        return ac, ce, f"{p1}{p2}"

    m_ac, m_ce, m_pat = get_pattern(main_vals)
    c_ac, c_ce, c_pat = get_pattern(calc_vals)
    points = _compare_patterns(m_pat, c_pat)

    return {
        "stage": 3,
        "name": "Threshold 5 Calculation + Pattern Comparison",
        "main": {"a+c": m_ac, "c+e": m_ce, "pattern": m_pat},
        "calc": {"a+c": c_ac, "c+e": c_ce, "pattern": c_pat},
        "comparison": f"{m_pat} vs {c_pat}",
        "points": points
    }


# =====================================================================
# STAGE 4 — Inner Calculation Using 10
# =====================================================================
def stage_4(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Calculates: (a + c) + (c + e)
    Compares against 10 (>= 10 -> '>', < 10 -> '<').
    Comparison between Main and Calc:
        same sign ('> vs >' or '< vs <') -> 0 pts
        different sign                   -> 1 pt
    """
    def get_sign(vals: List[int]):
        a, b, c, d, e = vals
        combined = (a + c) + (c + e)
        sign = _threshold_sign(combined, 10)
        return combined, sign

    m_val, m_sign = get_sign(main_vals)
    c_val, c_sign = get_sign(calc_vals)
    points = 0 if m_sign == c_sign else 1

    return {
        "stage": 4,
        "name": "Inner Calculation Using 10",
        "main": {"combined": m_val, "result": m_sign},
        "calc": {"combined": c_val, "result": c_sign},
        "comparison": f"{m_sign} vs {c_sign}",
        "points": points
    }


# =====================================================================
# STAGE 5 — Individual Inner Calculation Against 10
# =====================================================================
def stage_5(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    Calculates separately:
        a + c
        c + e
    Compares each against 10 (>= 10 -> '>', < 10 -> '<').
    Patterns are compared using Rule 13.
    """
    def get_pattern(vals: List[int]):
        a, b, c, d, e = vals
        ac = a + c
        ce = c + e
        p1 = _threshold_sign(ac, 10)
        p2 = _threshold_sign(ce, 10)
        return ac, ce, f"{p1}{p2}"

    m_ac, m_ce, m_pat = get_pattern(main_vals)
    c_ac, c_ce, c_pat = get_pattern(calc_vals)
    points = _compare_patterns(m_pat, c_pat)

    return {
        "stage": 5,
        "name": "Individual Inner Calculation Against 10",
        "main": {"a+c": m_ac, "c+e": m_ce, "pattern": m_pat},
        "calc": {"a+c": c_ac, "c+e": c_ce, "pattern": c_pat},
        "comparison": f"{m_pat} vs {c_pat}",
        "points": points
    }


# =====================================================================
# STAGE 6 — P1 / P2 Digit Calculation + Pattern Comparison
# =====================================================================
def stage_6(main_vals: List[int], calc_vals: List[int]) -> Dict[str, Any]:
    """
    P1 = sum(Main)
    P2 = sum(Calc)
    If single digit, treated as 2-digit with leading zero (Rule 16).
    Each digit compared against 5 (>= 5 -> '>', < 5 -> '<').
    Patterns compared using Rule 13.
    """
    def get_digits_and_pattern(total: int):
        s = f"{total:02d}"
        digits = [int(ch) for ch in s[:2]]
        pattern = "".join(_threshold_sign(d, 5) for d in digits)
        return digits, pattern

    p1 = sum(main_vals)
    p2 = sum(calc_vals)
    p1_digits, p1_pat = get_digits_and_pattern(p1)
    p2_digits, p2_pat = get_digits_and_pattern(p2)
    points = _compare_patterns(p1_pat, p2_pat)

    return {
        "stage": 6,
        "name": "P1 / P2 Digit Calculation + Pattern Comparison",
        "P1": {"total": p1, "digits": p1_digits, "pattern": p1_pat},
        "P2": {"total": p2, "digits": p2_digits, "pattern": p2_pat},
        "comparison": f"{p1_pat} vs {p2_pat}",
        "points": points
    }


# =====================================================================
# STAGE 7 — Vertical Calculation
# =====================================================================
def stage_7(main_val: int = 1, calc_val: int = 1) -> Dict[str, Any]:
    """
    Vertical calculation (Rule 17, 18):
        points = |Main_value - Calculation_value|
    """
    diff = abs(main_val - calc_val)
    return {
        "stage": 7,
        "name": "Vertical Calculation",
        "main_val": main_val,
        "calc_val": calc_val,
        "formula": f"|{main_val} - {calc_val}|",
        "points": diff
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
# STAGE 8 — Final Total
# =====================================================================
def run_all_stages(main_input: Union[str, List[str], List[int]],
                   calc_input: Union[str, List[str], List[int]],
                   stage7_main: int = 1,
                   stage7_calc: int = 1,
                   original_value: Optional[float] = None) -> Dict[str, Any]:
    """
    Orchestrates Stages 1 through 7 and computes Stage 8 Final Score.
    Also calculates Original Value 0.85% addition and subtraction results if provided.
    """
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
    s6 = stage_6(main_vals, calc_vals)
    s7 = stage_7(stage7_main, stage7_calc)

    stages = [s1, s2, s3, s4, s5, s6, s7]
    final_total = sum(s["points"] for s in stages)
    orig_adj = calculate_original_value_adjustment(original_value)

    return {
        "main_vals": main_vals,
        "calc_vals": calc_vals,
        "stages": stages,
        "final_total": final_total,
        "original_value_adj": orig_adj
    }


def print_detailed_breakdown(res: Dict[str, Any]):
    """Pretty prints the full calculation audit report."""
    print("=" * 66)
    print("                8-STAGE CALCULATION AUDIT REPORT")
    print("=" * 66)
    mv = res["main_vals"]
    cv = res["calc_vals"]
    print(f"Main File Extracted Values:        a={mv[0]}, b={mv[1]}, c={mv[2]}, d={mv[3]}, e={mv[4]}")
    print(f"Calculation File Extracted Values: a={cv[0]}, b={cv[1]}, c={cv[2]}, d={cv[3]}, e={cv[4]}")
    print("-" * 66)

    for s in res["stages"]:
        idx = s["stage"]
        name = s["name"]
        pts = s["points"]
        print(f"Stage {idx}: {name:<46} = {pts} pts")

    print("-" * 66)
    print(f"STAGE 8 -- FINAL TOTAL SCORE: {res['final_total']} POINTS")
    print("=" * 66)


def main():
    parser = argparse.ArgumentParser(description="8-Stage Business Logic Calculator")
    parser.add_argument("--main-file", help="Path to main file")
    parser.add_argument("--calc-file", help="Path to calculation file")
    parser.add_argument("--s7-main", type=int, default=1, help="Main value for Stage 7 (default: 1)")
    parser.add_argument("--s7-calc", type=int, default=1, help="Calculation value for Stage 7 (default: 1)")
    args = parser.parse_args()

    if args.main_file and args.calc_file:
        main_vals = read_file(args.main_file)
        calc_vals = read_file(args.calc_file)
    else:
        # Use default reference test data from specification
        main_vals = ["1-2", "1-1", "2-6", "1-1", "1-2"]
        calc_vals = ["1-2", "1-1", "2-8", "1-3", "1-2"]

    results = run_all_stages(main_vals, calc_vals, stage7_main=args.s7_main, stage7_calc=args.s7_calc)
    print_detailed_breakdown(results)


if __name__ == "__main__":
    main()
