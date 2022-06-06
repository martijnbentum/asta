from django.db import models
import numpy as np
from utils.clean_text import clean_simple
from utils import celex, audio
import matplotlib.image as mpimg
from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = (10,12)
	

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
	comments = models.TextField(default = '')
	model_description = models.TextField(default='')
	tokenizer_description = models.TextField(default='')
	feature_extractor_description = models.TextField(default='')

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
	celex_coverage = models.FloatField(null=True,blank=True)
	ocr_confidence = models.FloatField(null=True,blank=True)
	ocr_handwritten = models.BooleanField(default = False)
	
	def __repr__(self):
		m = 'recording: ' + self.city_names +' | ' + str(self.duration)
		return m

	def __str__(self):
		return self.__repr__()

	@property
	def name(self):
		return self.city_names.replace(', ','_').replace(' ','_')

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

	def load_audio(self,start = 0.0, end = None):
		return audio.load_recording(self,start,end)

	def show_ocr_page_images(self, npages = None):
		if npages == None: npages = len(self.ocrs)
		for ocr in self.ocrs[:npages]:
			print(ocr.page_number)
			ocr.show_page_image()

	@property
	def ocr_transcriptions(self):
		if not self.ocr_transcription_available: return []
		if not hasattr(self,'_ocr_transcriptions'):
			self._ocr_transcriptions = []
			for ocr_page in self.ocrs:
				self._ocr_transcriptions.extend(ocr_page.transcriptions)
		return self._ocr_transcriptions

	@property
	def text_clean(self):
		if not self.ocr_transcription_available: return ''
		return '\n'.join([x.text_clean for x in self.ocr_transcriptions])

	@property
	def words(self):
		if not hasattr(self,'_words'):
			self._words = self.text_clean.replace('\n',' ').split(' ')
		return self._words

	@property
	def nwords(self):
		return len(self.words)

	@property
	def words_in_celex(self):
		if not hasattr(self,'_words_in_celex'):
			wt_celex = celex.load_word_types()
			self._words_in_celex = [w for w in self.words if w in wt_celex]
		return self._words_in_celex
			
	@property
	def nwords_in_celex(self):
		return len(self.words_in_celex)

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
	meta_text_page = models.BooleanField(default=False)

	def __repr__(self):
		m = self.ocr_filename + ' | ' + self.image_filename 
		m += ' | ' + str(self.page_number)
		return m

	def __str__(self):
		return self.__repr__()

	@property
	def transcriptions(self):
		if not hasattr(self,'_transcriptions'):
			t= self.transcription_set.filter(usable=True)
			self._transcriptions = list(t.order_by('ocr_avg_y'))
		return self._transcriptions

	@property
	def text_clean(self):
		return '\n'.join([x.text_clean for x in self.transcriptions])

	@property
	def words(self):
		return self.text_clean.replace('\n',' ').split(' ')

	@property
	def nwords(self):
		return len(self.words)

	@property
	def words_in_celex(self):
		if not hasattr(self,'_words_in_celex'):
			wt_celex = celex.load_word_types()
			self._words_in_celex = [w for w in self.words if w in wt_celex]
		return self._words_in_celex
			
	@property
	def nwords_in_celex(self):
		return len(self.words_in_celex)

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
		plt.clf()
		plt.imshow(img,cmap='gray')
		plt.tight_layout()
		axis= plt.gca()
		axis.axes.get_xaxis().set_visible(False)
		axis.axes.get_yaxis().set_visible(False)
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
	usable = models.BooleanField(default=True)
	double = models.BooleanField(default=False)
	is_meta_text = models.BooleanField(default=False)
	asr_words = models.TextField(default='')

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
		if self.ocr:
			return self.ocr.page_number
		else: return ''

	@property
	def page_confidence(self):
		return self.ocr.confidence

	@property
	def city_names(self):
		return self.recording.city_names

	@property
	def text_clean(self):
		if not hasattr(self,'_text_clean'):
			self._text_clean= clean_simple(self.text).lower()
		return self._text_clean

	@property
	def words(self):
		return self.text_clean.split(' ')

	@property
	def nwords(self):
		return len(self.words)

	@property
	def words_in_celex(self):
		if not hasattr(self,'_words_in_celex'):
			wt_celex = celex.load_word_types()
			self._words_in_celex = [w for w in self.words if w in wt_celex]
		return self._words_in_celex
			
	@property
	def nwords_in_celex(self):
		return len(self.words_in_celex)


	def show_line_image(self):
		img = self.ocr.image
		y = self.ocr_avg_y
		start, end = y - 30, y + 30
		plt.clf()
		plt.imshow(img[start:end],cmap='gray')
		plt.tight_layout()
		axis= plt.gca()
		axis.axes.get_xaxis().set_visible(False)
		axis.axes.get_yaxis().set_visible(False)
		axis.hlines(y=30,xmin=self.ocr_left_x,xmax=self.ocr_right_x,
			linewidth=6,alpha=0.2)
		plt.show()
		print(self)



