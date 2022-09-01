import librosa

def load_audio(filename, start = 0.0, end=None):
	if not end: duration = None
	else: duration = end - start
	audio, sr = librosa.load(filename, sr = 16000, offset=start, duration=end)
	return audio

def load_recording(recording, start = 0.0,end = None):
	audio = load_audio(recording.wav_filename,start,end)
	return audio
	

def load_audio_section(start_time,end_time,filename,audio=None):
    sampling_rate = 16000
    if not audio: audio = load_audio(filename)
    return audio[int(start_time*sampling_rate):int(end_time*sampling_rate)]
        
