from transformers import Wav2Vec2ForCTC
from transformers import Wav2Vec2Processor
from texts.models import Recording, Recordingtype, Asr, Transcription
from texts.models import Transcriptiontype
import os 

fremy_model1 = 'FremyCompany/xls-r-2b-nl-v2_lm-5gram-os'

''' 
More info about pipelines for ASR see:
https://huggingface.co/docs/transformers/v4.19.2/en/main_classes/pipelines#transformers.AutomaticSpeechRecognitionPipeline
'''
from transformers import AutomaticSpeechRecognitionPipeline as ap

default_recognizer_dir = "/vol/bigdata2/datasets2/SSHOC-T44-LISpanel-2021/"
default_recognizer_dir += "TEXT_ANALYSIS/homed_lm_recognizers/cgn/"

def load_model(recognizer_dir = default_recognizer_dir):
	model = Wav2Vec2ForCTC.from_pretrained(recognizer_dir)
	return model

def load_processor(recognizer_dir = default_recognizer_dir):
	processor = Wav2Vec2Processor.from_pretrained(recognizer_dir)
	return processor

def load_pipeline(recognizer_dir=None, chunk_length_s = 10, device = -1):
	if not recognizer_dir: recognizer_dir = default_recognizer_dir
	print('loading model:',recognizer_dir)
	model = load_model(recognizer_dir)
	print('loading processor')
	p= load_processor(recognizer_dir)
	print('loading pipeline')
	pipeline = ap(
		feature_extractor =p.feature_extractor,
		model = model,
		tokenizer = p.tokenizer,
		chunk_length_s = chunk_length_s,
		device = device
	)
	return pipeline

def decode_recording(recording, pipeline, start=0.0, end=None):
	audio = recording.load_audio(start,end)
	output = pipeline(audio, return_timestamps = 'word')
	return output 
	

def load_or_make_asr(pipeline,model_name='', comments = ''):
	directory= pipeline.tokenizer.name_or_path
	try: asr = Asr.objects.get(directory = directory)
	except Asr.DoesNotExist:
		print('creating asr',directory)
		asr = Asr(
			directory=directory,
			modelname = model_name,
			comments = comments,
			tokenizer_description = str(pipeline.tokenizer),
			model_description = str(pipeline.model),
			feature_extractor_description = str(pipeline.feature_extractor)
		)
		asr.save()
	else:
		m = 'loading asr object corresponding to a pipeline loaded from:\n'
		print(m,directory)
	return asr


def make_decoding_output_filename(asr,recording):
	filename = '../WAV2VEC2_TRANSCRIPTIONS/'
	filename += 'record_id-' + str(recording.record_id)
	filename += '_recording-' + str(recording.pk)
	filename += '_asr-' + str(asr.pk)
	return filename

def save_pipeline_output_to_file(output, asr, recording):
	filename = make_decoding_output_filename(asr,recording)
	table = pipeline_output2table(output)
	print('saving to:',filename)
	with open(filename,'w') as fout:
		fout.write(table2str(table))

def save_pipeline_output_to_transcription(output, asr, recording):
	tt = Transcriptiontype.objects.get(name = 'asr')
	table = pipeline_output2table(output)
	table_str = table2str(table)
	start = table[0][1]
	end  = table[-1][2]
	transcription = Transcription(
		recording = recording,
		text = output['text'],
		transcription_type = tt,
		asr = asr,
		asr_words = table_str,
		start_time = start,
		end_time = end,
	)
	transcription.save()
	return transcription

def pipeline_output2table(output):
	table = []
	for d in output['chunks']:
		start, end = d['timestamp']
		table.append([d['text'], start, end])
	return table

def table2str(table):
	output = []
	for line in table:
		output.append('\t'.join(list(map(str,line))))
	return '\n'.join(output)

def transcribe_recordings(recordings,pipeline = None, overwrite = False):
	if not pipeline:
		print('loading default pipeline, uses GPU')
		pipeline = load_pipeline(device = 0)
	asr = load_or_make_asr(pipeline)
	nrecordings = len(recordings)
	for i,recording in enumerate(recordings):
		filename = make_decoding_output_filename(asr,recording)
		if not overwrite and os.path.isfile(filename):
			print('SKIPPING:',i,recording,'filename exists:',filename)
			continue
		else: print('decoding:',i,recording,nrecordings)
		output = decode_recording(recording, pipeline)
		save_pipeline_output_to_file(output, asr, recording)
		save_pipeline_output_to_transcription(output, asr, recording)
		

		

