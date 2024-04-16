from django.shortcuts import render, redirect
from .forms import QueryForm
from .models import InputData
from youtube_transcript_api.formatters import TextFormatter
from deepmultilingualpunctuation import PunctuationModel
import kss
import re
from django.http import HttpResponseRedirect
from django.urls import reverse
import uuid
import json


def time_str_to_seconds(time_str):
    parts = list(map(int, time_str.split(":")))
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
    else:
        hours, minutes, seconds = 0, int(parts[0]), int(parts[1])
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds


def capitalize_sentences(text):
    sentence_pattern = r"(?:^|(?<=[.!?]))\s*(\w)"
    result = re.sub(sentence_pattern, lambda x: x.group(0).upper(), text)
    return result


def text_to_paragraphs(text, max_sentences_per_paragraph=10, max_paragraph_length=300):
    sentence_delimiters = [".", "!", "?"]
    sentences = []
    current_sentence = ""
    paragraphs = []
    current_paragraph = ""
    paragraph_length = 0

    for char in text:
        current_sentence += char
        if char in sentence_delimiters:
            sentences.append(current_sentence)
            current_sentence = ""

    if current_sentence:
        sentences.append(current_sentence)

    for sentence in sentences:
        sentence = sentence.strip()  # Remove leading/trailing whitespace and newlines
        if sentence:
            if current_paragraph:
                if (paragraph_length + len(sentence) + 1 <= max_paragraph_length) and (
                    len(current_paragraph.split(".")) < max_sentences_per_paragraph
                ):
                    current_paragraph += " "  # Add space between sentences
                    current_paragraph += sentence
                    paragraph_length += len(sentence) + 1  # +1 for the space
                else:
                    paragraphs.append(current_paragraph)
                    current_paragraph = sentence
                    paragraph_length = len(sentence)
            else:
                current_paragraph = sentence
                paragraph_length = len(sentence)

    if current_paragraph:
        paragraphs.append(current_paragraph)

    return paragraphs


def text_to_sentences(text):
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = re.split(sentence_pattern, text)
    return sentences


def query_view(request):
    if request.method == "POST":
        form = QueryForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.uid = uuid.uuid4()
            instance.transcript = form.cleaned_data.get("transcript")
            instance.save()

            return redirect("transcribe", uid=instance.uid)
    else:
        form = QueryForm()
    return render(request, "index.html", {"form": form})


def transcribe(request, uid):
    try:
        data = InputData.objects.get(uid=uid)
        formatter = TextFormatter()

        # get data from form
        url = data.youtube_url
        language = data.language
        start_time = data.start_time
        end_time = data.end_time
        transcript_json = data.transcript
        transcript = json.loads(transcript_json)

        # delete data once consumed
        data.delete()

        # get time data
        transcript_last = transcript[-1]
        max_time = transcript_last["start"] + transcript_last["duration"]
        start_time_seconds = time_str_to_seconds(start_time) if start_time != "" else 0
        end_time_seconds = time_str_to_seconds(end_time) if end_time != "" else max_time

        # clean transcript
        transcript = [
            phrase
            for phrase in transcript
            if phrase["start"] >= start_time_seconds
            and phrase["start"] <= end_time_seconds
        ]
        fs = formatter.format_transcript(transcript)
        nl = fs.replace("\n", " ")
        fs = re.sub(r"\[(.*?)\]", "", nl)
        fs = re.sub(r"\(.*?\)", "", fs)

        if language == "en":
            pm = PunctuationModel()
            fs = pm.restore_punctuation(fs)
            fs = re.sub(r"([?!~])\.", r"\1", fs)
            fs = capitalize_sentences(fs)
        elif language == "ko":
            fs = ". ".join(kss.split_sentences(fs))
            fs = re.sub(r"([?!~])\.", r"\1", fs)

        ps = text_to_paragraphs(fs)
        ss = text_to_sentences(fs)

        return render(
            request,
            "transcribe/result.html",
            {"raw": nl, "transcript": fs, "paragraphs": ps, "sentences": ss},
        )

    except Exception:
        return HttpResponseRedirect(reverse("query_view"))
