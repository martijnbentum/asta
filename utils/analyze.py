from collections import Counter
from matplotlib import pyplot as plt
import numpy as np
import os
from scipy import stats
from texts.models import Recording,Transcription
from . import celex


def recording_duration_histogram(nbins = 30):
	duration_minutes = [x.duration/60 for x in Recording.objects.all()]
	plt.clf()
	plt.hist(duration_minutes,nbins)
	plt.title('Distribution of recording durations')
	plt.ylabel('number of recordings')
	plt.xlabel('duration in minutes')
	plt.show()
	
def recording_date_histogram(nbins = 30):
	d= [x.recording_date for x in Recording.objects.all() if x.recording_date]
	plt.clf()
	plt.hist(d,nbins)
	plt.title('Distribution of recording dates')
	plt.ylabel('number of recordings')
	plt.xlabel('date')
	plt.show()

def province_recording_counts_barplot():
	nl = Recording.objects.filter(country__name='Netherlands')
	provinces = [x.province.name for x in nl if x.province]
	counter_provinces = Counter(provinces)
	# sort the provinces by recording count in ascending order
	counter_provinces=dict(sorted(counter_provinces.items(),key=lambda x:x[1]))
	names = list(counter_provinces.keys())
	counts = list(counter_provinces.values())
	plt.clf()
	plt.bar(names,counts)
	plt.xticks(rotation='vertical')
	plt.ylabel('count')
	plt.title('number of recordings per province')
	plt.subplots_adjust(bottom=0.3)

	ocr = Recording.objects.filter(ocr_transcription_available=True) 
	ocr_nl = ocr.filter(country__name='Netherlands')
	provs = [x.province.name for x in ocr_nl if x.province]
	cprovs = Counter(provs)
	cprovs = dict(sorted(cprovs.items(),key = lambda x:x[1]))
	prov_names = list(cprovs.keys())
	prov_counts = list(cprovs.values())
	plt.bar(prov_names,prov_counts)
	plt.legend(['total recordings','transcribed recordings'])

	plt.show()

def celex_coverage_per_recording_histogram(coverage = None,nbins=30):
	ocr = Recording.objects.filter(ocr_transcription_available=True,
		ocr_handwritten = False)
	coverage = [x.celex_coverage for x in ocr]
	plt.clf()
	plt.hist(coverage,nbins)
	plt.title('Distribution of recording transcription celex coverage')
	plt.ylabel('number of recordings')
	plt.xlabel('coverage')
	plt.show()

def transcription_sentence_confidence_density_plot():
	t = Transcription.objects.all()
	confidence = [x.confidence for x in t if x.confidence]
	density = stats.gaussian_kde(confidence)
	x = np.linspace(0,1,1000)
	y = density(x)
	plt.clf()
	plt.title('ocr confidence on sentence level')
	plt.xlabel('confidence')
	plt.plot(x,y)

	plt.show()


def analyze_transcriptions(save = False):
	ocr = Recording.objects.filter(ocr_transcription_available=True,
		ocr_handwritten = False)
	print('n recordings:',ocr.count())
	c = celex.Celex()
	o = []
	[o.extend(recording.ocr_transcriptions) for recording in ocr]
	text = ' '.join([x.text_clean for x in o])
	words = text.split(' ')
	word_types = list(set(words))
	word_types_in_celex = [wt for wt in word_types if wt in c.vocab]
	words_in_celex = [word for word in words if word in word_types_in_celex]
	d = {'transcriptions':o,'words':words,'word_types':word_types}
	d['word_types_in_celex']=word_types_in_celex
	d['words_in_celex']=words_in_celex
	if save: _save_analyze_dict(d)
	return d

def _save_analyze_dict(d = None):
	if not d: d = analyze_transcriptions()
	text = '\n'.join([x.text_clean for x in d['transcriptions']])
	with open('../TRANSCRIPTION_ANALYSIS/all_transcriptions','w') as fout:
		fout.write(text)
	with open('../TRANSCRIPTION_ANALYSIS/word_types','w') as fout:
		fout.write('\n'.join(d['word_types']))
	with open('../TRANSCRIPTION_ANALYSIS/word_types_in_celex','w') as fout:
		fout.write('\n'.join(d['word_types_in_celex']))


def _find_double_transcriptions(transcriptions):
	doubles = []
	pks = []
	for transcription in transcriptions:
		temp = [transcription]
		if transcription.pk in pks: continue
		for other_transcription in transcriptions:
			if other_transcription.pk in pks: continue
			if transcription.pk == other_transcription.pk: continue
			if transcription.ocr_avg_y == other_transcription.ocr_avg_y:
				if transcription.text == other_transcription.text:
					temp.append(other_transcription)
		if len(temp) > 1:
			pks.extend([x.pk for x in temp])
			doubles.append(temp)
	return doubles
	
def find_double_transcriptions():
	recordings = Recording.objects.filter(ocr_transcription_available=True)
	doubles = []
	for recording in recordings:
		for ocr_page in recording.ocrs:
			doubles.extend(_find_double_transcriptions(ocr_page.transcriptions))
	return doubles
			
	
def annotate_ocr_recording_is_handwritten():
	ocr = Recording.objects.filter(ocr_transcription_available=True) 
	ocr = list(ocr)
	ocr = sorted(ocr, key = lambda x:x.ocr_confidence)
	for i,recording in enumerate(ocr):
		if recording.ocr_handwritten: continue
		print(i,recording)
		recording.show_ocr_page_images(npages =9)
		print(i,recording)
		a = input('handwritten: ')
		if a == 'y':
			recording.ocr_handwritten = True
			recording.save()
	

