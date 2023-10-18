from django.db import models
import uuid


class InputData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    youtube_url = models.URLField()
    start_time = models.CharField(max_length=10, blank=True)
    end_time = models.CharField(max_length=10, blank=True)
    language = models.CharField(
        max_length=20,
        choices=[
            ("en", "English"),
            ("ko", "한국어"),
        ],
        default="English",
    )
