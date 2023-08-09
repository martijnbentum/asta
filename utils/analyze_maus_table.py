'''module to analyze bas webmaus output
https://clarin.phonetik.uni-muenchen.de/BASWebServices/interface/WebMAUSBasic
praat textgrid output is converted to table and read in with Table
the audio & orthographic transcription was chunked and then forced aligned
pipeline with asr / gp2 -> chunker -> maus
'''
import glob
from texts.models import Recording
import os 
import random
import string

def match_recordings_and_table_filenames(recordings,filenames):
    d = {}
    for recording in recordings:
        f = recording.wav_filename.split('/')[-1].replace('.wav','.Table')
        for filename in filenames:
            if f in filename: break
        d[filename] =recording
    return d

def make_all_tables(pks = [106,171,348,588,589]):
    r = Recording.objects.filter(pk__in = pks)
    fn = glob.glob('../fa/*.Table')
    d = match_recordings_and_table_filenames(r,fn)
    output = []
    for filename, recording in d.items():
        output.append(Table(filename, recording))
    return output
    

class Table:
    '''object to read textgrid -> table MAUS output.'''
    def __init__(self,filename, recording = None):
        self.filename = filename
        self._load_table()
        self.handled_align = False
        self.handle_align(recording.align)
        self.recording = recording
        self._set_info()

    def __repr__(self):
        m = 'Table: ' + str(len(self.chunks)) + ' '
        m += str(len(self.words)) + ' '
        m += self.filename
        return m

    def _set_info(self):
        self.wav_filename = ''
        self.directory = ''
        if self.recording:
            self.wav_filename = self.recording.wav_filename
            d = self.wav_filename.split('_')[-1].split('.')[0].lower()
            self.directory='../maus/'+d+'_r-'+str(self.recording.pk)+'/'
            if not os.path.isdir(self.directory): os.mkdir(self.directory)
            
        
    def _load_table(self):
        '''reads in the words and chunks in the table.
        words are only the orthographic words
        chunks are the parts of the audio / transcription
        it neede to be chunked because maus has a word limit of 5000
        to speed up processing
        '''
        self.table = load_table(self.filename)
        self.words = []
        self.chunks = []
        for line in self.table:
            if line[1] == 'orthographic_chunk':
                chunk = Chunk(line)
                self.chunks.append(chunk)
            if line[1] == 'orthographic_word': 
                word = Word(line, chunk)
                self.words.append(word)
                chunk.add_word(word)

    def _make_sentences(self):
        '''create sentences based on the ocr_lines in the align object
        these are the orthographic transcription lines
        the basic unit used to evaluate the wav2vec2 output
        '''
        self.sentences = []
        if not self.align: return
        for i,ocr_line in enumerate(self.align.ocr_lines):
            sentence = Sentence(ocr_line = ocr_line, index = i, table = self)
            self.sentences.append(sentence)
        
    def _match_sentences_with_table_words(self):
        '''the maus output is at word level collect all words that
        match with a sentence
        numbers are written out in the maus output
        so ignore words in the sentences that can be converted to int
        '''
        for i,sentence in enumerate(self.sentences):
            try:sentence.collect_words(self)
            except:
                sentence.ok = False

    def handle_align(self,align):
        '''the align object contain ocr-lines with annotations
        evaluating the alignment of wav2vec pipeline
        the ocr-lines are converted to sentence object and the 
        sentence object collects the words outputed from maus with 
        timing information.
        '''
        self.align = align
        self.word_index = 0
        self._make_sentences()
        self._match_sentences_with_table_words()

    @property
    def ok_sentences(self):
        if hasattr(self,'_ok_sentences'): return self._ok_sentences
        self._ok_sentences = [x for x in self.sentences if x.ok]
        return self._ok_sentences

    @property
    def sentences_with_alignment(self):
        if hasattr(self, '_annot_sentences'): return self._annot_sentences
        s = self.ok_sentences
        self._annot_sentences = [x for x in s if x.alignment]
        return self._annot_sentences

class Chunk:
    '''a part of the transcription (and audio) the whole audio / transcription
    to speed up forced alignment processing.
    this is part of the maus output on the TRN tier
    '''
    def __init__(self,line):
        self.line = line
        self.type = self.line[1]
        self.chunk = self.line[2]
        self.start_time = self.line[0]
        self.end_time = self.line[-1]
        self.duration = self.end_time - self.start_time
        self.words = []

    def __repr__(self):
        if len(self.chunk) > 63:
            chunk = self.chunk[:60] + '...'
        else: chunk = self.chunk
        m = 'Chunk: ' + chunk + ' ' + str(round(self.duration,3)) 
        m += ' nwords: ' + str(len(self.words))
        return m

    def add_word(self,word):
        '''collect the words form the word tier that are part of the chunk.'''
        self.words.append(word)

class Word:
    '''there is orthographic and phonemic tier in the maus output.
    type indicates the type.
    orthographic words are collected
    '''
    def __init__(self,line, chunk = None):
        self.line = line
        self.chunk = chunk
        self.type = self.line[1]
        self.word = self.line[2]
        self.start_time = self.line[0]
        self.end_time = self.line[-1]
        self.duration = self.end_time - self.start_time

    def __repr__(self):
        return 'Word: ' + self.word + ' ' + str(round(self.duration,3)) 

    def equal(self,other, verbose = False):
        '''check whether words are the same.'''
        if type(other) == type(self):
            other_word = other.word
        elif type(other) == str:
            other_word = other
        else:
            raise ValueError(other,'unknown type, should be string or Word')
        if self.word != other_word:
            print('other',[other_word],'not equal:',[self.word])
        return self.word == other_word

