from datetime import datetime
from . import convert_to_wav 
from .dicts import gender_dict,province_dict,country_dict
from .dicts import meta_data_header_to_english, recording_type_dict
import glob
from lxml import etree
import os
from . import read_xml 
import subprocess

soundbites_filename = '../soundbites_utf8.csv'
meta_data_filename ='../landsdb-dialectdb.tsv'
transcriptions_filename = '../landsdb-dialectdb_transcriptions.tsv'
asta_audio = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/audio/'
asta_wav = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/wav/'
downloaded_mp3_dir = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/extra_mp3/'
ocr_dir = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/transcriptions/ocr_xml/'

def read_meta_data():
	'''
	preprocessed meta data by Eric, matched with audio files
	'''
	f = meta_data_filename
	t = [x.split('\t') for x in open(f).read().split('\n')]
	header = t[0]
	data = t[1:]
	return header,data

def handle_meta_data():
	'''
	preprocessed meta data by Eric, matched with audio files
	creates a dictionary per record of meta data
	'''
	header, data = read_meta_data()
	output = []
	_ , soundbites_dict = make_soundbites_list_dict()
	for line in data:
		if not len(line) > 1: continue
		output.append(meta_data_line_to_dict(line, soundbites_dict))
	return output
		
		
def meta_data_line_to_dict(line, soundbites_dict = None):
	'''
	create a dictionary for a record
	'''
	if not soundbites_dict: _, soundbites_dict = make_soundbites_list_dict()
	o = {}
	mp3_wav = load_mp3_wav_fn()
	for i, name in enumerate(meta_data_header_to_english.values()):
		item = line[i]
		if name == 'original_audio_filename':
			wav = mp3_to_wav(item, mp3_wav)
			o['wav_filename'] = wav
		if name in ['id','record_id','age','date_of_birth']: 
			if not item: item = ''
			else: item = int(item)
		if name == 'sex': item = gender_dict[item]
		if name == 'recording_date': 
			o['recording_date_str'] = item
			item = date2datetime(item)
		if name == 'duration': 
			o['duration_str'] = item
			item = clock2seconds(item)
		if name == 'recording_type': 
			o['recording_type_description_dutch'] = item
			item = recording_type2tags(item) 
		o[name] =  item
		if name == 'record_id': add_soundbites_info(item,o, soundbites_dict)
	return o

def add_soundbites_info(record_id, line_dict, soundbites_dict):
	''' 
	add the metadata in the soundbites file to the meta_data from 
	the landsdb
	'''
	info = soundbites_dict[record_id]
	line_dict['province'] = province_dict[info['provincie']]
	line_dict['country'] = country_dict[info['land']]
	line_dict['city'] = info['plaatsnaam']
	line_dict['soundbites_info'] = '\t'.join(info.values())


def recording_type2tags(rt):
	''' 
	transelate recording type into English tags.
	'''
	if rt in recording_type_dict.keys(): return recording_type_dict[rt].split(',')
	if rt == '': return ''
	print('this recording type is not in the dict:',[rt],'setting to none')
	return ''

def date2datetime(str_date):
	'''
	map str date to datetime object
	'''
	if not str_date or str_date == 'onbekend': return ''
	if str_date.endswith('-00-00'): str_date = str_date.replace('00-00','01-01')
	if str_date.endswith('-00'): str_date = str_date.replace('-00','-01')
	str_date = str_date.replace('-00-','-01-')
	return datetime.strptime(str_date,'%Y-%m-%d')

def clock2seconds(clock):
	'''
	map str with format 00:01:23 to 83 an integer representing duration in sec
	'''
	clock = clock.split(':')
	if len(clock) != 3:
		print(clock,'unexpected format for a duration, setting to none')
		return None
	hours,minutes,seconds = map(int,clock)
	duration = hours * 3600 + minutes * 60 + seconds
	return duration


def load_mp3_wav_fn():
	'''
	load the text file that maps mp3 filename to wav filenames
	'''
	f = '../mp3_wav_filenames'
	return [x.split('\t') for x in open(f).read().split('\n')]


