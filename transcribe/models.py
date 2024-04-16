from django.db import models
import uuid


class InputData(models.Model):
    uid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=True)
    youtube_url = models.URLField()
    start_time = models.CharField(max_length=10, blank=True)
    end_time = models.CharField(max_length=10, blank=True)
    language = models.CharField(
        max_length=20,
        choices=[
            ("en_US", "English"),
            ("ko", "한국어"),
        ],
        default="English",
    )
    transcript = models.TextField(default="")
