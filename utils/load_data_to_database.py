from . import read_tsv
from . import read_kloeke
from . import make_name_lists as mnl
# from django.core.exceptions import DoesNotExist
from texts.models import Country, Province, Location, Recording, Recordingtype
from texts.models import Sex


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
	for name in 'male,female'.split(','):
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



def load_recording(soundbites_metadata):
	if not soundbites_metadata: 
		soundbites_metadata, _ = read_tsv.soundbites_to_metadata()
	for x in soundbites_to_metadata:
		try: Recording.objects.get(record_id= x['record_id'])
		except:
			print('creating recording:',x['record_id'])
			
		
	
	pass
	landsdb_id = models.PositiveIntegerField(null=True,blank=True) 
	record_id = models.PositiveIntegerField(null=True,blank=True) 
	ocr_transcription_available = models.BooleanField(default = False)
	locations= models.ManyToManyField(Location, blank=True)
	area = models.CharField(max_length=100,default='')
	soundbites_info = models.TextField(default='')
	mp3_url = models.CharField(max_length=300,default='')
	wav_filename = models.CharField(max_length=300,default='')
	original_audio_filename = models.CharField(max_length=300,default='')
	recording_date_str = models.CharField(max_length=30, default='')
	recording_date = models.DateTimeField()
	duration = models.PositiveIntegerField(null=True,blank=True) 
	sex = models.ForeignKey(Sex, **dargs)
	year_of_birth = models.PositiveIntegerField(null=True,blank=True) 
	age = models.PositiveIntegerField(null=True,blank=True) 
	recording_type_dutch = models.CharField(max_length = 100, default = '')
	recording_types = models.ManyToManyField(Recordingtype,blank=True)
	
	

	
