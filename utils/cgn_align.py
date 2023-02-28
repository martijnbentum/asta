# part of the ASTA project to align wav2vec and cgn with nw
# further analysis done here.

import glob
import random
import os
from utils import needleman_wunch as nw
# from text.models import Textgrid

cgn_wav2vec_dir = '/vol/tensusers3/mbentum/cgn_wav2vec/'
cgn_align = '/vol/tensusers3/mbentum/cgn_wav2vec_align/'

def table_filenames():
    fn = glob.glob(cgn_wav2vec_dir + '*.table')
    return fn

def text_filename():
    fn = glob.glob(cgn_wav2vec_dir + '*.txt')
    return fn

def load_table(filename):
    with open(filename) as fin:
        t = fin.read()
    temp= [x.split('\t') for x in t.split('\n') if x]
    table = []
    for grapheme, start, end in temp:
        table.append([grapheme,float(start), float(end)])
    return table

def load_text(filename):
    with open(filename) as fin:
        t = fin.read()
    return t

def table_filename_to_cgn_id(f):
    cgn_id = f.split('/')[-1].split('.')[0]
    return cgn_id

def make_alignments():
    fn = table_filenames()
    random.shuffle(fn)
    for f in fn:
        cgn_id = table_filename_to_cgn_id(f)
        align_filename = cgn_align + cgn_id
        if os.path.isfile(align_filename): 
            print('skiping',cgn_id)
            continue
        print('handling',cgn_id)
        Align(cgn_id)
        
    

    
class Align:
    def __init__(self,cgn_id):
        self.cgn_id = cgn_id
        self.textgrid = Textgrid.objects.get(cgn_id = cgn_id)
        self.awd_words = self.textgrid.word_set.all()
        self.awd_text = ' '.join([w.awd_word for w in self.awd_words])
        self._set_wav2vec_table_and_text()
        self._set_align()

    def _set_wav2vec_table_and_text(self):
        self.wav2vec_base_filename = cgn_wav2vec_dir + self.textgrid.cgn_id
        self.wav2vec_table=load_table(self.wav2vec_base_filename+'.table')
        self.wav2vec_text=load_text(self.wav2vec_base_filename+'.txt')

    def _set_align(self):
        self.align_filename = cgn_align + self.cgn_id
        if os.path.isfile(self.align_filename): 
            with open(self.align_filename) as fin:
                self.align = fin.read()
        else:
            self.align = nw.nw(self.awd_text, self.wav2vec_text)
            with open(self.align_filename, 'w') as fout:
                fout.write(self.align)


        
    
