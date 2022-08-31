from unidecode import unidecode
from utils.dialect import dialect_groups
import json
import re
from utils import select
import string
import random

cache_dir = '/vol/tensusers/mbentum/ASTA/WAV2VEC_DATA/'
vocab_filename = cache_dir + 'vocab.json'

random.seed(9)

area_dict = select.make_area_to_recording_dict()

def make_datasets(minimum_match = 60, minimum_duration= 1, max_duration = 7,
    minimum_tokens = 10, train_perc = .8, save = False):
    datasets = {}
    for name in dialect_groups.keys():
        d = Dataset(name,minimum_match,minimum_duration,max_duration,
            minimum_tokens, train_perc, save)
        datasets[name] = d
    if save:
        make_vocab_dict(datasets, True)
    return datasets


def get_dialect_recordings(dialect_name):
    recordings = []
    for area_name in dialect_groups[dialect_name]:
        recordings.extend(area_dict[area_name])
    return recordings

def get_dialect_ocrlines(dialect_name, minimum_match = 60, minimum_duration= 1,
    minimum_tokens = 10):
    recordings = get_dialect_recordings(dialect_name)
    mismatch = minimum_match = 100 - minimum_match
    ocrlines = []
    d={'no_match':[],'no_times':[],'to_short':[],'to_few_tokens':[],'all':[]}
    for recording in recordings:
        align = recording.align
        if not hasattr(align,'ocr_lines'):continue
        ols= align.filter_ocr_lines(mismatch_threshold=mismatch)
        no_match=[x for x in align.ocr_lines if x.align_match < minimum_match]
        no_times = [x for x in ols if not x.duration]
        to_short= [x for x in ols if x.duration < minimum_duration]
        to_few_tokens= [x for x in ols if len(x.ocr_text) < minimum_tokens]
        bad = list(set(no_times + to_short + to_few_tokens))
        ok = [x for x in ols if x not in bad]
        d['no_match'].extend(no_match)
        d['no_times'].extend(no_times)
        d['to_short'].extend(to_short)
        d['to_few_tokens'].extend(to_few_tokens)
        d['all'].extend(bad + no_match)
        ocrlines.extend(ok)
    return ocrlines, d

class Dataset:
    def __init__(self, dialect_name, minimum_match = 60, minimum_duration = 1,
        max_duration = 7, minimum_tokens = 10, train_perc = .8, save = False):
        self.dialect_name = dialect_name
        self.minimum_match = minimum_match
        self.minimum_duration = minimum_duration
        self.max_duration = max_duration
        self.minimum_tokens = minimum_tokens
        self.train_perc = train_perc
        self.save = save
        self._set_info()
        self._clean()
        self._make_train_dev_test()
        self.make_json()

    def __repr__(self):
        m = 'Dataset: ' + self.dialect_name
        m += ' | dur: ' + str(round(self.duration_all/3600,1))
        # m += ' | dur excl: ' + str(round(self.duration_excluded/3600,1))
        m += ' | dur train: ' + str(round(self.duration_train/3600,1))
        # m += ' | dur test: ' + str(round(self.duration_test/3600,1))
        return m

    def _set_info(self):
        self.recordings = get_dialect_recordings(self.dialect_name)
        self.ocr_lines, d= get_dialect_ocrlines(self.dialect_name,
            self.minimum_match, self.minimum_duration, self.minimum_tokens)
        for key, value in d.items():
            setattr(self,'excluded_'+key,value)

    def _clean(self):
        for ol in self.ocr_lines:
            ol.cleaner = Cleaner(ol.ocr_text)

    def _make_train_dev_test(self):
        o = make_train_dev_test_set(self,self.max_duration,self.train_perc) 
        self.train, self.dev, self.test, self.train_perc = o

    def make_json(self):
        n = self.dialect_name
        self.train_data = make_json(self.train,n +'_train', save= self.save)
        self.dev_data = make_json(self.dev,n +'_dev', save=self.save)
        self.test_data = make_json(self.test,n+'_test', save=self.save)


    @property
    def duration_selection(self):
        return sum([x.duration for x in self.ocr_lines])

    @property
    def duration_train(self):
        return sum([x.duration for x in self.train])

    @property
    def duration_test(self):
        return sum([x.duration for x in self.test])
        
    @property
    def duration_all(self):
        return sum([x.duration for x in self.recordings])

    @property
    def duration_excluded(self):
        return sum([x.duration for x in self.excluded_all])
        
    @property
    def text_selection_raw(self):
        return '\n'.join([x.ocr_text for x in self.ocr_lines])

    @property
    def text_excluded_raw(self):
        return '\n'.join([x.ocr_text for x in self.excluded_all])
        
    

