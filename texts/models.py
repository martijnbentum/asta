from django.db import models
import numpy as np
from utils.clean_text import clean_simple
import matplotlib.image as mpimg
from matplotlib import pyplot as plt
	

class Dialect(models.Model):
	'''Grouping for kloekecodes.'''
	name = models.CharField(max_length=100,default='')

	def __repr__(self):
		return self.name

class Recordingtype(models.Model):
	'''Type of speech recorded e.g conversation, song story.'''
	name = models.CharField(max_length=100,default='')

	def __repr__(self):
		return self.name

class Transcriptiontype(models.Model):
	'''Type of transcription ocr asr human.'''
	name = models.CharField(max_length=100,default='')

	def __repr__(self):
		return self.name

class Country(models.Model):
	'''country name Netherlands / Belgium / Germany'''
	name = models.CharField(max_length=100,default='')

	def __repr__(self):
		return self.name

class Province(models.Model):
	'''location name for province.'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	name = models.CharField(max_length=100,default='')
	country = models.ForeignKey(Country, **dargs)

	def __repr__(self):
		return self.name


class Sex(models.Model):
	'''gender of speaker'''
	name = models.CharField(max_length=100,default='')

	def __repr__(self):
		return self.name

class Location(models.Model):
	'''city/village where the recording is made.'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	name = models.CharField(max_length=100,default='')
	alternative_names = models.CharField(max_length=300,default='')
	kloeke = models.CharField(max_length= 9,default='')
	latitude = models.FloatField(default = None,null=True)
	longitude = models.FloatField(default = None,null=True)
	dialect = models.ForeignKey(Dialect, **dargs)
	province = models.ForeignKey(Province, **dargs)
	country = models.ForeignKey(Country, **dargs)

	def __repr__(self):
		return self.name + ' | ' + self.kloeke + ' | ' + self.province.name


class Asr(models.Model):
	''' Automatic speech recognition information of the transcription.
	'''
	modelname = models.CharField(max_length=300, default='')
	directory = models.CharField(max_length=300, default='')

	def __repr__(self):
		return self.modelname

class Recording(models.Model):
	''' A recording of speech, linked to a location and optionally to a
	human transcription that is scanned and ocr. 
	'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	landsdb_id = models.PositiveIntegerField(null=True,blank=True) 
	record_id = models.PositiveIntegerField(null=True,blank=True) 
	ocr_transcription_available = models.BooleanField(default = False)
	locations= models.ManyToManyField(Location, blank=True)
	location_str = models.CharField(max_length=600,default='')
	country = models.ForeignKey(Country, **dargs)
	province= models.ForeignKey(Province, **dargs)
	area = models.CharField(max_length=100,default='')
	soundbites_info = models.TextField(default='')
	mp3_url = models.CharField(max_length=300,default='')
	wav_filename = models.CharField(max_length=300,default='')
	original_audio_filename = models.CharField(max_length=300,default='')
	recording_date_str = models.CharField(max_length=30, default='')
	recording_date = models.DateTimeField(null=True,blank=True)
	duration_str = models.CharField(max_length=10, default='')
	duration = models.PositiveIntegerField(null=True,blank=True) 
	sex = models.ForeignKey(Sex, **dargs)
	year_of_birth = models.PositiveIntegerField(null=True,blank=True) 
	age = models.PositiveIntegerField(null=True,blank=True) 
	recording_type_dutch = models.CharField(max_length = 100, default = '')
	recording_types = models.ManyToManyField(Recordingtype,blank=True)
	
	def __repr__(self):
		m = 'recording: ' + self.city_names +' | ' + str(self.duration)
		return m

	def __str__(self):
		return self.__repr__()

	@property
	def cities(self):
		if not hasattr(self,'_cities'):
			self._cities = [x.name for x in self.locations.all()]
		return self._cities

	@property
	def city_names(self):
		return ', '.join([city for city in self.cities])

	@property
	def ocrs(self):
		if not hasattr(self,'_ocrs'): 
			self._ocrs = self.ocr_set.all().order_by('page_number')
		return self._ocrs

	@property
	def ocr_transcriptions(self):
		if not self.ocr_transcription_available: return []
		if not hasattr(self,'_ocr_transcriptions'):
			self._ocr_transcriptions = []
			for ocr_page in self.ocrs:
				self._ocr_transcriptions.extend(ocr_page.transcriptions)
		return self._ocr_transcriptions
			

class Ocr(models.Model):
	'''optical charcter recognition information of the transcription.
	the speech recordings were transcribed on type writer and scanned and ocr
	'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	ocr_filename = models.CharField(max_length=300,default='')
	image_filename = models.CharField(max_length=300,default='')
	page_number = models.PositiveIntegerField(null=True,blank=True) 
	page_width = models.PositiveIntegerField(null=True,blank=True)
	page_height = models.PositiveIntegerField(null=True,blank=True)
	recording = models.ForeignKey(Recording,**dargs)
	confidence = models.FloatField(null=True,blank=True)
	avg_left_x= models.FloatField(null=True,blank=True)

	def __repr__(self):
		m = self.ocr_filename + ' | ' + self.image_filename 
		m += ' | ' + str(self.page_number)
		return m

	def __str__(self):
		return self.__repr__()

	@property
	def transcriptions(self):
		if not hasattr(self,'_transcriptions'):
			t= self.transcription_set.all()
			self._transcriptions = list(t.order_by('ocr_avg_y'))
		return self._transcriptions

	def _set_confidence(self):
		confidence =[x.confidence for x in self.transcriptions if x.confidence]
		if confidence: 
			self.confidence = np.mean(confidence)
			self.save()

	def _set_avg_left_x(self):
		leftx = [x.ocr_left_x for x in self.transcriptions if x.ocr_left_x]
		if leftx: 
			self.avg_left_x = np.mean(leftx)
			self.save()

	@property
	def image(self):
		path = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/transcriptions/'
		path += '1001:2_Transcripties_geanonimiseerd/'
		filename = path + self.image_filename
		img = mpimg.imread(filename)
		return img

	def show_page_image(self):
		img = self.image
		plt.imshow(img,cmap='gray')
		plt.tight_layout()
		frame = plt.gca()
		frame.axes.get_xaxis().set_visible(False)
		frame.axes.get_yaxis().set_visible(False)
		plt.show()
		

