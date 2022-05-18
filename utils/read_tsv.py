from datetime import datetime
from .dicts import gender_dict,province_dict,country_dict
from .dicts import meta_data_header_to_english
import glob
import os
import subprocess

soundbites_filename = '../soundbites_utf8.csv'
meta_data_filename ='../landsdb-dialectdb.tsv'
transcriptions_filename = '../landsdb-dialectdb_transcriptions.tsv'
asta_audio = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/audio/'
asta_wav = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/wav/'
downloaded_mp3_dir = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/extra_mp3/'

def read_meta_data():
	# preprocessed meta data by Eric, matched with audio files
	f = meta_data_filename
	t = [x.split('\t') for x in open(f).read().split('\n')]
	header = t[0]
	data = t[1:]
	return header,data

def handle_meta_data():
	# preprocessed meta data by Eric, matched with audio files
	# creates a dictionary per record of meta data
	header, data = read_meta_data()
	output = []
	_ , soundbites_dict = make_soundbites_list_dict()
	for line in data:
		if not len(line) > 1: 
			print('line not long enough:',line,len(line))
			continue
		output.append(meta_data_line_to_dict(line, soundbites_dict))
	return output
		
		
def meta_data_line_to_dict(line, soundbites_dict = None):
	# create a dictionary for a record
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
	info = soundbites_dict[record_id]
	line_dict['province'] = province_dict[info['provincie']]
	line_dict['country'] = country_dict[info['land']]
	line_dict['city'] = info['plaatsnaam']
	line_dict['soundbites_info'] = '\t'.join(info.values())


def recording_type2tags(rt):
	if rt in recording_type_dict.keys(): return recording_type_dict[rt].split(',')
	if rt == '': return ''
	print('this recording type is not in the dict:',[rt],'setting to none')
	return ''

def date2datetime(str_date):
	if not str_date or str_date == 'onbekend': return ''
	if str_date.endswith('-00-00'): str_date = str_date.replace('00-00','01-01')
	if str_date.endswith('-00'): str_date = str_date.replace('-00','-01')
	return datetime.strptime(str_date,'%Y-%m-%d')

def clock2seconds(clock):
	clock = clock.split(':')
	if len(clock) != 3:
		print(clock,'unexpected format for a duration, setting to none')
		return None
	hours,minutes,seconds = map(int,clock)
	duration = hours * 3600 + minutes * 60 + seconds
	return duration


def load_mp3_wav_fn():
	f = '../mp3_wav_filenames'
	return [x.split('\t') for x in open(f).read().split('\n')]


def mp3_to_wav(mp3_filename, mp3_wav_file = None, return_mp3_filename= False):
	if not mp3_wav_file: mp3_wav_file = load_mp3_wav_fn()
	for line in mp3_wav_file:
		mp3, wav = line
		if mp3.lower().endswith(mp3_filename.lower()): 
			if return_mp3_filename: return wav,mp3
			else: return wav
	if return_mp3_filename: return '',''
	return ''
	

def read_soundbites():
	f = soundbites_filename
	t = [x.split('","') for x in open(f).read().split('\n') if x] 
	header = [x.strip('"') for x in t[0]]
	data = [x for x in t[1:] if len(x)>1 ]
	print('read:',len(data),'out of:',len(t)-1,'possible lines')
	return header, data

def make_soundbites_list_dict():
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
	if not soundbites_dict: 
		soundbites_list, soundbites_dict = make_soundbites_list_dict()
	else: soundbites_list = None
	record_id = meta['record_id']
	if record_id in soundbites_dict.keys(): return soundbites_dict[record_id]
	return {}

def load_soundbites_to_audio_filenames():
	t = open('../soundbites_id_to_audiofilenames').read().split('\n')
	t = [x.split('\t') for x in t if x]
	return t
	
def _soundbites_to_audio_filenames(soundbites_list = None, save = False):
	'''link a soundbites line to the audio filename via the meertens url
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

def _match_start_number_mp3_file(filename,fn):
	number = filename.split('/')[-1][:2]
	for f in fn:
		name = f.split('/')[-1]
		if number == name[:2]: 
			wav = mp3_to_wav(f)
			return filename,f,wav,fn 
	return False, False, False,False

def _fuzzy_match_not_found_mp3_file(filename):
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
			return filename,f, wav,fn
	ok, f1, wav1, fn1 = _match_start_number_mp3_file(filename,fn)
	if ok: return filename,f1,wav1,fn1
	print('---')
	for f in fn:
		fm = f.replace(asta_audio,'')
		fm = fm.lower().replace(' ','_').replace('.aif','')
		sfolder = '/'.join(fm.split('/')[:-1]) + '/'
		name = fm.split('/')[-1].replace('-','_')
		fm = sfolder + name
		print('fi:',[filename],'\nf :',[f],'\nfm:',[fm], filename in fm)
	return filename,False,False,fn

def download_mp3_from_url(url, goal_dir = downloaded_mp3_dir):
	goal_name = goal_dir + url.split('audio/soundbites/')[-1].replace('/','__')
	name = url.split('/')[-1]
	os.system('wget ' + url)
	os.system('mv '+name+' '+goal_name)


def _update_soundbites_to_audio_filenames():
	''' some audio filenames were missed because of mismatches between
	url name and name in /vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/audio
	'''
	t = load_soundbites_to_audio_filenames()
	not_found = [x for x in t if not x[3] or not x[4]] 
	matches = []
	for line in not_found:
		m = _fuzzy_match_not_found_mp3_file(line[1])
		matches.append([m[:-1],line[0]])
		if not m[2]: download_mp3_from_url(line[0])
	return t, not_found,matches

def url_to_original_audio_url_filename(url):
	'''retrieve audiofilename based on url.'''
	output = {}
	s = subprocess.check_output(['curl',url]).decode()
	output['mp3_url'] = s.split('href="')[-1].split('>')[0].strip('"')
	output['mp3_filename'] = output['mp3_url'].split('audio/soundbites/')[-1]
	return output

def read_transcriptions():
	f = transcriptions_filename
	t = [x.split('\t') for x in open(f).read().split('\n') if x]
	header = t[0]
	data = t[1:]
	return header, data

def handle_transcriptions():
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


