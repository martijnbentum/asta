import regex as re
import string

def remove_speaker_identifier(line):
	'''removes the speaker identifier at the start of the line:
	'A: says hello' 			-> 			'says hello'
	' b: says bye' 				-> 			'says bye'

	^  		start of line
	(\s+)? 	one or more optional whitespaces
	. 		any non whitespace character
	: 		the colon character
	'''
	return re.sub('^(\s+)?.(\s+)?:(\s+)?','',line)


def remove_punctuation(line):
	punctuation = string.punctuation.replace("'",'')
	output = ''
	for char in punctuation:
		line = re.sub('(\s+)?\\'+char +'(\s+)?',' ',line)
	line = re.sub(" ' ",' ',line)
	if line:
		line = re.sub('\s+',' ',line)
	line = line.strip()
	return line


def clean_simple(text):
	text = remove_speaker_identifier(text)
	return remove_punctuation(text)
		

