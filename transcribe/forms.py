from django import forms
from .models import InputData
from django.forms import URLInput, TextInput
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
)
from urllib.parse import urlparse, parse_qs
from django.core.validators import RegexValidator
import json


def time_str_to_seconds(time_str):
    parts = list(map(int, time_str.split(":")))
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
    else:
        hours, minutes, seconds = 0, int(parts[0]), int(parts[1])
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds


class QueryForm(forms.ModelForm):
    class Meta:
        model = InputData
        fields = ("youtube_url", "language", "start_time", "end_time")
        widgets = {
            "youtube_url": URLInput(
                attrs={
                    "class": "input",
                    "placeholder": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                }
            ),
        }

    start_time = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex="^(?:(?:\d:)?\d{1,2}:)\d{2}$",
                message="Enter valid timestamps (e.g., 00:00).",
                code="invalid_time",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "00:00",
            }
        ),
    )

    end_time = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex="^(?:(?:\d:)?\d{1,2}:)\d{2}$",
                message="Enter valid timestamps (e.g., 00:00).",
                code="invalid_time",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "00:00",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get("youtube_url")
        language = cleaned_data.get("language")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if url is not None and "youtu.be" not in url and "youtube.com" not in url:
            self.add_error(
                "youtube_url",
                forms.ValidationError(
                    "Enter a valid YouTube URL.",
                    code="invalid_link",
                ),
            )
            return cleaned_data

        try:
            parsed_url = urlparse(url)
            video_id = ""
            if "youtu.be" in url:
                path_segments = parsed_url.path.split("/")
                video_id = path_segments[-1]
            else:
                parsed_dict = parse_qs(parsed_url.query)
                video_id = parsed_dict["v"][0]
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=[language]
            )

            transcript_json = json.dumps(transcript)
            cleaned_data["transcript"] = transcript_json
        except KeyError:
            self.add_error(
                "youtube_url",
                forms.ValidationError(
                    "Enter a valid YouTube URL.",
                    code="invalid_link",
                ),
            )
        except NoTranscriptFound:
            lang = ""
            if language == "ko":
                lang = "한국어"
            elif language == "en_US":
                lang = "English"
            self.add_error(
                "youtube_url",
                forms.ValidationError(
                    f"No {lang} transcript is available for this YouTube video.",
                    code="invalid_link",
                ),
            )
        except TranscriptsDisabled:
            self.add_error(
                "youtube_url",
                forms.ValidationError(
                    "Transcripts are disabled for this YouTube video.",
                    code="invalid_link",
                ),
            )
        except Exception:
            pass

        try:
            transcript_last = transcript[-1]
            max_time = transcript_last["start"] + transcript_last["duration"]
            start_time_seconds = (
                time_str_to_seconds(start_time) if start_time != "" else 0
            )
            end_time_seconds = (
                time_str_to_seconds(end_time) if end_time != "" else max_time
            )
            if start_time_seconds > max_time or end_time_seconds > max_time:
                self.add_error(
                    "start_time",
                    forms.ValidationError(
                        "Enter a valid time range.",
                        code="invalid_time",
                    ),
                )
            elif start_time_seconds > end_time_seconds:
                self.add_error(
                    "start_time",
                    forms.ValidationError(
                        "Start time cannot be greater than end time.",
                        code="invalid_time",
                    ),
                )

        except Exception:
            pass

        return cleaned_data
