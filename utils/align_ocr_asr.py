from texts.models import Recording, Asr
import glob
import os
import time
import textgrids


align_dir = '/vol/tensusers/mbentum/ASTA/ALIGN/'
ocr_dir = align_dir + 'OCR_CLEAN_TEXTS/'
asr_dir = align_dir + 'WAV2VEC2_CLEAN_TEXTS/'
started = align_dir + 'STARTED_ASR_CLEAN_TEXT_ALIGN/'
output_dir = align_dir + 'OUTPUT/'
nw_script = '/vol/tensusers/mbentum/ASTA/repo/utils/needleman_wunch.py'
textgrid_dir = '../TEXTGRIDS/'


def make_recording_filename(recording):
    '''create a filename based on a recording'''
    f ='record_id-'+str(recording.record_id)
    f += '_recording-' + str(recording.pk)
    return f

def make_ocr_texts():
    '''write ocr text to a text file
    '''
    recordings = Recording.objects.filter(ocr_transcription_available=True, 
        ocr_handwritten=False)
    error = []
    for x in recordings:
        filename = make_recording_filename(x)
        filename += '_ocr'
        filename = ocr_dir + filename
        ocr_text = x.text_clean.replace('\n',' ')
        if len(ocr_text) == 0:error.append(x)
        print('saving text to:',filename)
        with open(filename,'w') as fout:
            fout.write(ocr_text)
    return error


def make_asr_texts(asr=None):
    '''write asr text to a text file
    '''
    if not asr: asr = Asr.objects.get(pk = 1)
    recordings= Recording.objects.filter(ocr_transcription_available=True, 
        ocr_handwritten=False)
    error = []
    for x in recordings:
        filename = make_recording_filename(x)
        filename += '_asr-' + str(asr.pk)
        filename = asr_dir + filename
        t = x.transcription_set.filter(transcription_type__name='asr')
        try:asr_transcription= t.get(asr=asr)
        except:
            print(x,'does not have asr transcription')
            error.append(x)
        else:
            asr_text = asr_transcription.text
            print('saving text to:',filename)
            with open(filename,'w') as fout:
                fout.write(asr_text)
    return error
        
        
def make_ocr_asr_pairs(asr = None):
    '''search for match ocr asr files to align.
    asr         asr object to select the asr version to align with the ocr text
    '''
    if not asr: asr = Asr.objects.get(pk = 1)
    ocr_fn = glob.glob(ocr_dir + '*')
    asr_fn = glob.glob(asr_dir + '*asr-'+str(asr.pk))
    pairs = []
    error = []
    for ocr_f in ocr_fn:
        found = False
        ocr_record_id = ocr_f.split('record_id-')[-1].split('_')[0]
        for asr_f in asr_fn:
            asr_record_id = asr_f.split('record_id-')[-1].split('_')[0]
            if ocr_record_id == asr_record_id:
                pairs.append([ocr_f,asr_f])
                found =True
                break
        if not found: error.append(ocr_f)
    return pairs,error


def align(asr=None, n = 5, check_started = True):
    '''
    align asr and ocr output with needleman wunch algorithm
    the computation time increases a lot with longer sequences
    so new python processes are called to align multiple sequences
    simultanuously
    asr             asr object to select the asr version to align with 
                    the ocr text
    n               number of processes to run simultanuously
    check_started   check whether the specific pair was already started
                    usefull if you run this function multiple times
    '''
    if not asr: asr = Asr.objects.get(pk = 1)
    pairs, error = make_ocr_asr_pairs(asr)
    counter = 0
    record_ids = [] 
    for pair in pairs:
        if counter > n: 
            print('started:',n,'processes')
            counter, record_ids =wait_for_processes_to_complete(counter,
            record_ids)
        ocr_f, asr_f = pair
        started_filename = started + asr_f.split('/')[-1]
        if os.path.isfile(started_filename ) and check_started: 
            print(asr_f, 'already started to align')
            continue
        record_ids.append( ocr_f.split('record_id-')[-1].split('_')[0])
        with open(started_filename,'w') as fout:
            fout.write('started')
        output_filename = output_dir + asr_f.split('/')[-1]
        output_filename = output_filename + '_output'
        command = 'python3 ' + nw_script + ' ' + ocr_f + ' ' +asr_f + ' '
        command += output_filename + ' &'
        print(command)
        os.system(command)
        counter += 1


