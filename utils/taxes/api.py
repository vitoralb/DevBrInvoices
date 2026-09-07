from django.http import JsonResponse
from utils.taxes import load_tax_tables, get_active_table
from datetime import datetime

def api_tax_tables(request):
    """API endpoint to get all tax tables, optionally filtered by type and date"""
    tax_type = request.GET.get('tax_type')
    date_str = request.GET.get('date')
    
    if tax_type and date_str:
        try:
            reference_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            table = get_active_table(tax_type, reference_date)
            return JsonResponse(table if table else {}, safe=False)
        except ValueError:
            return JsonResponse({"error": "Invalid date format, use YYYY-MM-DD"}, status=400)
            
    tables = load_tax_tables(tax_type)
    return JsonResponse(tables, safe=False)
