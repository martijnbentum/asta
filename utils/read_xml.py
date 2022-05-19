from lxml import etree


def tag_to_element(tag,xml):
	'''extract a specific element for xml object'''
	temp = list(xml.iter('{*}' + tag))
	if len(temp) == 0: return None
	if len(temp) > 1: print('found more than one elements',tag,len(temp))
	return temp[0]
	
def points_to_avg_y(points):
	all_y = []
	for xy in points.split(' '):
		x,y = xy.split(',')
		all_y.append(float(y))
	return int(sum(all_y) / len(all_y))

def points_to_left_x(points):
	return int(points.split(' ')[0].split(',')[0])

def _get_transcription_from_textline(textline):
	textequiv = tag_to_element('TextEquiv',textline)
	uc = tag_to_element('Unicode',textequiv)
	transcription = uc.text
	conf = textequiv.get('conf')
	baseline= tag_to_element('Baseline',textline)
	points = baseline.get('points')
	y = points_to_y(points)
	x = points_to_left_x(points)
	try: conf = round(float(conf),4)
	except:pass
	return transcription, conf, x, y

def extract_transcription_from_xml(filename):
	xml = etree.fromstring(open(filename).read())
	transcription = []
	for x in xml.iter('{*}TextLine'):
			line = _get_transcription_from_textline(x)
			transcription.append(line)
	return transcription 