def _wait_for_processes_to_complete(counter,record_ids):
    '''
    helper function to wait for processes to complete before starting
    new processes to align ocr and asr
    '''
    print(' waiting ... ',record_ids,counter)
    old_counter = counter
    exclude_rids = []
    while True:
        output_fn = glob.glob(output_dir +'*')
        for f in output_fn:
            for rid in record_ids:
                if 'record_id-' + rid in f: 
                    counter -= 1
                    exclude_rids.append(rid)
        if counter < old_counter:
            output_rids = [rid for rid in record_ids if rid not in exclude_rids]
            break
        print('did not find completed files, waiting ... ',record_ids,counter)
        time.sleep(15)
    return counter, output_rids

def recording_to_alignment_filename(recording, asr = None):
    if not asr: asr = Asr.objects.get(pk = 1)
    f = output_dir + '*recording-' + str(recording.pk) +'_asr-'+str(asr.pk)+'*'
    fn = glob.glob(f)
    if fn: return fn[0]
    else: return False

def recording_to_alignment(recording, asr = None):    
    '''
    recording  the recording you need the alignment for betwen ocr and asr
    asr        asr object to select the asr version to align with the ocr text
    '''
    if not asr: asr = Asr.objects.get(pk = 1)
    f = recording_to_alignment_filename(recording,asr)
    if not f: return False,False
    with open(f) as fin:
        ocr, asr = fin.read().split('\n')
    return ocr, asr


class Align:
    def __init__(self,recording, asr = None):
        if not asr: asr = Asr.objects.get(pk = 1)
        self.recording = recording
        self.asr = asr
        self._load_alignment()
        if self.ok:
            self._align_ocr_transcriptions()
            self._get_asr_transcription()
            self._align_asr_words()
            self._check_ok()
        
    def __repr__(self):
        return 'Alignment of ' + self.recording.__repr__()

    def _check_ok(self):
        ok,ok1 = True,True
        for ocr_line in self.ocr_lines:
            if not ocr_line.ok: ok = False
        if not ok: self.ocr_lines_ok = False
        else: self.ocr_lines_ok = True 
        for asr_word in self.asr_words:
            if not asr_word.ok: ok1 = False
        if not ok1: self.asr_words_ok = False
        else: self.asr_words_ok=True 
        if not ok or not ok1: self.ok = False
        
    def _load_alignment(self):
        self.filename = recording_to_alignment_filename(self.recording,self.asr)
        o,a = recording_to_alignment(self.recording,self.asr)
        self.ocr_align = o
        self.asr_align = a
        if self.ocr_align:
            self.nchars = len(self.ocr_align)
        else: self.nchars = 0
        if self.nchars == 0 or not self.asr_align: self.ok = False
        else: 
            self.ok = True
            asr_check = list(set(self.asr_align))
            if len(asr_check) == 1 and asr_check[0] == '-': self.ok = False

    def _align_ocr_transcriptions(self):
        self.ocr_lines = []
        index = 0
        for transcription in self.recording.ocr_transcriptions:
            if not transcription.text_clean: continue
            ol = Ocrline(transcription,self,index)
            self.ocr_lines.append(ol)
            index = ol.end + 1
            
    def _get_asr_transcription(self):
        self.asr_transcription = False
        asr_transcriptions = self.recording.asr_to_transcriptions(self.asr)
        if len(asr_transcriptions) == 0: return
        longest = asr_transcriptions[0]
        for x in asr_transcriptions:
            if x.duration > longest.duration: longest = x
        self.asr_transcription = longest

    def _align_asr_words(self):
        self.asr_words = []
        index=0
        self.index_to_times = {}
        self.index_to_asr_word= {}
        for word in self.asr_transcription.asr_word_table:
            aw = Asrword(word,self,index)
            self.asr_words.append(aw)
            index = aw.end + 1
            self.index_to_times.update(aw.index_to_times)
            self.index_to_asr_word.update(aw.index_to_asr_word)

    def _asr_word_tier(self):
        intervals = make_asr_word_intervals(self.asr_words)
        return textgrids.Tier(intervals)

    @property
    def textgrid(self):
        if hasattr(self,'_textgrid'): return self._textgrid 
        f = textgrid_dir + self.filename.split('/')[-1]
        self.filename_textgrid = f.replace('_output','.TextGrid')
        tg = textgrids.TextGrid()
        tg['asr words'] = self._asr_word_tier()
        for name in self.ocr_lines[0].interval_dict.keys():
            if name == 'asr words': continue
            if name not in tg.keys(): tg[name] = textgrids.Tier()
            for ocr_line in self.ocr_lines:
                if not ocr_line.start_time or not ocr_line.end_time:continue
                if ocr_line.duration == 0: continue
                interval = ocr_line.interval_dict[name]
                if not interval: continue
                tg[name].append(interval)
        tg.xmin = self.start_time
        tg.xmax = self.end_time
        tg.filename = self.filename_textgrid
        self._textgrid = tg
        return self._textgrid

    def save_textgrid(self):
        self.textgrid.write(self.filename_textgrid)

    @property
    def start_time(self):
        return self.asr_words[0].start_time

    @property
    def end_time(self):
        return self.asr_words[-1].start_time
        
    def show(self,width = 90):
        starts = list(range(0,self.nchars,width))
        ends = list(range(width,self.nchars,width)) + [self.nchars+1]
        for start, end in zip(starts,ends):
            print('OCR: ', self.ocr_align[start:end])
            print('ASR: ', self.asr_align[start:end])
            print(' ')

    def filter_ocr_lines(self,mismatch_threshold = 55):
        output = []
        for ocr_line in self.ocr_lines:
            if ocr_line.align_mismatch < mismatch_threshold:
                output.append(ocr_line)
        return output

    @property
    def ocr_lines_ok_perc(self):
        return len(self.filter_ocr_lines()) / len(self.ocr_lines) * 100
        

