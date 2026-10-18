import json
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from calculation_engine import run_all_stages, parse_source_lines


def index_view(request):
    """Renders the single page application dashboard."""
    return render(request, 'calculator/index.html')


def sample_data_view(request):
    """Returns the official reference sample data and Excel screenshot dataset."""
    sample_type = request.GET.get('type', 'excel')
    if sample_type == 'spec':
        main_src = "1-2\n1-1\n2-6\n1-1\n1-2"
        calc_src = "1-2\n1-1\n2-8\n1-3\n1-2"
        calc_res = run_all_stages(main_src, calc_src, stage6_main_val=1, stage6_calc_val=1)
        return JsonResponse({
            "main_source": main_src,
            "calc_source": calc_src,
            "stage6_main": 1,
            "stage6_calc": 1,
            "expected_total": calc_res["final_total"]
        })
    else:
        main_src = "1_2\n1_3\n2_1\n2_1\n3_1"
        calc_src = "2_2\n1_2\n2_2\n2_3\n2_1"
        calc_res = run_all_stages(main_src, calc_src, stage6_main_val=1, stage6_calc_val=1)
        return JsonResponse({
            "main_source": main_src,
            "calc_source": calc_src,
            "stage6_main": 1,
            "stage6_calc": 1,
            "expected_total": calc_res["final_total"]
        })


class CalculateAPIView(APIView):
    """
    REST API endpoint for 8-Stage calculation.
    Supports JSON body and multipart form data (with file uploads).
    """

    def post(self, request, *args, **kwargs):
        try:
            main_input = None
            calc_input = None

            # Handle file uploads if present
            if 'main_file' in request.FILES:
                main_input = request.FILES['main_file'].read().decode('utf-8')
            elif 'main_input' in request.data:
                main_input = request.data['main_input']

            if 'calc_file' in request.FILES:
                calc_input = request.FILES['calc_file'].read().decode('utf-8')
            elif 'calc_input' in request.data:
                calc_input = request.data['calc_input']

            if not main_input or not calc_input:
                return Response(
                    {"success": False, "error": "Both Main File and Calculation File inputs are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vertical calculation parameters in Stage 6 (optional, defaults to 1)
            raw_s6_main = request.data.get('stage6_main', request.data.get('stage7_main', 1))
            try:
                s6_main = int(raw_s6_main)
            except (ValueError, TypeError):
                s6_main = 1

            raw_s6_calc = request.data.get('stage6_calc', request.data.get('stage7_calc', 1))
            try:
                s6_calc = int(raw_s6_calc)
            except (ValueError, TypeError):
                s6_calc = 1

            orig_val = request.data.get('original_value')
            if orig_val is not None and str(orig_val).strip() != "":
                try:
                    orig_val = float(orig_val)
                except (ValueError, TypeError):
                    orig_val = None
            else:
                orig_val = None

            # Run 8-stage calculation
            result = run_all_stages(
                main_input=main_input,
                calc_input=calc_input,
                stage6_main_val=s6_main,
                stage6_calc_val=s6_calc,
                original_value=orig_val
            )

            return Response({
                "success": True,
                "data": result
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response(
                {"success": False, "error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"success": False, "error": f"Internal calculation error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