class Sentence:
    '''class to contain information of an ocr line
    the words in the sentence are used to collect words in the maus output
    integer words in the sentence should be ignored because maus writes out
    numbers in words
    '''
    def __init__(self,sentence= '', ocr_line = None, index = None,
        table = None, strict = True):
        self.sentence = sentence
        self.ocr_line = ocr_line
        self.index = index
        self.table = table
        self.strict = strict
        self.ok = True
        if ocr_line: self.sentence = ocr_line.ocr_text
        self.sentence_words = self.sentence.split(' ')
        self.nwords = len(self.sentence_words)
        self.words = []
        self.collected_words = False

    def __repr__(self):
        m = 'sentence: '+self.sentence + ' '
        m += 'ok: ' + str(self.ok) + ' '
        if hasattr(self,'duration'):
            m += str(self.duration)
        return m

    def __gt__(self,other):
        return self.nwords > other.nwords

    def _handle_error(self, table, index, word):
        '''show when the sentence and maus output are not aligned.'''
        self.ok = False
        m = 'mismatch at table index '
        m += str(table.word_index)+' sentence ' + str(index)
        m += ' ' + word
        if self.strict:
            raise ValueError(m)
        else:
            print(m)

    def collect_words(self,table):
        '''collect words from the table.
        the ocr lines from the align object are processed in order
        therefore each word in each sentence should match the next word
        in the table
        '''
        self.ok = True
        if self.collected_words: 
            raise ValueError('already collected words')
        for index,word in enumerate(self.sentence_words):
            table_word = table.words[table.word_index]
            if word_is_integer or table_word.equal(word):
                self.words.append(table_word)
                table.word_index += 1
            else: self._handle_error(table,index,word)
        self._set_times()
        self._set_alignment()

    def _set_times(self):
        self.start_time = self.words[0].start_time
        self.end_time = self.words[-1].end_time
        self.duration = round(self.end_time - self.start_time,3)

    def _set_alignment(self):
        '''set the alignment of the wav2vec annotations.'''
        annotations = self.ocr_line.annotations
        if annotations:
            self.alignment = self.ocr_line.annotations[0].alignment
        else:
            self.alignment = None

    @property
    def directory(self):
        if not self.ocr_line:
            print('sentence has no ocr line no directory available')
            return
        if not self.table:
            print('sentence has no table no directory available')
            return
        return self.table.directory
        
    @property
    def wav_filename(self): 
        if not self.directory: return
        f = self.directory
        f += get_ascii_start(self.sentence,6)
        f += '_r-' + str(self.table.recording.pk)
        f += '_s-' + str(self.index)
        f += '.wav'
        return f


def word_is_integer(word):
    '''check whether the word is a number.'''
    try: int(word)
    except: return False
    return True
            
def load_table(filename):
    '''load a maus output textgrid -> table file.'''
    with open(filename,encoding = 'utf16') as fin:
        table=[line.split('\t') for line in fin.read().split('\n')[1:] if line]
    d = get_tier_name_dict()
    for line in table:
        line[0] = float(line[0])
        line[1] = d[line[1]]
        line[-1] = float(line[-1])
    return table


def get_tier_name_dict():
    '''transelate maus tier names to readable tier names.'''
    d = {
        'TRN': 'orthographic_chunk',
        'ORT-MAU': 'orthographic_word',
        'KAN-MAU': 'phoneme_word',
        'MAU': 'phoneme'
        }
    return d

def sentences_to_alignment_dict(sentences):
    d = {}
    for sentence in sentences:
        a = sentence.alignment
        if a == 'middle_mismatch': continue
        if a not in d.keys(): d[a] = []
        d[a].append(sentence)
    for align in d.keys():
        d[align] = sorted(d[align],reverse = True)
    return d



def sentence_to_audio(sentence, overwrite = False):
    if not(sentence.wav_filename):
        print('sentence does not have wav_filename doing nothing')
        return
    if os.path.isfile(sentence.wav_filename) and not overwrite:
        print('sentence wav file already exists doing nothing')
        return
    cmd = 'sox ' + sentence.table.wav_filename + ' ' 
    cmd += sentence.wav_filename + ' trim ' 
    cmd += str(sentence.start_time)
    cmd += ' ' + str(sentence.duration)
    print('extracting audio')
    print(cmd)
    text_filename = sentence.wav_filename.replace('.wav','.txt')
    with open(text_filename,'w') as fout:
        fout.write(sentence.sentence)
    os.system(cmd)

        
def get_ascii_start(sentence,n):
    o = ''
    for char in sentence:
        if len(o) == n: break
        if char not in string.ascii_letters: continue
        o += char
    if len(o) == 0: o = string.ascii_letters[:n]
    return o

def filter_out_old_sentences(sentences):
    output = []
    for sentence in sentences:
        if os.path.isfile(sentence.wav_filename): continue
        output.append(sentence)
    return sentences
    
def select_sentences(sentences, n):
    sentences = filter_out_old_sentences(sentences)
    d = sentences_to_alignment_dict(sentences)
    output = []
    for alignment, sentences in d.items():
        if len(sentences) < n: 
            print(alignment,'has',len(sentences),'sentences')
            sample_size = len(sentences)
        else: sample_size = n
        if sample_size == 0:
            print('no more sentences for', alignment)
        output.extend(random.sample(sentences,sample_size))
    return output


def make_audio_text_for_select_sentences(all_tables = None, n = 20):
    if not all_tables: all_tables = make_all_tables()
    for table in all_tables:
        sentences = select_sentences(table.sentences_with_alignment, n = n)
        for sentence in sentences:
            sentence_to_audio(sentence)

    
    

        
    