class Ocrline:
    def __init__(self,transcription,align,index):
        self.transcription = transcription
        self.align = align
        self.index = index
        self._align_transcription_with_alignment()

    def __repr__(self):
        m = 'Ocrline: ' + str(self.start) + ' ' + str(self.end) + ' | '
        m += str(self.start_time) + ' - '
        m += str(self.end_time) 
        return m

    def __str__(self):
        m = self.__repr__() + '\n'
        if self.duration: m += 'Duration: ' + str(self.duration) + '\n'
        m += 'mismatch: ' + str(self.align_mismatch) + '\n'
        m += 'ocr gaps: ' + str(self.ocr_align_gaps) + '\n'
        m += 'asr gaps: ' + str(self.asr_align_gaps) + '\n'
        m +=  'OCR: '+self.transcription.text_clean + '\n'
        m +=  'ASR: '+ self.asr_text + '\n'
        m +=  'OA:  '+self.ocr_align_text+ '\n'
        m +=  'AA:  '+self.asr_align_text
        return m

    
    def _align_transcription_with_alignment(self):
        self.indices,self.ok = align_ocr_transcription_with_ocr_alignment(
            self.index, self.transcription, self.align.ocr_align)
        if self.indices:
            self.start = self.indices[0]
            self.end = self.indices[-1]
        else: self.start, self.end = False, False

    @property
    def matching_indices(self):
        if hasattr(self,'_matching_indices'): return self._matching_indices
        indices = range(self.start,self.end+1)
        self._matching_indices = []
        for index in indices:
            if index in self.align.index_to_asr_word.keys():
                self._matching_indices.append(index)
        return self._matching_indices

    def _check_asr_word(self, word,other_indices):
        if not other_indices: return True
        indices = self.matching_indices
        other_count, this_count = 0, 0 
        for index in word.index_to_asr_word.keys():
            if index in other_indices: other_count += 1
            if index in indices: this_count += 1
        return this_count > other_count
        

    @property
    def asr_words(self):
        if hasattr(self,'_asr_words'): return self._asr_words
        indices = self.matching_indices
        self._asr_words = []
        for index in indices:
            word = self.align.index_to_asr_word[index]
            if self.asr_words == []: 
                ok = self._check_asr_word(word,self.previous_indices)
            if word not in self._asr_words and ok:self.asr_words.append(word)
        if self._asr_words:
            ok = self._check_asr_word(self._asr_words[-1],self.next_indices)
            if not ok:
                self._asr_words = self._asr_words[:-1]
        return self._asr_words

    @property
    def asr_text(self):
        return ' '.join([x.word for x in self.asr_words])

    @property
    def ocr_align_text(self):
        return self.align.ocr_align[self.start:self.end+1]

    @property
    def asr_align_text(self):
        return self.align.asr_align[self.start:self.end+1]

    @property
    def align_mismatch(self):
        n = len(self.asr_align_text)
        mismatch = 0
        for achar,ochar in zip(self.asr_align_text,self.ocr_align_text):
            if achar != ochar: mismatch += 1
        return round(mismatch / n * 100,2)
            
    @property
    def asr_align_gaps(self):
        n = len(self.asr_align_text)
        gaps = self.asr_align_text.count('-')
        return round(gaps / n * 100,2)

    @property
    def ocr_align_gaps(self):
        n = len(self.asr_align_text)
        gaps = self.ocr_align_text.count('-')
        return round(gaps / n * 100,2)
                

    @property
    def start_time(self):
        if self.asr_words:
            return self.asr_words[0].start_time
        return False

            
    @property
    def end_time(self):
        if self.asr_words:
            return self.asr_words[-1].end_time
        return False

    @property
    def previous_indices(self):
        index = self.align.ocr_lines.index(self)
        if index == 0: return False
        return self.align.ocr_lines[index -1].matching_indices

    @property
    def next_indices(self):
        index = self.align.ocr_lines.index(self)
        if index == len(self.align.ocr_lines) -1: return False
        return self.align.ocr_lines[index +1].matching_indices

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return False

    @property
    def show(self):
        print(self.align.ocr_align[self.start:self.end+1])
        print(self.transcription.text_clean)

    @property
    def interval_dict(self):
        return make_ocr_line_intervals(self)
        