def mp3_to_wav(mp3_filename, mp3_wav_file = None, return_mp3_filename= False):
	'''
	map a given mp3 filename to a wav filename based on the mp3_wav_filenames
	'''
	if not mp3_wav_file: mp3_wav_file = load_mp3_wav_fn()
	for line in mp3_wav_file:
		mp3, wav = line
		if mp3.lower().endswith(mp3_filename.lower()): 
			if return_mp3_filename: return wav,mp3
			else: return wav
	if return_mp3_filename: return '',''
	return ''
	

def read_soundbites():
	'''
	read the metadata soundbites file
	'''
	f = soundbites_filename
	t = [x.split('","') for x in open(f).read().split('\n') if x] 
	header = [x.strip('"') for x in t[0]]
	data = [x for x in t[1:] if len(x)>1 ]
	print('read:',len(data),'out of:',len(t)-1,'possible lines')
	return header, data

def make_soundbites_list_dict():
	'''
	make a list and a dict (mapping a id to a line in the metadata) of 
	the soundbites metadata file
	'''
	header,data = read_soundbites()
	output = []
	output_dict = {}
	for line in data:
		line_dict = {}
		for i,column_name in enumerate(header):
			if column_name == 'id': identifier = int(line[i].strip('"'))
			line_dict[column_name] = line[i].strip('"')
		output.append(line_dict)
		output_dict[identifier] = line_dict
	return output, output_dict

def meta_to_soundbite(meta, soundbites_dict = None):
	'''
	map a metadata record from the landsdb database to the soundbites metadata 
	'''
	if not soundbites_dict: 
		soundbites_list, soundbites_dict = make_soundbites_list_dict()
	else: soundbites_list = None
	record_id = meta['record_id']
	if record_id in soundbites_dict.keys(): return soundbites_dict[record_id]
	return {}

def load_soundbites_to_audio_filenames():
	'''
	loads a file that maps the soundbites id to the corresponding audiofilename
	'''
	t = open('../soundbites_id_to_audiofilenames').read().split('\n')
	t = [x.split('\t') for x in t if x]
	return t
	
def _make_soundbites_to_audio_filenames(soundbites_list = None, save = False):
	'''
	use load_soundbites_to_audio_filenames to acces this info
	link a soundbites line to the audio filename via the meertens url
	link that audio filename to the converted wav audio filename
	only use this function if the file ../soundbites_id_to_audiofilenames
	does not exists, uses curl requests to audio filenames -> time consuming
	'''
	if not soundbites_list: soundbites_list, _ = make_soundbites_list_dict()
	mp3_wav = load_mp3_wav_fn()
	output = []
	for line in soundbites_list:
		url = line['audio']
		if not url: continue
		o = url_to_original_audio_url_filename(url)
		o['id'] =line['id']
		mp3_filename = o['mp3_filename']
		wav, mp3 = mp3_to_wav(mp3_filename, mp3_wav, return_mp3_filename = True)
		o['original_audio_filename'] = mp3
		o['wav_filename'] = wav
		output.append(o)
	if save:
		header = '\t'.join(o.keys())
		t = [header]
		t.extend(['\t'.join(line.values()) for line in output])
		with open('../soundbites_id_to_audiofilenames','w') as fout:
			fout.write('\n'.join(t))
	return output

def _match_start_number_mp3_file(d,fn):
	'''
	match mp3 filename (filename) to a filename from a set of filenames (fn) 
	that mismatch on spelling, but can match on the number (first 2 characters)
	'''
	filename = d['mp3_filename']
	number = filename.split('/')[-1][:2]
	for f in fn:
		name = f.split('/')[-1]
		if number == name[:2]: 
			wav = mp3_to_wav(f)
			d['original_audio_filename'] =f
			d['wav_filename'] = wav
			return d, True
	return d, False

