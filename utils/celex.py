vocab_filename = '/vol/bigdata/corpora/CELEX/DUTCH/DOL/DOL.CD'
readme_filename = '/vol/bigdata/corpora/CELEX/DUTCH/DOL/README'


class Celex:
	def __init__(self):
		self.vocab_filename = vocab_filename
		self.readme_filename = readme_filename
		self.vocab_str= open(vocab_filename).read()
		self._make_vocab()

	def _make_vocab(self):
		self.vocab = []
		for line in self.vocab_str.split('\n'):
			line = line.split('\\')
			if len(line) < 2: continue
			self.vocab.append(line[1])

	@property
	def readme(self):
		print(open(self.readme_filename))

	def in_celex(self,word):
		return word in self.vocab


def load_word_types():
	with open('../TRANSCRIPTION_ANALYSIS/word_types_in_celex') as fin:
		return fin.read().split('\n')

def load_recording_coverage():
	with open('../TRANSCRIPTION_ANALYSIS/coverage') as fin:
		coverage = fin.read().split('\n')
		coverage = list(map(float,coverage))
	return coverage
