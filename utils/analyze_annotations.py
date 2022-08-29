import numpy as np
from matplotlib import pyplot as plt
        


class Gaps:
    def __init__(self,recording):
        self.recording = recording
        self.align = recording.align
        self.ols = self.align.ocr_lines
        self.annotations = None
        self.users = None
        if self.align: self.set_info()
        else: self.ok = False

    def __repr__(self):
        m = 'Gaps object of ' +self.recording.__repr__() 
        return m

    def __str__(self):
        m = self.__repr__() + '\n'
        m += 'Annotators: '+ ', '.join([user.username for user in self.users])
        m += '\nnannotations: ' + str(self.nannotations) + '\n'
        m += 'perc annotated: ' + str(self.perc_annotated) + '\n'
        return m


    def set_info(self):
        self.annotations = self.align.annotations
        if not self.annotations:
            self.ok = False
            return
        self.nannotations = len(self.annotated_ocrlines)
        self.perc_annotated = (self.nannotations / self.align.nocrlines)*100
        self.perc_annotated = round(self.perc_annotated,2)
        self.users = list(set([x.user for x in self.annotations]))
        self.username_to_annations = {}
        for user in self.users:
            annotations = self.annotations.filter(user = user)
            self.username_to_annations[user.username] = annotations

    @property
    def annotated_ocrlines(self):
        if not hasattr(self,'_annotated_ocrlines'):
            ols = self.align.ocr_lines
            t = list(set([ols[x.ocrline_index] for x in self.annotations]))
            self._annotated_ocrlines = t
        return self._annotated_ocrlines

    @property
    def not_annotated_ocrlines(self):
        if hasattr(self,'_not_annotated_ocrlines'):
            return self._not_annotated_ocrlines
        output = []
        for ol in self.align.ocr_lines:
            if ol in self.annotated_ocrlines: continue
            if ol not in output:
                output.append(ol)
        self._not_annotated_ocrlines = output
        return self._not_annotated_ocrlines

    @property
    def mismatching_annotations_ocrlines(self):
        if hasattr(self,'_mismatching_annotations_ocrlines'):
            return self._mismatching_annotations_ocrlines
        ocrlines= []
        for mismatch in self.mismatching_annotations:
            ocrlines.append(mismatch[0].ocrlines)
        self._mismatching_annotations_ocrlines = ocrlines
        return self._mismatching_annotations_ocrlines

    @property
    def matchinging_annotations_ocrline_indices(self):
        if hasattr(self,'_matching_annotations_ocrlines'):
            return self._matching_annotations_ocrlines
        ocrlines = []
        for match in self.matching_annotations:
            ocrlines.append(match[0].ocrline_index)
        self._matching_annotations_ocrlines = ocrlines
        return self._matching_annotations_ocrlines

    @property
    def mismatching_annotations(self):
        if hasattr(self,'_mismatching_align_annotations'):
            return self._mismatching_align_annotations
        mismatch = []
        match = []
        for ocrline_index in self.annotated_ocrline_indices:
            annotations = self.annotations.filter(ocrline_index = ocrline_index)
            if len(annotations) > 1:
                alignments = list(set([x.alignment for x in annotations]))
                if len(alignments) > 1: mismatch.append(annotations)
                else: match.append(annotations)
        self._mismatching_align_annotations = mismatch 
        self._matching_align_annotations = match 
        return self._mismatching_align_annotations

    @property
    def matching_annotations(self):
        if hasattr(self,'_matching_align_annotations'):
            return self._matching_align_annotations
        _ = self.mismatching_align_annotations
        return self._matching_align_annotations
        

    @property
    def start_gap(self):
        '''gap object containing ocr lines at the start of the recording not 
        annotated possibly meta text
        '''
        if hasattr(self,'_start_gap'): return self._start_gap
        annotations = sorted(self.annotations,key=lambda x:x.ocrline_index)
        index = len(annotations) -1
        for annotation in annotations:
            if annotation.alignment != 'bad': 
                index = annotation.ocrline_index
                break
        self._start_gap = Gap(self, self.align.ocr_lines[:index])
        return self._start_gap

    @property
    def end_gap(self):
        '''ocr lines at the end of the recording not annotated or not matching.
        '''
        if hasattr(self,'_end_gap'): return self._end_gap
        annotations = sorted(self.annotations,key=lambda x:x.ocrline_index)
        index = 0
        for annotation in annotations[::-1]:
            if annotation.alignment != 'bad':
                index = annotation.ocrline_index +1
                break
        self._end_gap = Gap(self, self.align.ocr_lines[index:])
        return self._end_gap

    @property
    def middle_gaps(self):
        '''gaps in the middle of a recording, containing ocr lines
        not annotated or not aligned properly
        if length is long probably bad alignment
        '''
        if hasattr(self,'_middle_gaps'): return self._middle_gaps
        self._middle_gaps = []
        annotations = self.annotations.exclude(alignment = 'bad')
        for i,annotation in enumerate(annotations):
            if i >= len(annotations)-1: break
            if annotation.ocrline_index+1 != annotations[i+1].ocrline_index:
                start = annotation.ocrline_index +1
                end = annotations[i+1].ocrline_index +1
                ocr_lines = self.align.ocr_lines[start:end]
                gap = Gap(self,ocr_lines)
                if gap.ok: self._middle_gaps.append(gap)
        return self._middle_gaps

    def filter_middle_gaps(self, min_duration = None, n_median = 2):
        if min_duration == None: 
            min_duration=np.median([x.duration for x in self.middle_gaps])
            min_duration *= n_median 
        return [x for x in self.middle_gaps if x.duration >= min_duration]
    
        