def _fuzzy_match_not_found_mp3_file(d):
	'''
	match an mp3 filename (retrieved from meertens url) to an audio file
	stored on ponyland, matching audio to soundbites metadata	
	'''
	filename = d['mp3_filename']
	folder = asta_audio + '/'.join(filename.split('/')[:-1]) + '/'
	fn = glob.glob(folder + '*.mp3')
	for f in fn:
		fm = f.replace(asta_audio,'').replace("'",'_')
		fm = fm.lower().replace(' ','_').replace('.aif','')
		sfolder = '/'.join(fm.split('/')[:-1]) + '/'
		name = fm.split('/')[-1].replace('-','_')
		fm = folder + name
		if filename in fm: 
			wav = mp3_to_wav(f)
			d['original_audio_filename'] = f
			d['wav_filename'] = wav
			return d
	d, ok = _match_start_number_mp3_file(d,fn)
	if ok: return d
	# this is only for debugging should be removed:
	print('---')
	for f in fn:
		fm = f.replace(asta_audio,'')
		fm = fm.lower().replace(' ','_').replace('.aif','')
		sfolder = '/'.join(fm.split('/')[:-1]) + '/'
		name = fm.split('/')[-1].replace('-','_')
		fm = sfolder + name
		print('fi:',[filename],'\nf :',[f],'\nfm:',[fm], filename in fm)
	return d

def download_mp3_from_url(url, goal_dir = downloaded_mp3_dir, download= False):
	'''
	download mp3 from url (meertens) to get missing audio that is listed in
	soundbites metadata file
	'''
	goal_name = goal_dir + url.split('audio/soundbites/')[-1].replace('/','__')
	name = url.split('/')[-1]
	if download:
		print('downloading')
		os.system('wget ' + url)
		os.system('mv '+name+' '+goal_name)
	return goal_name

def _make_soundbites_to_audiofilename_dict(header,line):
	d = {}
	for key,value in zip(header,line):
		d[key] = value
	return d

def _update_soundbites_to_audio_filenames(save = False,download_mp3_files = False):
	''' some audio filenames were missed because of mismatches between
	url name and name in /vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/audio
	'''
	t = load_soundbites_to_audio_filenames()
	header = t[0]
	not_found = [[i,x] for i,x in enumerate(t) if not x[3] or not x[4]] 
	matches = []
	for index, line in not_found:
		d = _make_soundbites_to_audiofilename_dict(header,line)
		d = _fuzzy_match_not_found_mp3_file(d)
		if not d['wav_filename']: 
			mp3_filename=download_mp3_from_url(line[0],
				download=download_mp3_files)
			wav_filename = convert_to_wav.make_wav_name(mp3_filename,
				org_directory= convert_to_wav.extra_mp3)
			d['original_audio_filename'] = mp3_filename
			d['wav_filename'] = wav_filename
		matches.append([d,index])
		t[index] = list(d.values())
	with open('../soundbites_id_to_audiofilenames','w') as fout:
		fout.write('\n'.join(['\t'.join(x) for x in t]))
	return t, not_found,matches

def url_to_original_audio_url_filename(url):
	'''retrieve audiofilename based on url.'''
	output = {}
	s = subprocess.check_output(['curl',url]).decode()
	output['mp3_url'] = s.split('href="')[-1].split('>')[0].strip('"')
	output['mp3_filename'] = output['mp3_url'].split('audio/soundbites/')[-1]
	return output

def read_transcriptions():
	'''
	read transcriptions tsv file, datadumb from the landsdb database
	'''
	f = transcriptions_filename
	t = [x.split('\t') for x in open(f).read().split('\n') if x]
	header = t[0]
	data = t[1:]
	return header, data

def handle_transcriptions():
	'''
	create a list of dictionaries from the transcription file
	'''
	header, data = read_transcriptions()
	output = []
	for line in data:
		line_dict = {}
		for i,column_name in enumerate(header):
			item = line[i]
			if column_name in ['id', 'recid', 'subid']: item = int(item)
			if column_name == 'recid': column_name = 'record_id'
			if column_name == 'subid': column_name = 'page_id'
			if column_name == 'scanfilepath': column_name = 'ocr_image_filename'
			if column_name == 'ocr': column_name = 'transcription'
			line_dict[column_name] = item
		output.append(line_dict)
	return output

