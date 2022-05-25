from django.db import models

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

	@property
	def cities(self):
		if not hasattr(self,'_cities'):
			self._cities = [x.name for x in self.locations.all()]
		return self._cities

	@property
	def city_names(self):
		return ', '.join([city for city in self.cities])


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

	def __repr__(self):
		m = self.ocr_filename + ' | ' + self.image_filename 
		m += ' | ' + str(self.page_number)
		return m

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
		if len(self.text) > 150: t = self.text[:150] + '[...]'
		else : t = self.text
		m = t 
		if self.recording_type:
			m += ' | ' + self.recording_type.name


