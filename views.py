from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import csv
from .models import StoreStatus, StoreHours, StoreTimezone


def parse_csv_and_load_to_db(csv_file, model):
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader) 
        for row in csv_reader:
            fields_dict = {field.name: value for field, value in zip(model._meta.fields, row)}
            model.objects.create(**fields_dict)


def calculate_uptime_downtime(start_time, end_time, interval_start, interval_end, status):
    total_uptime = total_downtime = 0
    current_time = start_time
    
    while current_time < end_time:
        next_time = current_time + timedelta(hours=1)
        if current_time < interval_end and next_time > interval_start:
            if status == 'active':
                total_uptime += 1
            else:
                total_downtime += 1
        current_time = next_time
    
    return total_uptime, total_downtime


@csrf_exempt
def trigger_report(request):
    parse_csv_and_load_to_db("store_status.csv", StoreStatus)
    parse_csv_and_load_to_db("store_hours.csv", StoreHours)
    parse_csv_and_load_to_db("store_timezone.csv", StoreTimezone)
    
    interval_end = datetime.utcnow()
    interval_start = interval_end - timedelta(weeks=1)
    report_data = []
    store_ids = set(StoreStatus.objects.values_list('store_id', flat=True))
    
    for store_id in store_ids:
        try:
            store_hours = StoreHours.objects.get(store_id=store_id)
        except StoreHours.DoesNotExist:
            store_hours = None
        
        try:
            store_timezone = StoreTimezone.objects.get(store_id=store_id)
        except StoreTimezone.DoesNotExist:
            timezone_str = 'America/Chicago'
        else:
            timezone_str = store_timezone.timezone_str
        
    
        total_uptime = total_downtime = 0
        status_records = StoreStatus.objects.filter(store_id=store_id, timestamp_utc__gte=interval_start, timestamp_utc__lt=interval_end)
        for record in status_records:
            # Convert timestamp_utc to local time
            local_time = record.timestamp_utc.astimezone(timezone_str)
            if store_hours and store_hours.start_time_local <= local_time.time() < store_hours.end_time_local:
                status = record.status
                uptime, downtime = calculate_uptime_downtime(local_time, local_time + timedelta(hours=1), interval_start, interval_end, status)
                total_uptime += uptime
                total_downtime += downtime
        
        report_data.append({
            'store_id': store_id,
            'uptime_last_hour': total_uptime,
            'uptime_last_day': total_uptime / 24,
            'uptime_last_week': total_uptime / (24 * 7),
            'downtime_last_hour': total_downtime,
            'downtime_last_day': total_downtime / 24,
            'downtime_last_week': total_downtime / (24 * 7)
        })
    
    # Return the report data
    return JsonResponse({"report_data": report_data})


def get_report(request):
    # Check if report generation status and return the report CSV file
    report_id = request.GET.get('report_id')
    csv_data = "store_id, uptime_last_hour(in minutes), uptime_last_day(in hours), update_last_week(in hours), downtime_last_hour(in minutes), downtime_last_day(in hours), downtime_last_week(in hours)\n"
    # Assuming report_data is available
    for entry in report_data:
        csv_data += f"{entry['store_id']},{entry['uptime_last_hour']},{entry['uptime_last_day']},{entry['uptime_last_week']},{entry['downtime_last_hour']},{entry['downtime_last_day']},{entry['downtime_last_week']}\n"
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'
    return response