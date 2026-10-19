from django.test import TestCase, Client
from django.urls import reverse
import json

from calculation_engine import (
    stage_1,
    stage_2,
    stage_3,
    stage_4,
    stage_5,
    stage_6,
    stage_7,
    run_all_stages,
    parse_source_lines,
    calculate_original_value_adjustment
)


class CalculationEngineComprehensiveTests(TestCase):
    """
    Automated test suite verifying the 8-stage calculation engine specification.
    """

    # 1. Stage 1 combination-divisibility points
    def test_stage_1_combination_divisibility(self):
        # Main: [3, 3, 3, 3, 3] -> S1 = 3+3+3 = 9 (%3==0), S2 = 3+3+3 = 9 (%3==0) -> 2 comb pts
        # Calc: [1, 1, 2, 1, 1] -> S1 = 1+1+2 = 4 (%3!=0), S2 = 2+1+1 = 4 (%3!=0) -> 0 comb pts
        res = stage_1([3, 3, 3, 3, 3], [1, 1, 2, 1, 1])
        self.assertEqual(res["main"]["comb_points"], 2)
        self.assertTrue(res["main"]["s1_div"])
        self.assertTrue(res["main"]["s2_div"])
        self.assertEqual(res["calc"]["comb_points"], 0)
        self.assertFalse(res["calc"]["s1_div"])
        self.assertFalse(res["calc"]["s2_div"])

    # 2. Stage 1 ratio checks: div by 2, div by 3, self/mutual matches
    def test_stage_1_ratio_checks(self):
        # Example 1: 9/7 -> no qualifying condition; 0 points
        # Main: a=3, b=3, c=3, d=1, e=3 -> S1=9, S2=7 -> 9/7
        res1 = stage_1([3, 3, 3, 1, 3], [1, 1, 2, 1, 1])
        self.assertEqual(res1["main"]["s1"], 9)
        self.assertEqual(res1["main"]["s2"], 7)
        self.assertFalse(res1["main"]["ratio_qualifies"])
        self.assertEqual(res1["main"]["ratio_points"], 0)

        # Example 2: 8/4 -> divisible by 2; qualifying condition (1 pt)
        res2 = stage_1([2, 2, 4, 0, 0], [1, 1, 2, 1, 1])
        self.assertEqual(res2["main"]["s1"], 8)
        self.assertEqual(res2["main"]["s2"], 4)
        self.assertTrue(res2["main"]["is_div_2"])
        self.assertTrue(res2["main"]["ratio_qualifies"])
        self.assertEqual(res2["main"]["ratio_points"], 1)

        # Example 3: 9/3 -> divisible by 3; qualifying condition (1 pt)
        res3 = stage_1([3, 3, 3, 0, 0], [1, 1, 2, 1, 1])
        self.assertEqual(res3["main"]["s1"], 9)
        self.assertEqual(res3["main"]["s2"], 3)
        self.assertTrue(res3["main"]["is_div_3"])
        self.assertTrue(res3["main"]["ratio_qualifies"])
        self.assertEqual(res3["main"]["ratio_points"], 1)

        # Example 4: 4/4 -> self divisible; qualifying condition (1 pt)
        res4 = stage_1([1, 1, 2, 1, 1], [1, 1, 2, 1, 1])
        self.assertEqual(res4["main"]["s1"], 4)
        self.assertEqual(res4["main"]["s2"], 4)
        self.assertTrue(res4["main"]["is_self_match"])
        self.assertTrue(res4["main"]["ratio_qualifies"])
        self.assertEqual(res4["main"]["ratio_points"], 1)

        # User Example: 21/18 -> both divisible by 3 -> 1 point!
        # [7, 5, 9, 8, 1] -> S1 = 7+5+9 = 21, S2 = 9+8+1 = 18
        res_21_18 = stage_1([7, 5, 9, 8, 1], [7, 5, 9, 8, 1])
        self.assertEqual(res_21_18["main"]["s1"], 21)
        self.assertEqual(res_21_18["main"]["s2"], 18)
        self.assertTrue(res_21_18["main"]["is_div_3"])
        self.assertTrue(res_21_18["main"]["ratio_qualifies"])
        self.assertEqual(res_21_18["main"]["ratio_points"], 1)
        # Check that it applies to calc file too!
        self.assertEqual(res_21_18["calc"]["s1"], 21)
        self.assertEqual(res_21_18["calc"]["s2"], 18)
        self.assertTrue(res_21_18["calc"]["is_div_3"])
        self.assertEqual(res_21_18["calc"]["ratio_points"], 1)

        # User Example: 2/4 -> divisible by 2 -> 1 point
        # [0, 1, 1, 1, 2] -> S1 = 0+1+1 = 2, S2 = 1+1+2 = 4
        res_2_4 = stage_1([0, 1, 1, 1, 2], [1, 1, 2, 1, 1])
        self.assertEqual(res_2_4["main"]["s1"], 2)
        self.assertEqual(res_2_4["main"]["s2"], 4)
        self.assertTrue(res_2_4["main"]["is_div_2"])
        self.assertEqual(res_2_4["main"]["ratio_points"], 1)

        # User Example: 2/2 -> self divisible -> 1 point
        # [0, 1, 1, 0, 1] -> S1 = 0+1+1 = 2, S2 = 1+0+1 = 2
        res_2_2 = stage_1([0, 1, 1, 0, 1], [1, 1, 2, 1, 1])
        self.assertTrue(res_2_2["main"]["is_self_match"])
        self.assertEqual(res_2_2["main"]["ratio_points"], 1)

        # User Example: 4/9 -> not divisible by 2 or 3 or self -> 0 points
        # [1, 2, 1, 4, 4] -> S1 = 1+2+1 = 4, S2 = 1+4+4 = 9
        res_4_9 = stage_1([1, 2, 1, 4, 4], [1, 1, 2, 1, 1])
        self.assertEqual(res_4_9["main"]["s1"], 4)
        self.assertEqual(res_4_9["main"]["s2"], 9)
        self.assertFalse(res_4_9["main"]["ratio_qualifies"])
        self.assertEqual(res_4_9["main"]["ratio_points"], 0)

        # User Example: 5/4 -> not divisible by 2 or 3 or self -> 0 points
        # [2, 2, 1, 1, 2] -> S1 = 2+2+1 = 5, S2 = 1+1+2 = 4
        res_5_4 = stage_1([2, 2, 1, 1, 2], [1, 1, 2, 1, 1])
        self.assertEqual(res_5_4["main"]["s1"], 5)
        self.assertEqual(res_5_4["main"]["s2"], 4)
        self.assertFalse(res_5_4["main"]["ratio_qualifies"])
        self.assertEqual(res_5_4["main"]["ratio_points"], 0)

        # User Example: 10/10 -> self divisible -> 1 point
        # [3, 4, 3, 3, 4] -> S1 = 3+4+3 = 10, S2 = 3+3+4 = 10
        res_10_10 = stage_1([3, 4, 3, 3, 4], [1, 1, 2, 1, 1])
        self.assertTrue(res_10_10["main"]["is_self_match"])
        self.assertEqual(res_10_10["main"]["ratio_points"], 1)

        # User Example: 9/27 -> divisible by 3 -> 1 point
        # [3, 3, 3, 12, 12] -> S1 = 3+3+3 = 9, S2 = 3+12+12 = 27
        res_9_27 = stage_1([3, 3, 3, 12, 12], [1, 1, 2, 1, 1])
        self.assertEqual(res_9_27["main"]["s1"], 9)
        self.assertEqual(res_9_27["main"]["s2"], 27)
        self.assertTrue(res_9_27["main"]["is_div_3"])
        self.assertEqual(res_9_27["main"]["ratio_points"], 1)

    # 3. Stage 1 combined subtotal
    def test_stage_1_combined_subtotal(self):
        # Main: S1=9, S2=9 (comb=2, ratio=1 -> 3 pts)
        # Calc: S1=11, S2=13 (comb=0, ratio=0 -> 0 pts)
        res = stage_1([2, 1, 6, 1, 2], [2, 1, 8, 3, 2])
        self.assertEqual(res["main"]["points"], 3)
        self.assertEqual(res["calc"]["points"], 0)
        self.assertEqual(res["points"], 3)

    # 4. Stage 2 total-sum divisibility
    def test_stage_2_total_sum_divisibility(self):
        # sum = 12 -> 12 % 2 == 0 (1), 12 % 3 == 0 (1) -> 2 pts
        # sum = 16 -> 16 % 2 == 0 (1), 16 % 3 == 1 (0) -> 1 pt
        res = stage_2([2, 1, 6, 1, 2], [2, 1, 8, 3, 2])
        self.assertEqual(res["main"]["points"], 2)
        self.assertEqual(res["calc"]["points"], 1)
        self.assertEqual(res["points"], 3)

    # 5. Stage 3 threshold-5 comparisons and pattern scoring
    def test_stage_3_threshold_5(self):
        # Main: a+c = 8 (>=5 -> '>'), c+e = 8 (>=5 -> '>') -> '>>' (Homogeneous)
        # Calc: a+c = 10 (>=5 -> '>'), c+e = 10 (>=5 -> '>') -> '>>' (Homogeneous)
        # Homogeneous vs Homogeneous -> 0 pts
        res1 = stage_3([2, 1, 6, 1, 2], [2, 1, 8, 3, 2])
        self.assertEqual(res1["points"], 0)

        # Test mixed vs homogeneous -> 1 pt
        # Main: a+c=6 ('>'), c+e=2 ('<') -> '><' (Mixed)
        # Calc: a+c=6 ('>'), c+e=6 ('>') -> '>>' (Homogeneous)
        res2 = stage_3([4, 1, 2, 1, 0], [2, 1, 4, 1, 2])
        self.assertEqual(res2["main"]["pattern"], "><")
        self.assertEqual(res2["calc"]["pattern"], ">>")
        self.assertEqual(res2["points"], 1)

    # 6. Stage 4 combined inner calculation against 10
    def test_stage_4_inner_calculation_using_10(self):
        # Same sign: both >= 10 -> 0 pts
        res1 = stage_4([2, 1, 6, 1, 2], [2, 1, 8, 3, 2])
        self.assertEqual(res1["points"], 0)

        # Different signs: Main < 10 ('<'), Calc >= 10 ('>') -> 1 pt
        res2 = stage_4([1, 1, 1, 1, 1], [3, 3, 3, 3, 3])
        self.assertEqual(res2["main"]["result"], "<")
        self.assertEqual(res2["calc"]["result"], ">")
        self.assertEqual(res2["points"], 1)

    # 7. Stage 5 individual inner calculation against 10
    def test_stage_5_individual_inner_calculation_against_10(self):
        # Main: a+c = 8 (<10 -> '<'), c+e = 8 (<10 -> '<') -> '<<' (Homogeneous)
        # Calc: a+c = 10 (>=10 -> '>'), c+e = 10 (>=10 -> '>') -> '>>' (Homogeneous)
        # Both homogeneous -> 0 pts
        res = stage_5([2, 1, 6, 1, 2], [2, 1, 8, 3, 2])
        self.assertEqual(res["points"], 0)

    # 8. Stage 6 P1/P2 digit patterns and vertical differences
    def test_stage_6_combined_p1_p2_and_vertical(self):
        # P1 = 12 -> digits [1, 2] -> '<<' (Homogeneous)
        # P2 = 16 -> digits [1, 6] -> '<>' (Mixed)
        # Pattern points: Homogeneous vs Mixed -> 1 pt
        # Vertical: first digits are 1 and 1 -> |1 - 1| = 0 pts
        # Stage 6 Total = 1 + 0 = 1 pt
        res = stage_6([2, 1, 6, 1, 2], [2, 1, 8, 3, 2])
        self.assertEqual(res["P1"]["total"], 12)
        self.assertEqual(res["P1"]["digits"], [1, 2])
        self.assertEqual(res["P1"]["pattern"], "<<")
        self.assertEqual(res["P2"]["total"], 16)
        self.assertEqual(res["P2"]["digits"], [1, 6])
        self.assertEqual(res["P2"]["pattern"], "<>")
        self.assertEqual(res["pattern_points"], 1)
        self.assertEqual(res["vertical"]["points"], 0)
        self.assertEqual(res["points"], 1)

        # User Screenshot Example: P1=20 -> [2, 0], P2=18 -> [1, 8]
        # Vertical: |2 - 1| = 1 point!
        # Pattern: '<<' vs '<>' -> 1 point
        # Stage 6 Total = 1 + 1 = 2 pts
        res_user_screen = stage_6([3, 8, 2, 3, 4], [7, 4, 2, 3, 2])
        self.assertEqual(res_user_screen["P1"]["total"], 20)
        self.assertEqual(res_user_screen["P1"]["digits"], [2, 0])
        self.assertEqual(res_user_screen["P2"]["total"], 18)
        self.assertEqual(res_user_screen["P2"]["digits"], [1, 8])
        self.assertEqual(res_user_screen["vertical"]["points"], 1)
        self.assertEqual(res_user_screen["points"], 2)

        # User Example 2: P1 digits [3, 1] vs P2 digits [1, 1] -> 3 - 1 = 2 points
        res_3_1 = stage_6([6, 6, 6, 6, 7], [2, 2, 2, 2, 3])
        self.assertEqual(res_3_1["P1"]["digits"], [3, 1])
        self.assertEqual(res_3_1["P2"]["digits"], [1, 1])
        self.assertEqual(res_3_1["vertical"]["points"], 2)

        # User Example 3: P1 digits [2, 1] vs P2 digits [2, 2] -> 2 - 2 = 0 points
        res_2_2 = stage_6([4, 4, 4, 4, 5], [4, 4, 4, 5, 5])
        self.assertEqual(res_2_2["P1"]["digits"], [2, 1])
        self.assertEqual(res_2_2["P2"]["digits"], [2, 2])
        self.assertEqual(res_2_2["vertical"]["points"], 0)

        # Test single digit padding in P1: e.g. sum = 4 -> digits [0, 4] vs P2 digits [2, 5] -> |0 - 2| = 2
        res_single = stage_6([0, 0, 1, 1, 2], [5, 5, 5, 5, 5])
        self.assertEqual(res_single["P1"]["total"], 4)
        self.assertEqual(res_single["P1"]["digits"], [0, 4])
        self.assertEqual(res_single["vertical"]["points"], 2)

    # 9. Stage 7 average divisibility by 2, including odd sums
    def test_stage_7_average_divisibility_by_2(self):
        # Even sum: P1 = 12, P2 = 16 -> Sum = 28 -> 28 % 2 == 0 -> 1 pt, avg = 14
        res_even = stage_7([2, 1, 6, 1, 2], [2, 1, 8, 3, 2])
        self.assertEqual(res_even["sum"], 28)
        self.assertTrue(res_even["div_by_2"])
        self.assertEqual(res_even["average"], 14)
        self.assertEqual(res_even["points"], 1)

        # Odd sum: P1 = 13, P2 = 14 -> Sum = 27 -> 27 % 2 == 1 -> 0 pts, avg = 13.5
        res_odd = stage_7([3, 1, 6, 1, 2], [2, 1, 7, 2, 2])
        self.assertEqual(res_odd["sum"], 27)
        self.assertFalse(res_odd["div_by_2"])
        self.assertEqual(res_odd["average"], 13.5)
        self.assertEqual(res_odd["points"], 0)

    # 10. Stage 8 final-total arithmetic & no double-counting
    def test_stage_8_final_total_arithmetic(self):
        results = run_all_stages(
            [2, 1, 6, 1, 2],
            [2, 1, 8, 3, 2],
            stage6_main_val=1,
            stage6_calc_val=1
        )
        self.assertEqual(len(results["stages"]), 7)
        expected_total = sum(s["points"] for s in results["stages"])
        self.assertEqual(results["final_total"], expected_total)
        self.assertEqual(results["final_total"], 8)
        self.assertIn("3 + 3 + 0 + 0 + 0 + 1 + 1 = 8 POINTS", results["stage8_equation"])

    # 11. Original value 0.85% adjustment calculation
    def test_original_value_085_adjustment(self):
        adj = calculate_original_value_adjustment(149.96)
        self.assertIsNotNone(adj)
        self.assertEqual(adj["original_value"], 149.96)
        self.assertEqual(adj["adjustment"], 1.27)
        self.assertEqual(adj["addition_result"], 151.23)
        self.assertEqual(adj["subtraction_result"], 148.69)
        self.assertEqual(adj["formula_add"], "149.96 + 1.27 = 151.23")
        self.assertEqual(adj["formula_sub"], "149.96 - 1.27 = 148.69")

    # 12. Input parsing, formats, normalization and validation
    def test_input_parsing_formats(self):
        # Spaced delimiter format from user: '2 _ 7   2 _ 7   2 _ 6   2 _ 3   1 _ 1'
        vals1 = parse_source_lines("2 _ 7\t2 _ 7\t2 _ 6\t2 _ 3\t1 _ 1")
        self.assertEqual(vals1, [7, 7, 6, 3, 1])

        # Standard hyphen format
        vals2 = parse_source_lines("1-2\n1-1\n2-6\n1-1\n1-2")
        self.assertEqual(vals2, [2, 1, 6, 1, 2])

        # 10 raw numbers fallback
        vals3 = parse_source_lines("2 7 2 7 2 6 2 3 1 1")
        self.assertEqual(vals3, [7, 7, 6, 3, 1])

        # Single numbers
        vals4 = parse_source_lines("7, 7, 6, 3, 1")
        self.assertEqual(vals4, [7, 7, 6, 3, 1])

        # Empty input raises ValueError
        with self.assertRaises(ValueError):
            parse_source_lines("")

        # Incomplete input (e.g. 4 values) raises ValueError
        with self.assertRaises(ValueError):
            parse_source_lines("1_2 1_3 2_1 2_1")

    # 13. REST API endpoint test (/api/calculate/)
    def test_api_calculate_endpoint(self):
        client = Client()
        url = reverse('api-calculate')

        # Successful calculation
        payload = {
            "main_input": "2 _ 7\t2 _ 7\t2 _ 6\t2 _ 3\t1 _ 1",
            "calc_input": "2 _ 9\t2 _ 5\t2 _ 5\t1 _ 1\t3 _ 9",
            "original_value": "149.96",
            "stage6_main": 1,
            "stage6_calc": 1
        }
        resp = client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["stages"]), 7)
        self.assertIn("stage8_equation", data["data"])
        self.assertIsNotNone(data["data"]["original_value_adj"])
        self.assertEqual(data["data"]["original_value_adj"]["addition_result"], 151.23)

        # Missing input raises 400
        bad_payload = {"main_input": "1_2 1_2 1_2 1_2 1_2"}
        resp_bad = client.post(url, data=json.dumps(bad_payload), content_type="application/json")
        self.assertEqual(resp_bad.status_code, 400)
