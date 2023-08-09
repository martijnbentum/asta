'''module to analyze bas webmaus output
https://clarin.phonetik.uni-muenchen.de/BASWebServices/interface/WebMAUSBasic
praat textgrid output is converted to table and read in with Table
the audio & orthographic transcription was chunked and then forced aligned
pipeline with asr / gp2 -> chunker -> maus
'''

class Table:
    '''object to read textgrid -> table MAUS output.'''
    def __init__(self,filename, align = None):
        self.filename = filename
        self._load_table()
        self.handled_align = False
        self.handle_align(align)

    def __repr__(self):
        m = 'Table: ' + str(len(self.chunks)) + ' '
        m += str(len(self.words)) + ' '
        m += self.filename
        return m
        
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
        for ocr_line in self.align.ocr_lines:
            sentence = Sentence(ocr_line = ocr_line)
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
    def __init__(self,sentence= '', ocr_line = None, strict = True):
        self.sentence = sentence
        self.ocr_line = ocr_line
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
    