class Transcriptionset(models.Model):
	'''
	a set of transcriptions, in the transcription_pk_order field
	you can store the order of transcription pks
	'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	name = models.CharField(max_length=300,default='')
	start_time = models.FloatField(default = None,null=True)
	end_time = models.FloatField(default = None,null=True)
	recording = models.ForeignKey(Recording, **dargs)
	transcription_pk_order = models.TextField(default='')

	def __repr__(self):
		return self.name + ' | ' + self.transcription_pk_order

class Transcription(models.Model):
	'''Transcription of speech recording made by asr or humans 
	(scanned and ocr.)'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	id_name = models.CharField(max_length=100,default='')
	text = models.TextField(default='')
	words_tsv = models.CharField(max_length=500,default='')
	words_confidence_tsv = models.CharField(max_length=500,default='')
	confidence = models.FloatField(default=None,null=True)
	transcription_type = models.ForeignKey(Transcriptiontype, **dargs)
	start_time = models.FloatField(default = None,null=True)
	end_time = models.FloatField(default = None,null=True)
	asr = models.ForeignKey(Asr,**dargs)
	ocr = models.ForeignKey(Ocr, **dargs)
	ocr_left_x = models.PositiveIntegerField(null=True,blank=True) 
	ocr_right_x = models.PositiveIntegerField(null=True,blank=True) 
	ocr_avg_y = models.PositiveIntegerField(null=True,blank=True) 
	recording = models.ForeignKey(Recording, **dargs)

	def __repr__(self):
		m = str(self.page_number).ljust(4)
		if len(self.text_clean) > 150: t = self.text_clean[:150] + '[...]'
		else : t = self.text_clean
		m += t 
		return m

	def __str__(self):
		return self.__repr__()

	@property
	def page_number(self):
		return self.ocr.page_number

	@property
	def page_confidence(self):
		return self.ocr.confidence

	@property
	def city_names(self):
		return self.recording.city_names

	@property
	def text_clean(self):
		if not hasattr(self,'_clean_text_simple'):
			self._clean_text_simple = clean_simple(self.text).lower()
		return self._clean_text_simple



