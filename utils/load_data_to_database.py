from . import read_tsv
from . import read_kloeke
from . import make_name_lists as mnl
# from django.core.exceptions import DoesNotExist
from texts.models import Country, Province, Location, Recording, Recordingtype
from texts.models import Sex, Transcription, Transcriptiontype, Ocr


def load_province(province_to_country = None):
	if not province_to_country:
		_ , province_to_country = mnl.make_province_list()
	for province_name, country_name in province_to_country.items():
		country = Country.objects.get(name = country_name)
		try: Province.objects.get(name = province_name)
		except Province.DoesNotExist:
			print('creating province:',province_name, country.name)
			province = Province(name = province_name,country=country)
			province.save()
		else:print(province_name,country.name,'already exists')
		

def load_country():
	for name in 'Netherlands,Belgium,Germany'.split(','):
		try: Country.objects.get(name = name)
		except Country.DoesNotExist:
			print('creating country',name)
			c = Country(name=name)
			c.save()
		else:print(name,'already exists')


def load_location():
	kloeke = mnl.make_city_list_kloeke()
	for x in kloeke:
		try: Location.objects.get(kloeke = x['kloeke'])
		except: 
			print('creating location with kloeke',x['kloeke'])
			if ',' in x['province']: pname = x['province'].split(',')[0]
			else: pname = x['province']
			province = Province.objects.get(name =pname)
			country= Country.objects.get(name =x['country']) 
			location = Location(name = x['name'],
				alternative_names=x['alternative_names'],
				kloeke=x['kloeke'],
				latitude=x['latitude'],
				longitude=x['longitude'],
				province=province,
				country=country)
			location.save()
		else:print('kloeke location:',x['kloeke'],'already exists')

def load_recording_type(soundbites_metadata=None):
	rt_names = mnl.make_recording_type_list(soundbites_metadata)
	for name in rt_names:
		try: Recordingtype.objects.get(name = name)
		except Recordingtype.DoesNotExist:
			print('creating recording type:',name)
			rt = Recordingtype(name = name)
			rt.save()
		else: print('recording type:',name,'already exists')

def load_sex():
	for name in 'male,female,both'.split(','):
		try: Sex.objects.get(name = name)
		except Sex.DoesNotExist:
			print('creating sex',name)
			s = Sex(name=name)
			s.save()
		else:print(name,'already exists')

def get_locations(kloeke):
	locations = []
	if ',' in kloeke:
		for kc in kloeke.split(','):
			locations.append(Location.objects.get(kloeke = kc))
	else: locations = [ Location.objects.get(kloeke = kloeke) ]
	return locations

def get_recording_types(recording_types):
	if recording_types == '': return []
	output= []
	if ',' in recording_types:
		for rc in recording_types.split(','):
			output.append(Recordingtype.objects.get(name= rc))
	else: output= [ Recordingtype.objects.get(name= recording_types) ]
	return output

def make_location_str(line):
	column_names = 'country,province,city,kloekecode,area'.split(',')
	o = []
	for column_name in column_names:
		o.append(line[column_name])
	return '\t'.join(o)
		

def load_recording(soundbites_metadata):
	if not soundbites_metadata: 
		soundbites_metadata, _ = read_tsv.soundbites_to_metadata()
	for x in soundbites_metadata:
		try: Recording.objects.get(record_id= x['record_id'])
		except:
			print('creating recording:',x['record_id'])
			locations = get_locations(x['kloekecode'])
			rts = get_recording_types(x['recording_type'])
			if not x['sex']: sex = None
			elif ',' in x['sex']: sex = Sex.objects.get(name ='both')
			else: sex = Sex.objects.get(name = x['sex'])
			country = Country.objects.get(name=x['country'])
			if not ',' in x['province']:
				province= Province.objects.get(name=x['province'])
			else: province = None
			if x['recording_date']: recording_date= x['recording_date']
			else: recording_date = None
			if not x['year_of_birth']: year_of_birth = None
			else: year_of_birth = x['year_of_birth']
			if not x['age']: age= None
			else: age = x['age']
			if not x['id']:landsdb_id = None
			else: landsdb_id = x['id']

			recording = Recording(
				landsdb_id = landsdb_id,
				record_id = x['record_id'],
				ocr_transcription_available = x['ocr_transcription_available'],
				location_str= make_location_str(x),
				country = country,
				province = province,
				area = x['area'],
				soundbites_info = x['soundbites_info'],
				mp3_url = x['mp3_url'],
				wav_filename= x['wav_filename'],
				original_audio_filename= x['original_audio_filename'],
				recording_date_str= x['recording_date_str'],
				recording_date= recording_date,
				duration_str= x['duration_str'],
				duration= x['duration'],
				sex = sex,
				year_of_birth = age,
				age = age,
				recording_type_dutch= x['recording_type_description_dutch'],
			)
			recording.save()
			for recording_type in rts:
				recording.recording_types.add(recording_type) 
			for location in locations:
				recording.locations.add(location)
		else:print(x['record_id'],'already exists')
			
	
def load_transcriptiontype():
	for name in 'asr,ocr,human'.split(','):
		try: Transcriptiontype.objects.get(name = name)
		except Transcriptiontype.DoesNotExist:
			print('creating transcription type',name)
			tt = Transcriptiontype(name=name)
			tt.save()
		else:print(name,'already exists')

def load_ocr(ocr_list = None):
	if not ocr_list: ocr_list = mnl.make_ocr_list()
	for line in ocr_list:
		try: Ocr.objects.get(ocr_filename = line['ocr_filename'])
		except Ocr.DoesNotExist:
			print('creating ocr:',line['ocr_filename'])
			record_id = int(line['record_id'])
			recording = Recording.objects.get(record_id = record_id)
			ocr = Ocr(
				ocr_filename = line['ocr_filename'],
				image_filename = line['ocr_image_filename'],
				page_number = line['page_id'],
				page_width = line['page_width'],
				page_height = line['page_height'],
				recording = recording
			)
			ocr.save()
		else:print(ocr_filename, 'already exists')

def load_transcription(transcriptions=None):
	if not transcriptions:
		transcriptions = read_tsv.handle_new_transcription_file()
	tt = Transcriptiontype.objects.get(name = 'ocr')
	d = read_tsv.load_line_id_to_word_conf_list_dict()
	for line in transcriptions:
		try: Transcription.objects.get(id_name = line['ocr_line_id'])
		except Transcription.DoesNotExist:
			print('creating transcription:', line['ocr_line_id'])
			ocr = Ocr.objects.get(ocr_filename=line['ocr_filename'],
				page_number = line['page_id'])
			recording = Recording.objects.get(record_id=line['record_id'])
			tsv_word_info = d[line['ocr_line_id']]
			Transcription(
				id_name = line['ocr_line_id'],
				text = line['transcription'],
				words_tsv = tsv_word_info['words'],
				words_confidence_tsv = tsv_word_info['confs'],
				confidence = line['confidence'],
				transcription_type = tt,
				ocr = ocr,
				ocr_left_x = line['left_x'],
				ocr_right_x = line['right_x'],
				ocr_avg_y= line['avg_y'],
				recording = recording
			)
	else: print(line['ocr_line_id'],line['transcription'],'already exists')

