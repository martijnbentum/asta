import numpy as np

class Gaps:
    def __init__(self,recording):
        self.recording = recording
        self.align = recording.align
        self.annotations = None
        self.users = None
        if self.align: self.set_info()
        else: self.ok = False

    def set_info(self):
        self.annotations = self.align.annotations
        self.users = list(set([x.user for x in self.annotations]))
        self.username_to_annations = {}
        for user in self.users:
            annotations = self.annotations.filter(user = user)
            self.username_to_annations[user.username] = annotations

    @property
    def annotated_ocrline_indices(self):
        if not hasattr(self,'_annotated_ocrline_indices'):
            t = list(set([x.ocrline_index for x in self.annotations]))
            self._annotated_ocrline_indices = t
        return self._annotated_ocrline_indices

    @property
    def not_annotated_ocrline_indices(self):
        if hasattr(self,'_not_annotated_ocrline_indices'):
            return self._not_annotated_ocrline_indices
        indices = self.annotated_ocrline_indices
        output = []
        for ol in self.align.ocr_lines:
            if ol.ocrline_index in indices: continue
            if ol.ocrline_index not in output:
                output.append(ol.ocrline_index)
        self._not_annotated_ocrline_indices = output
        return self._not_annotated_ocrline_indices

    @property
    def mismatching_align_annotations(self):
        if hasattr(self,'_mismatching_align_annotations'):
            return self._mismatching_align_annotations
        output = []
        for ocrline_index in self.annotated_ocrline_indices:
            annotations = self.annotations.filter(ocrline_index = ocrline_index)
            if len(annotations) > 1:
                alignments = list(set([x.alignment for x in annotations]))
                if len(alignments) > 1: output.append(annotations)
        self._mismatching_align_annotations = output
        return self._mismatching_align_annotations

    @property
    def start_gap(self):
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
        