class Asrword:
    def __init__(self,asr_word,align,index):
        self.asr_word = asr_word
        self.word = asr_word['word']
        self.start_time = self.asr_word['start']
        self.end_time = self.asr_word['end']
        self.align = align
        self.index = index
        self._align_asr_word_with_alignment()
        self.start = self.indices[0]
        self.end = self.indices[-1]

    def __repr__(self):
        m = 'Asr word: '+ self.word + ' | ' 
        m += str(self.start_time) + ' - ' + str(self.end_time)
        return m
        
    def _align_asr_word_with_alignment(self):
        self.indices,self.ok = align_asr_word_with_asr_alignment(
            self.index, self.asr_word, self.align.asr_align)

    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def show(self):
        print(self.align.asr_align[self.start:self.end+1])
        print(self.asr_word['word'])

    @property
    def index_to_times(self):
        indices = range(self.start,self.end+1)
        d = {}
        for index in indices:
            d[index] = {'start_time':self.start_time, 'end_time':self.end_time}
        return d
            
    @property
    def index_to_asr_word(self):
        indices = range(self.start,self.end+1)
        d = {}
        for index in indices:
            d[index] = self
        return d


def align_ocr_transcription_with_ocr_alignment(start_index,transcription,
    align_text):
    t = transcription.text_clean
    indices,ok = _string_pair_to_indices(start_index, t, align_text)
    return indices,ok
            
def align_asr_word_with_asr_alignment(start_index, asr_word, align_text):
    t = asr_word['word']
    indices, ok = _string_pair_to_indices(start_index,t,align_text)
    return indices,ok

def _string_pair_to_indices(start_index,short_string,long_string):
    ok = True
    indices = []
    for char in short_string:
        while True:
            if start_index > len(long_string) -1: break
            align_char = long_string[start_index] 
            if char == align_char: 
                indices.append(start_index)
                start_index += 1
                break
            start_index += 1
    if len(indices) != len(short_string): 
        print(short_string,start_index)
        ok = False
    if short_string != _make_string_from_indices(indices,long_string):
        print(short_string,_make_string_from_indices(indices,long_string))
        ok = False
    #assert len(indices) == len(short_string)
    #assert short_string == _make_string_from_indices(indices,long_string)
    return indices, ok 
    

def _make_string_from_indices(indices,align_text):
    o = ''
    for index in indices:
        o += align_text[index]
    return o


def make_ocr_line_intervals(ocr_line):
    '''make textgrid intervals for different tiers based on ocr line info.'''
    start, end = ocr_line.start_time, ocr_line.end_time
    d = {}
    d['ocr transcription'] = textgrids.Interval(
        ocr_line.transcription.text_clean, start, end)
    d['asr transcription'] = textgrids.Interval(ocr_line.asr_text,start,end) 
    d['ocr align'] = textgrids.Interval(ocr_line.ocr_align_text,start,end) 
    d['asr align'] = textgrids.Interval(ocr_line.asr_align_text,start,end) 
    d['asr words'] = make_asr_word_intervals(ocr_line.asr_words)
    return d

def make_asr_word_intervals(asr_words):
    '''make textgrid intervals for different asr word interval tier.'''
    asr_word_intervals = []
    for word in asr_words:
        interval = textgrids.Interval(word.word, word.start_time, 
            word.end_time)
        asr_word_intervals.append(interval)
    return asr_word_intervals

def make_all_aligned_textgrids(start_index = 0):
    ocr = Recording.objects.filter(ocr_transcription_available=True, 
        ocr_handwritten=False)
    error = []
    for i,recording in enumerate(ocr[start_index:]):
        print(i+start_index,recording)
        a = Align(recording)
        if a.ok: a.save_textgrid()
        else:
            print('could not align',recording)
            if hasattr(a,'ocr_lines_ok'):
                print(a.ocr_lines_ok,a.asr_words_ok)
            error.append(recording)
    return error


