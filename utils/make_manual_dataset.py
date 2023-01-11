
import json
import pickle
import random
from unidecode import unidecode
from utils import handle_annotations

cache_dir = '/vol/tensusers/mbentum/ASTA/WAV2VEC_DATA/'
vocab_filename = cache_dir + 'vocab.json'
random.seed(9)


class ManualDataset():   
    def __init__(self, filename = '../etske_acht.pkl', minimum_duration = 0.5,
        max_duration = 7, minimum_tokens = 10, train_perc = .8, save = False):
        self.filename = filename
        self.data = handle_annotations.Data(filename)
        self.name = filename.split('/')[-1].split('.')[0]
        self.minimum_duration = minimum_duration
        self.max_duration = max_duration
        self.minimum_tokens = minimum_tokens
        self.train_perc = train_perc
        self.save = save
        self._set_info()
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
        self.lines, d = select_lines(self.data.data, self.minimum_duration, 
            self.minimum_tokens, self.max_duration)
        for key, value in d.items():
            setattr(self,'excluded_'+key,value)

    def _make_train_dev_test(self):
        o = make_train_dev_test_set(self.lines,self.train_perc) 
        self.train, self.dev, self.test, self.train_perc = o
        

    def make_json(self):
        n = self.name
        self.train_data = make_json(self.train,n +'_train', save= self.save)
        self.dev_data = make_json(self.dev,n +'_dev', save=self.save)
        self.test_data = make_json(self.test,n+'_test', save=self.save)

def line_to_dict(line):
    d = {'recording_pk':line.recording_pk}
    d['annotation_pk']=line.annotation_pk
    d['sentence']=line.transcription
    d['audiofilename']=line.wav_filename
    d['sampling_rate']=16000
    d['start_time'] = line.start_time
    d['end_time'] = line.end_time
    return d

def make_json(lines, name, cache_dir = cache_dir, save = False):
    data = []
    for line in lines:
        data.append(line_to_dict(line))
    output = {'data':data}
    if not name.endswith('.json'): name += '.json'
    if save:
        print('saving file to:',cache_dir + name)
        with open(cache_dir + name, 'w') as fout:
            json.dump(output,fout)
    return data

def make_train_dev_test_set(lines, train_perc = .8):
    ntotal = len(lines)
    ntrain = int(ntotal * train_perc)
    ndev = int((ntotal-ntrain)/2)
    ntest = ntotal - (ntrain + ndev)
    indices = list(range(len(lines)))
    good_indices = [i for i,x in enumerate(lines) if x.alignment == 'good']
    test_indices = random.sample(good_indices, ntest)
    other = [i for i in indices if i not in test_indices]
    dev_indices = random.sample(other, ndev)
    exclude = test_indices + dev_indices
    train_indices= [i for i in indices if i not in exclude]
    train = [lines[i] for i in train_indices]
    dev = [lines[i] for i in dev_indices]
    test= [lines[i] for i in test_indices]
    return train,dev,test,train_perc 

def select_lines(lines,minimum_duration= 1,minimum_tokens = 10, 
    max_duration = 7):
    d = {} 
    mt = minimum_tokens
    d['to_short'] = [x for x in lines if x.duration < minimum_duration]
    d['to_few_tokens'] = [x for x in lines if len(x.transcription) < mt]
    d['to_long'] = [x for x in lines if x.duration > max_duration]
    d['bad'] = list(set(d['to_short'] + d['to_few_tokens'] + d['to_long']))
    ok = [x for x in lines if x not in d['bad']]
    return ok, d


