from texts.models import Annotation
from utils.make_dataset import Cleaner
from utils import needleman_wunch
import Levenshtein
import pickle

def make_data_etske_acht(filename='../etske_acht.pkl', save = False):
    a = get_acht_etske_annotation_set()
    o = handle_alignments(a)
    if save:
        with open(filename,'wb') as fout:
            pickle.dump(o,fout)
    return o


class Data:
    '''object to contain data lines.
    datalines contain data for creating a dataset for wav2vec training
    this route used for annotated data
    input is a filename to a pickled list made with handle_annotations
    each line should be a list created with _annotation_to_line
    '''
    def __init__(self,filename = '../etske_acht.pkl'):
        self.filename = filename
        with open(filename,'rb') as fin:
            self.raw = pickle.load(fin)
        self.data = [DataLine(*x) for x in self.raw]
        self.nlines = len(self.data)
        self.duration = sum([x.duration for x in self.data])

    def __repr__(self):
        m = 'Data: ' + str(self.nlines)
        m += ' dur: ' + str(round(self.duration / 3600,1)) + ' hours'
        return m
        
class DataLine:
    '''contains annotation data for a single line of the ocr_transcription.
    input *line should be a list created with _annotation_to_line
    '''
    def __init__(self,annotation_pk, recording_pk, ocr_transcription,
        corrected_transcription, wav_filename, start_time, end_time,
        alignment):
        self.annotation_pk = annotation_pk
        self.recording_pk = recording_pk
        self.ocr_transcription = ocr_transcription
        self.corrected_transcription = corrected_transcription
        self.wav_filename = wav_filename
        self.start_time = start_time
        self.end_time = end_time
        self.alignment = alignment
        self.duration = self.end_time - self.start_time
        
    def __repr__(self):
        if self.corrected_transcription:
            t = self.corrected_transcription
        else: t = self.ocr_transcription
        if len(t) > 63: t = t[:60] + '...'
        m = 'Line: ' +str(self.annotation_pk) 
        m += ' ' + t.ljust(64)+ ' ' + self.alignment
        return m


def get_acht_etske_annotation_set(exclude_bad = True):
    '''gets all annotations from area 'Acht'.'''
    a = Annotation.objects.filter(recording__area='Acht')
    a = a.filter(user__username = 'Etske')
    if exclude_bad: a = a.exclude(alignment = 'bad')
    return a

def load_ocrlines(annotations):
    '''preloads Align objects on recordings to prevend multiple loadings.
    '''
    recordings = []
    for x in annotations:
        recording = x.recording
        if recording not in recordings: 
            recording.align
            recordings.append(recording)
        else:
            x.recording = recordings[recordings.index(recording)]
    return annotations

def _annotation_to_line(annotation, transcription):
    '''creates a list with relevant information to create wav2vec dataset.
    the list can be loaded with DataLine and a list of these lists can
    be loaded with data
    '''
    line = [annotation.pk]
    line.append(annotation.recording.pk)
    clean_transcription = Cleaner(transcription).text_clean
    line.extend([transcription,clean_transcription])
    line.append(annotation.recording.wav_filename)
    line.append(annotation.ocr_line.start_time)
    line.append(annotation.ocr_line.end_time)
    line.append(annotation.alignment)
    return line

'''
ocr transcription lines, aligned to the audio with wav2vec 2.0 asr 
model, where  manually annotated for the quality of audio ocr alignment
the different alignment labels need to be treated differently
function below handle the different cases.
'''

def handle_good_alignments(annotations):
    '''keep all good alignments and use the ocr transcription.'''
    a = get_alignment(annotations,'good')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        line = _annotation_to_line(annotation, annotation.ocr_line.ocr_text)
        output.append(line)
    return output

def handle_start_alignments(annotations, ratio_threshold = .5):
    '''only keep start alignment if levenshtein ration of last quarter
    is higher than ratio_threshold.
    if ASR is different in the last quarter of transcription compared to
    ocr transcription, it is likely that there was a substantial mismatch
    between ocr / asr transcription at the end
    '''
    a = get_alignment(annotations, 'start_match')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        if not annotation.corrected_transcription: continue
        add_levenshtein(annotation)
        if annotation.lratio.q4_ratio < ratio_threshold: continue
        ct = annotation.corrected_transcription
        line = _annotation_to_line(annotation,ct)
        output.append(line)
    return output

def handle_end_alignments(annotations, ratio_threshold = .5):
    '''only keep start alignment if levenshtein ration of first quarter
    is higher than ratio_threshold.
    if ASR is different in the first quarter of transcription compared to
    ocr transcription, it is likely that there was a substantial mismatch
    between ocr / asr transcription at the start
    '''
    a = get_alignment(annotations, 'end_match')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        if not annotation.corrected_transcription: continue
        add_levenshtein(annotation)
        if annotation.lratio.q1_ratio < ratio_threshold: continue
        ct = annotation.corrected_transcription
        line = _annotation_to_line(annotation,ct)
        output.append(line)
    return output

def handle_middle_alignments(annotations, ratio_threshold = .5):
    '''only keep start alignment if levenshtein ration of first and 
    quarter are higher than ratio_threshold.
    if ASR is different in the first & last quarter of transcription 
    compared to ocr transcription,
    it is likely that there was a substantial mismatch
    between ocr / asr transcription at the start and end
    '''
    a = get_alignment(annotations, 'middle_match')
    if not hasattr(a[0],'_align'): a = load_ocrlines(a)
    output = []
    for annotation in a:
        if not annotation.corrected_transcription: continue
        add_levenshtein(annotation)
        if annotation.lratio.q1_ratio < ratio_threshold: continue
        if annotation.lratio.q4_ratio < ratio_threshold: continue
        ct = annotation.corrected_transcription
        line = _annotation_to_line(annotation,ct)
        output.append(line)
    return output

def handle_alignments(annotations = None, ratio_threshold = .5):
    '''handle each annotation according to the different alignemnt
    labels.
    ratio_threshold is the cut of point for levenshtein ratio for
    non good alignments (see different function)
    '''
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
    '''get all annotation with a given alignment for a list of alignments.
    '''
    a = [x for x in annotations if x.alignment == alignment]
    return a

def add_needleman_wunch(a):
    '''add alignment between corrected_transcription and asr transcription.
    '''
    a.act=needleman_wunch.nw(a.corrected_transcription, a.ocr_line.asr_text)


def add_levenshtein(a):
    '''add the Ratio object to an annotation containing levenshtein ratio
    information.
    '''
    a.lratio = Ratio(a)
    
class Ratio:
    '''contains information about the levenshtein ration between corrected
    and asr transcription for different parts of the transcription.
    '''
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


            