def ocr_image_filename_to_xml_file(filename):
	prefix, name = filename.split('.')[0].split('/')[-2:]
	o = {}
	o['filename'] = prefix + '_' + name + '.xml'
	o['path'] = ocr_dir + o['filename']
	o['isfile'] = os.path.isfile(o['path'])
	return o
	
def save_list_of_dicts(ld, filename):
	header = '\t'.join(list(ld[0].keys()))
	o = [header]
	o.extend(['\t'.join(list(map(str,line.values()))) for line in ld])
	with open(filename,'w') as fout:
		fout.write('\n'.join(o))

def make_new_transcription_file(save = False):
	'''make a tsv file with one ocr transcription sentence per line.'''
	t = handle_transcriptions()
	output = []
	not_found = []
	n = len(t)
	for i,line in enumerate(t):
		del line['transcription']
		del line['id']
		fd = ocr_image_filename_to_xml_file(line['ocr_image_filename'])	
		if not fd['isfile']:
			not_found.append(d)
			continue
		perc = round(i/n*100,2)
		if i % 50 == 0: print(line['ocr_image_filename'],perc)
		line['ocr_filename'] = fd['path']
		d = read_xml.extract_transcription_from_xml(fd['path'])	
		for sentence in d:
			sentence.update(line)
			output.append(sentence)
	if save: save_list_of_dicts(output,'../ocr_transcription_sentences')
	return output,not_found

def make_record_ids_list_with_transcription():
	'''create a list of integers of record ids that have an ocr transcription
	'''
	d = handle_meta_data()
	record_ids=[str(l['record_id']) for l in d]
	with open('../record_ids_with_transcription','w') as fout:
		fout.write('\n'.join(record_ids))
	return record_ids

def _add_wav_mp3_filename_to_soundbite(line_dict):
	'''
	add audio filenames to the metadata format of soundbites line
	without a transcription
	'''
	t = load_soundbites_to_audio_filenames()
	header = t[0]
	lines = t[1:]
	for line in lines:
		d = _make_soundbites_to_audiofilename_dict(header,line)
		if int(d['id']) == line_dict['record_id']:
			line_dict['mp3_url'] = d['mp3_url']
			line_dict['wav_fileame'] = d['wav_filename']
			line_dict['original_audio_filename'] = d['original_audio_filename']
			return True
	return False



def soundbites_to_metadata():
	'''map soundbites line to metadata format
	for each audio that is transcribed a metadata line is created
	in handle_meta_data, create lines in the same format for audio files
	without transcription but with metadata in the soundbites file
	'''
	o,od = make_soundbites_list_dict()
	output,error = [],[]
	t = open('../record_ids_with_transcription').read().split('\n')
	record_ids_with_transcription = list(map(int,t))
	d = handle_meta_data()
	for record_id, value in od.items():
		idn = ''
		ocr_transcription_available = False
		if record_id in record_ids_with_transcription:
			d_line = [x for x in d if x['record_id'] == record_id][0]
			idn = d_line['id']
			ocr_transcription_available = True
		line_dict = {'id':idn,'record_id':record_id}
		line_dict['ocr_transcription_available'] = ocr_transcription_available
		add_soundbites_info(record_id,line_dict, od)
		ok = _add_wav_mp3_filename_to_soundbite(line_dict)
		if not ok:
			error.append(line_dict)
			continue
		line_dict['kloekecode'] = value['kloeke']
		line_dict['area'] = value['streek']
		line_dict['recording_date_str'] = value['opnamedatum']
		line_dict['recording_date'] = date2datetime(value['opnamedatum'])
		line_dict['duration_str'] = value['tijd']
		line_dict['duration'] = clock2seconds(value['tijd'])
		line_dict['sex'] = gender_dict[value['geslacht']]
		if value['geb_jaar'] == '':year = ''
		else: year= int(value['geb_jaar'])
		line_dict['year_of_birth'] = year
		if value['leeftijd'] == '': age = ''
		else:age = int(value['leeftijd'] )
		line_dict['age'] = age
		line_dict['recording_type_description_dutch']= value['opnameaard']
		line_dict['recording_type']= recording_type_dict[value['opnameaard']]
		output.append(line_dict)
	return output,error