class Cleaner:
    def __init__(self,text):
        self.text_raw = text
        self.clean()

    def clean(self):
        self.text_clean = self.text_raw.lower()
        self.remove_diacritics()
        self.remove_in_word_apostrophe()
        self.remove_xword()
        self.remove_number()
        self.remove_punctuation()
        self.remove_extra_white_space()

    def remove_diacritics(self):
        self.text_clean = unidecode(self.text_clean)

    def remove_in_word_apostrophe(self):
        self.text_clean=  re.sub("(?<=[a-z])'(?=[a-z])",'',self.text_clean)

    def remove_xword(self):
        '''unintelligable speech was marked with a number of xxxx.'''
        if not self.has_xword: return
        self.text_clean = re.sub('[x]{2,}','',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    def remove_number(self):
        self.text_clean = re.sub('\d+',' ',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    def remove_punctuation(self):
        for char in string.punctuation:
            self.text_clean = re.sub('\\'+char,' ',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    def remove_extra_white_space(self):
        #remove extra whitespace and some remaining characters
        self.text_clean = re.sub('\s+\n\s+','\n',self.text_clean)
        self.text_clean = re.sub('\n+','\n',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    @property
    def has_xword(self):
        if not hasattr(self,'_xwords'):
            self._xwords = re.findall('[x]{2,}',self.text_raw)
        return len(self._xwords) > 0

    @property
    def has_number(self):
        if not hasattr(self,'_numbers'):
            self._numbers= re.findall('\d+',self.text_raw)
        return len(self._numbers) > 0

    @property
    def has_apostrophe(self):
        if not hasattr(self,'_apostrophes'):
            self._apostrophes= re.findall("'+",self.text_raw)
        return len(self._apostrophes) > 0


def ocrline_to_dict(ocrline):
    d = {'recording_pk':ocrline.recording.pk}
    d['ocrline_index']=ocrline.ocrline_index
    d['sentence']=ocrline.cleaner.text_clean.lower()
    d['audiofilename']=ocrline.recording.wav_filename
    d['sampling_rate']=16000
    d['start_time'] = ocrline.start_time
    d['end_time'] = ocrline.end_time
    return d
        
    
def make_json(ocr_lines, name, cache_dir = cache_dir, save = False):
    data = []
    for ocrline in ocr_lines:
        data.append(ocrline_to_dict(ocrline))
    output = {'data':data}
    if not name.endswith('.json'): name += '.json'
    if save:
        print('saving file to:',cache_dir + name)
        with open(cache_dir + name, 'w') as fout:
            json.dump(output,fout)
    return data
        
        
    


def make_train_dev_test_set(d, max_duration = 7, train_perc = .8):
    ntotal = len(d.ocr_lines)
    ntrain = int(ntotal * train_perc)
    ndev = int((ntotal-ntrain)/2)
    ntest = ntotal - (ntrain + ndev)
    indices = list(range(len(d.ocr_lines)))
    i = [i for i,x in enumerate(d.ocr_lines) if x.duration <= max_duration]
    not_to_long_indices = i
    if len(not_to_long_indices) > ntrain:
        train_indices = random.sample(not_to_long_indices,ntrain)
        other = [i for i in indices if i not in train_indices]
    else:
        train_indices = not_to_long_indices
        ntrain = len(train_indices)
        ndev = int((ntotal-ntrain)/2)
        ntest = ntotal - (ntrain + ndev)
        train_perc = round(ntrain / ntotal,2)
    other = [i for i in indices if i not in train_indices]
    dev_indices = random.sample(other,ndev)
    test_indices = list(set(indices) - set(train_indices+dev_indices))
    train = [d.ocr_lines[i] for i in train_indices]
    dev = [d.ocr_lines[i] for i in dev_indices]
    test= [d.ocr_lines[i] for i in test_indices]
    return train,dev,test,train_perc 


def make_vocab_dict(datasets = None, save=False):
    if not datasets: datasets = make_datasets(save=False)
    sentences= []
    for d in datasets.values():
        for split in 'train,dev,test'.split(','):
            data = getattr(d,split+'_data')
            for line in data:
                sentences.append(line['sentence'])
    sentences = ' '.join(sentences)
    vocab = list(set(sentences))
    vocab_dict = {v: k for k, v in enumerate(sorted(vocab))}
    vocab_dict['[UNK]'] = len(vocab_dict)
    vocab_dict['[PAD]'] = len(vocab_dict)
    vocab_dict['|'] = vocab_dict[' ']
    del vocab_dict[' ']
    if save:
        with open(vocab_filename, 'w') as fout:
            json.dump(vocab_dict,fout)
    return vocab_dict
        
                
    


    
    


