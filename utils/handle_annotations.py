from texts.models import Annotation
from utils.make_dataset import Cleaner


def get_acht_etske_annotation_set():
    a = Annotation.objects.filter(recording__area='Acht')
    a = a.filter(user__username = 'Etske')
    return a


def handle_good_alignments(annotations):
    a = annotations.filter(alignment = 'good')
    output = []
    for annotation in a:
        line = [annotation.pk]
        line.append(annotation.recording.pk)
        transcription = annotation.ocr_line.ocr_text
        clean_transcription = Cleaner(transcription).text_clean
        line.extend([transcription,clean_transcription])
        line.append(annotation.recording.wav_filename)
        line.append(annotation.ocr_line.start_time)
        line.append(annotation.ocr_line.end_time)
        line.append(annotation.alignment)
        output.append(line)
    return output


