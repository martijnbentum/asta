import librosa

def load_audio(filename, start = 0.0, end=None):
	if not end: duration = None
	else: duration = end - start
	audio, sr = librosa.load(filename, sr = 16000, offset=start, duration=end)
	return audio

def load_recording(recording, start = 0.0,end = None):
	audio = load_audio(recording.wav_filename,start,end)
	return audio
	
