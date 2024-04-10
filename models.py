from django.db import models


class StoreStatus(models.Model):
    store_id = models.CharField(max_length=100)
    status = models.CharField(max_length=10) 
    timestamp_utc = models.DateTimeField()
    # active or inactive


class StoreHours(models.Model):
    store_id = models.CharField(max_length=100)
    day = models.IntegerField()  # 0=Monday, 6=Sunday
    start_time_local = models.TimeField()
    end_time_local = models.TimeField()


class StoreTimezone(models.Model):
    store_id = models.CharField(max_length=100)
    timezone_str = models.CharField(max_length=50)