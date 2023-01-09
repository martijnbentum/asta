from texts.models import Annotation
from utils.make_dataset import Cleaner
from utils import needleman_wunch
import Levenshtein


def get_acht_etske_annotation_set(exclude_bad = True):
    a = Annotation.objects.filter(recording__area='Acht')
    a = a.filter(user__username = 'Etske')
    if exclude_bad: a = a.exclude(alignment = 'bad')
    return a

def load_ocrlines(annotations):
    recordings = []
    for x in annotations:
        recording = x.recording
        if recording not in recordings: 
            recording.align
            recordings.append(recording)
        else:
            x.recording = recordings[recordings.index(recording)]
    return annotations

def _annotation_to_line(annotation):
    line = [annotation.pk]
    line.append(annotation.recording.pk)
    transcription = annotation.ocr_line.ocr_text
    clean_transcription = Cleaner(transcription).text_clean
    line.extend([transcription,clean_transcription])
    line.append(annotation.recording.wav_filename)
    line.append(annotation.ocr_line.start_time)
    line.append(annotation.ocr_line.end_time)
    line.append(annotation.alignment)
    return line

def handle_good_alignments(annotations):
    a = get_alignment(annotations,'good')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        line = _annotation_to_line(annotation)
        output.append(line)
    return output

def handle_start_alignments(annotations, ratio_threshold = .5):
    a = get_alignment(annotations, 'start_match')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        if not annotation.corrected_transcription: continue
        add_levenshtein(annotation)
        if annotation.lratio.q4_ratio < ratio_threshold: continue
        line = _annotation_to_line(annotation)
        output.append(line)
    return output

def handle_end_alignments(annotations, ratio_threshold = .5):
    a = get_alignment(annotations, 'end_match')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        if not annotation.corrected_transcription: continue
        add_levenshtein(annotation)
        if annotation.lratio.q1_ratio < ratio_threshold: continue
        line = _annotation_to_line(annotation)
        output.append(line)
    return output

def handle_middle_alignments(annotations, ratio_threshold = .5):
    a = get_alignment(annotations, 'middle_match')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        if not annotation.corrected_transcription: continue
        add_levenshtein(annotation)
        if annotation.lratio.q1_ratio < ratio_threshold: continue
        if annotation.lratio.q4_ratio < ratio_threshold: continue
        line = _annotation_to_line(annotation)
        output.append(line)
    return output

def handle_alignments(annotations = None, ratio_threshold = .5):
    if not annotations: annotations = get_acht_etske_annotation_set()
    if not hasattr(annotations[0],'_align'):
        annotations = load_ocrlines(annotations)
    oga = handle_good_alignments(annotations)
    print(len(oga),'good alignment annotations')
    osa = handle_start_alignments(annotations,ratio_threshold)
    nstart = len(get_alignment(annotations,'start_match'))
    print(len(osa),'start alignment annotations', nstart)
    oea = handle_end_alignments(annotations,ratio_threshold)
    nend = len(get_alignment(annotations,'end_match'))
    print(len(oea),'end alignment annotations ', nend)
    oma = handle_middle_alignments(annotations,ratio_threshold)
    nmiddle = len(get_alignment(annotations,'middle_match'))
    print(len(oma),'middle alignment annotations ', nmiddle)
    output = oga + osa + oea + oma
    nall = len(oga) + nstart + nend + nmiddle
    print(len(output), 'total manually checked phrases ', nall)
    return output
    


def get_alignment(annotations, alignment):
    a = [x for x in annotations if x.alignment == alignment]
    return a

def add_needleman_wunch(a):
    a.act = needleman_wunch.nw(a.corrected_transcription, a.ocr_line.asr_text)


def add_levenshtein(a):
    a.lratio = Ratio(a)
    
class Ratio:
    def __init__(self, annotation):
        a = annotation
        if not hasattr(a,'act'):_ = add_needleman_wunch(a)
        self.align_ct, self.align_at = a.act.split('\n')
        self.nchar = len(self.align_ct)
        first_quarter_index = int(self.nchar / 4)
        half_index = int(self.nchar /2)
        last_quarter_index = self.nchar - first_quarter_index
        self.q1_ratio = self.compute_l_ratio(first_quarter_index)
        self.h1_ratio = self.compute_l_ratio(half_index)
        self.h2_ratio = self.compute_l_ratio(half_index,True)
        self.q4_ratio = self.compute_l_ratio(last_quarter_index,True)
        self.ratio = self.compute_l_ratio(self.nchar)

    def compute_l_ratio(self,index, index_start = False):
        if index_start:
            s1 = self.align_ct[index:]
            s2 = self.align_at[index:]
        else:
            s1 = self.align_ct[:index]
            s2 = self.align_at[:index]
        return round(Levenshtein.ratio(s1,s2),2)

    def __repr__(self):
        m = 'l ratio | ' +str(self.ratio)
        m += ' q1: ' +str(self.q1_ratio)
        m += ' h1: ' +str(self.h1_ratio)
        m += ' h2: ' +str(self.h2_ratio)
        m += ' q4: ' +str(self.q4_ratio)
        return m