class Gap:
    def __init__(self, gaps, ocr_lines):
        self.gaps = gaps
        self.recording = gaps.recording
        self.align = gaps.align
        self.ocr_lines = ocr_lines
        self.ok = len(self.ocr_lines) > 0

    def __repr__(self):
        m = 'gap | start: ' + str(int(self.start_time))
        m += '| end: ' + str(int(self.end_time))
        m += '| dur: ' + str(int(self.duration))
        m += ' | nocrlines: ' + str(len(self.ocr_lines))
        m += ' | match: ' + str(int(self.match))
        return m

    @property
    def start_time(self):
        if hasattr(self,'_start_time'): return self._start_time
        self._start_time = 0.0
        ol = self.ocr_lines[0]
        if ol.start_time:
            self._start_time = ol.start_time
        if ol.ocrline_index != 0:
            temp = self.align.ocr_lines[:ol.ocrline_index]
            for ol in temp[::-1]:
                if ol.end_time: 
                    self._start_time = ol.end_time
                    break
                if ol.start_time: 
                    self._start_time = ol.start_time
        return self._start_time

    @property
    def end_time(self):
        if hasattr(self,'_end_time'): return self._end_time
        self._end_time = False
        ol = self.ocr_lines[-1]
        if ol.end_time: 
            self._end_time = ol.end_time
        elif ol.ocrline_index == len(self.align.ocr_lines) -1:
            import audio
            y = audio.load_audio(self.gaps.recording.web_wav)
            duration = librosa.get_duration(y,16000)
            return duration
        else:
            temp = self.align.ocr_lines[ol.ocrline_index:]
            for ol in temp:
                if ol.start_time: 
                    self._end_time= ol.start_time
                    break
                if ol.end_time: 
                    self._end_time= ol.end_time
                    break
        return self._end_time

    @property
    def duration(self):
        if type(self.start_time) == float and type(self.end_time) == float:
            return self.end_time - self.start_time
            
    @property
    def show(self):
        for line in self.ocr_lines:
            line.show

    @property
    def ocr_text(self):
        o = []
        for ol in self.ocr_lines:
            o.append(ol.ocr_text)
        return '\n'.join(o)

    @property
    def old_asr_text(self):
        o = []
        for ol in self.ocr_lines:
            o.append(ol.asr_text)
        return '\n'.join(o)

    @property
    def asr_words(self):
        if hasattr(self,'_asr_words'): return self._asr_words
        self._asr_words = []
        for aw in self.align.asr_words:
            if aw.in_interval(self.start_time,self.end_time):
                self._asr_words.append(aw)
        return self._asr_words 

    @property
    def asr_text(self):
        return ' '.join([x.word for x in self.asr_words])

    @property
    def match(self):
        return np.median([ol.align_match for ol in self.ocr_lines])
        
        

def cluster_indices(indices):
    indices = sorted(indices)
    output = []
    temp = []
    for index in indices:
        if not temp: temp.append(index)
        elif index == temp[-1] or index == temp[-1] +1:
            temp.append(index)
        else:
            output.append(temp)
            temp = []
    return output
        


def annotations_to_recording_set(annotations = None):
    if not annotations:
        from texts.models import Annotation
        annotations = Annotation.objects.all()
    recordings = []
    for annotation in annotations:
        if annotation.recording not in recordings:
            recordings.append(annotation.recording)
    return recordings

def annotations_to_ocrlines(annotations = None):
    recordings = annotations_to_recording_set(annotations)
    output = []
    for recording in recordings:
        g = Gaps(recording)
        output.extend(g.annotated_ocrlines)
    return output

def ocrlines_to_alignment_match(ocrlines = None):
    if not ocrlines: ocrlines = annotations_to_ocrlines()
    output = []
    for ol in ocrlines:
        alignments = list(set([x.alignment for x in ol.annotations]))
        match = ol.align_match
        output.append([alignments,match])
    return output

def bin_perc_ok_match(alignment_match = None):
    if not alignment_match: alignment_match = ocrlines_to_alignment_match()
    bins = zip(list(range(0,100,5)),list(range(5,101,5)))
    good_count = {}
    ok_count = {}
    good_count = {}
    total_count = {}
    for start, end in bins:
        if end not in ok_count.keys():
            ok_count[end], total_count[end], good_count[end] = 0,0,0
        for am in alignment_match:
            alignments, match = am
            if match >= start and match < end:
                if 'bad' not in alignments: 
                    ok_count[end] += 1
                if len(alignments) == 1 and alignments[0] == 'good':
                    good_count[end] += 1
                total_count[end] += 1
    perc_ok = []
    perc_good = []
    match = []
    total_counts = []
    ok_counts = []
    for key, value in ok_count.items():
        if total_count[key] == 0: perc = 0
        else: perc = round((value / total_count[key]) *100,2)
        perc_ok.append(perc)
        if perc == 0: perc_good.append(perc)
        else: 
            perc_good.append(round((good_count[key]/total_count[key])*100,2))
        match.append(key)
        total_counts.append(total_count[key])
        ok_counts.append(value)
    return perc_ok, match, ok_counts, total_counts, perc_good

def plot_perc_ok_match(perc_ok = None, match = None, total_counts = None,
    perc_good = None):
    if not perc_ok:
        perc_ok, match, ok_counts, total_counts, perc_good = bin_perc_ok_match()
    plt.clf()
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(match, perc_ok, 'b')
    ax1.plot(match, perc_good, 'c')
    ax2.plot(match, total_counts,'r')
    ax1.legend(['% ok alignment','% good alignment'])
    plt.title('% ok alignment as a function of ocr-asr token match')
    ax1.set_xlabel('% match between ocr and asr tokens')
    ax1.set_ylabel('% ok/good alignment', color = 'b')
    ax2.set_ylabel('# annotations', color = 'r')
    plt.show()
