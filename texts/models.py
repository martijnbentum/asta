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

class Area(models.Model):
	'''location name between city and province.'''
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

class City(models.Model):
	'''city/village where the recording is made.'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	name = models.CharField(max_length=100,default='')
	province = models.ForeignKey(Province, **dargs)
	country = models.ForeignKey(Country, **dargs)

	def __repr__(self):
		return self.name

class Kloekecode(models.Model):
	'''code dividing the Netherlands in small sections used for 
	dialect research
	'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	name = models.CharField(max_length= 9,default='')
	lattitude = models.FloatField(default = None,null=True)
	longitude = models.FloatField(default = None,null=True)
	dialect = models.ForeignKey(Dialect, **dargs)
	province = models.ForeignKey(Province, **dargs)
	country = models.ForeignKey(Country, **dargs)
	city = models.ForeignKey(City, **dargs)

	def __repr__(self):
		return 'kloeke: ' +self.name + ' | ' + self.dialect

class Ocr(models.Model):
	'''optical charcter recognition information of the transcription.
	the speech recordings were transcribed on type writer and scanned and ocr
	'''
	ocr_filename = models.CharField(max_length=300,default='')
	image_filename = models.CharField(max_length=300,default='')
	page_number = models.PositiveIntegerField(null=True,blank=True) 

	def __repr__(self):
		m = self.ocr_filename + ' | ' + self.image_filename 
		m += ' | ' + self.page_number
		return m

class Asr(models.Model):
	''' Automatic speech recognition information of the transcription.
	'''
	modelname = models.CharField(max_length=300,default='')
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
	province_str = models.CharField(max_length=200,default ='')
	city_str = models.CharField(max_length = 200, default = '')
	country = models.ForeignKey(Country, **dargs)
	kloekecodes= models.ManyToManyField(Kloekecode, blank=True)
	soundbites_info = models.TextField(default='')
	mp3_url = models.CharField(max_length=300,default='')
	wav_filename = models.CharField(max_length=300,default='')
	original_audio_filename = models.CharField(max_length=300,default='')
	area = models.ForeignKey(Area, **dargs)
	recording_date_str = models.CharField(max_length=30, default='')
	recording_date = models.DateTimeField()
	duration = models.PositiveIntegerField(null=True,blank=True) 
	sex = models.ForeignKey(Sex, **dargs)
	year_of_birth = models.PositiveIntegerField(null=True,blank=True) 
	age = models.PositiveIntegerField(null=True,blank=True) 
	recording_type_dutch = models.CharField(max_length = 100, default = '')
	recording_types = models.ManyToManyField(Recordingtype,blank=True)
	
	def __repr__(self):
		m = self.city.name + ' | ' + self.duration
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


