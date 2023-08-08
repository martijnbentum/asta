class Table:
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
        self.sentences = []
        if not self.align: return
        for ocr_line in self.align.ocr_lines:
            sentence = Sentence(ocr_line = ocr_line)
            self.sentences.append(sentence)
        
    def _match_sentences_with_table_words(self):
        for i,sentence in enumerate(self.sentences):
            try:sentence.collect_words(self)
            except:
                sentence.ok = False

    def handle_align(self,align):
        self.align = align
        self.word_index = 0
        self._make_sentences()
        self._match_sentences_with_table_words()
        

class Chunk:
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
        self.words.append(word)

            

class Word:
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
        self.ok = False
        m = 'mismatch at table index '
        m += str(table.word_index)+' sentence ' + str(index)
        m += ' ' + word
        if self.strict:
            raise ValueError(m)
        else:
            print(m)

    def collect_words(self,table):
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
        annotations = self.ocr_line.annotations
        if annotations:
            self.alignment = self.ocr_line.annotations[0].alignment
        else:
            self.alignment = None
        


def word_is_integer(word):
    try: int(word)
    except: return False
    return True
            
        

        

    


def load_table(filename):
    with open(filename,encoding = 'utf16') as fin:
        table=[line.split('\t') for line in fin.read().split('\n')[1:] if line]
    d = get_tier_name_dict()
    for line in table:
        line[0] = float(line[0])
        line[1] = d[line[1]]
        line[-1] = float(line[-1])
    return table


def get_tier_name_dict():
    d = {
        'TRN': 'orthographic_chunk',
        'ORT-MAU': 'orthographic_word',
        'KAN-MAU': 'phoneme_word',
        'MAU': 'phoneme'
        }
    return d
    
