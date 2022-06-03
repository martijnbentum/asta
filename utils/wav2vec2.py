from transformers import Wav2Vec2ForCTC
from transformers import Wav2Vec2Processor

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
