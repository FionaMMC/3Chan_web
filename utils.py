from datetime import datetime, timedelta

def get_current_sydney_time():
    utc_time = datetime.utcnow()
    sydney_offset = timedelta(hours=11 if utc_time.month > 9 or utc_time.month < 4 else 10)
    current_time = utc_time + sydney_offset
    current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S')
    return current_time