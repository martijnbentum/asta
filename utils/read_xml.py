from lxml import etree


def tag_to_element(tag,xml):
	'''extract a specific element for xml object'''
	temp = list(xml.iter('{*}' + tag))
	if len(temp) == 0: return None
	# if len(temp) > 1: print('found more than one elements',tag,len(temp))
	return temp[0]
	
def points_to_avg_y(points):
	all_y = []
	for xy in points.split(' '):
		x,y = xy.split(',')
		all_y.append(float(y))
	return int(sum(all_y) / len(all_y))

def points_to_left_x(points):
	return int(points.split(' ')[0].split(',')[0])

def points_to_right_x(points):
	return int(points.split(' ')[1].split(',')[0])

def _get_transcription_from_textline(textline):
	i= textline.get('id')
	textequiv = tag_to_element('TextEquiv',textline)
	uc = tag_to_element('Unicode',textequiv)
	transcription = uc.text
	if not transcription: return False
	conf = textequiv.get('conf')
	baseline= tag_to_element('Baseline',textline)
	points = baseline.get('points')
	avg_y = points_to_avg_y(points)
	left_x = points_to_left_x(points)
	right_x = points_to_right_x(points)
	try: conf = round(float(conf),4)
	except:pass
	d = {'ocr_line_id':i,'transcription':transcription, 'confidence':conf}
	d.update({'left_x':left_x, 'right_x':right_x, 'avg_y':avg_y})
	return d

def extract_transcription_from_xml(filename):
	xml = etree.fromstring(open(filename).read())
	transcription = []
	for x in xml.iter('{*}TextLine'):
		line = _get_transcription_from_textline(x)
		if not line: continue
		transcription.append(line)
	transcription = sorted(transcription, key = lambda x:x['avg_y'])
	return transcription 


def xml_filename_to_image_width_height(filename):
	xml = etree.fromstring(open(filename).read())
	page = tag_to_element('Page',xml)
	try: width = int(page.get('imageWidth'))
	except TypeError: width = None
	try: height= int(page.get('imageHeigth'))
	except TypeError: height = None	
	return width, height

def word_to_conf(word):
	te = tag_to_element('TextEquiv',word)
	if te == None: return ''
	conf = te.get('conf')
	if conf == None: return ''
	return conf

def word_to_text(word):
	te = tag_to_element('TextEquiv',word)
	if te == None: return ''
	uc = tag_to_element('Unicode',te)
	if uc == None: return ''
	text = uc.text
	if text == None: return ''
	return text

def id_to_textline(filename,id_name):
	xml = etree.fromstring(open(filename).read())
	for x in xml.iter('{*}TextLine'):
		if x.get('id') == id_name: return x
	return None

def textline_id_to_words(filename,id_name):
	textline = id_to_textline(filename,id_name)
	if textline == None:return None
	words = list(textline.iter('{*}Word'))
	return words

def transcription_line_to_word_conf_lists(line):
	words = textline_id_to_words(line['ocr_filename'],line['ocr_line_id'])
	word_texts = [word_to_text(w) for w in words]
	confs = [word_to_conf(w) for w in words]
	if word_texts: word_texts = '\t'.join(word_texts)
	else: word_texts = ''
	if confs: confs = '\t'.join(confs)
	else: confs =''
	return word_texts, confs
