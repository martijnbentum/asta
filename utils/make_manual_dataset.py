
import json
import pickle
import random
from unidecode import unidecode

cache_dir = '/vol/tensusers/mbentum/ASTA/WAV2VEC_DATA/'
vocab_filename = cache_dir + 'vocab.json'
random.seed(9)


class ManualDataset():   
    def __init__(self, filename, minimum_duration = 0.5,
        max_duration = 7, minimum_tokens = 10, train_perc = .8, save = False):
        self.filename = filename
        self.data = pickle.load(open(filename,'rb'))
        self.name = filename.split('/')[-1].split('.')[0]
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
        m = 'Dataset: ' + self.name
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

    def make_json(self):
        n = self.name
        self.train_data = make_json(self.train,n +'_train', save= self.save)
        self.dev_data = make_json(self.dev,n +'_dev', save=self.save)
        self.test_data = make_json(self.test,n+'_test', save=self.save)

def line_to_dict(data):
    d = {'recording_pk':line.recording.pk}
    d['ocrline_index']=line.ocrline_index
    d['sentence']=line.cleaner.text_clean.lower()
    d['audiofilename']=line.recording.wav_filename
    d['sampling_rate']=16000
    d['start_time'] = line.start_time
    d['end_time'] = line.end_time
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
    ntotal = len(d.data)
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


