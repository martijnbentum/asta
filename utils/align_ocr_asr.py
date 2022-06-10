from texts.models import Recording, Asr
import glob
import os
import time

align_dir = '/vol/tensusers/mbentum/ASTA/ALIGN/'
ocr_dir = align_dir + 'OCR_CLEAN_TEXTS/'
asr_dir = align_dir + 'WAV2VEC2_CLEAN_TEXTS/'
started = align_dir + 'STARTED_ASR_CLEAN_TEXT_ALIGN/'
output_dir = align_dir + 'OUTPUT/'
nw_script = '/vol/tensusers/mbentum/ASTA/repo/utils/needleman_wunch.py'


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
    asr             asr object to select the asr version to align with the ocr text
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
            counter, record_ids =wait_for_processes_to_complete(counter,record_ids)
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

def recording_to_alignment(recording, asr = None):    
    '''
    recording  the recording you need the alignment for betwen ocr and asr
    asr        asr object to select the asr version to align with the ocr text
    '''
    if not asr: asr = Asr.objects.get(pk = 1)
    f = output_dir + '*recording-' + str(recording.pk) +'*asr-'+str(asr.pk)+'*'
    fn = glob.glob(f)
    if fn: f = fn[0]
    else: return False,False
    with open(f) as fin:
        ocr, asr = fin.read().split('\n')
    return ocr, asr


class Align:
    def __init__(self,recording, asr = None):
        if not asr: asr = Asr.objects.get(pk = 1)
        self.recording = recording
        self.asr = asr
        self._load_alignment()
        
    def _load_alignment(self):
        o,a = recording_to_alignment(self.recording,self.asr)
        self.ocr_align = o
        self.asr_align = a
        self.nchars = len(self.ocr_align)

    def show(self,width = 90):
        starts = list(range(0,self.nchars,width))
        ends = list(range(width,self.nchars,width)) + [self.nchars+1]
        for start, end in zip(starts,ends):
            print('OCR: ', self.ocr_align[start:end])
            print('ASR: ', self.asr_align[start:end])
            print(' ')
        



