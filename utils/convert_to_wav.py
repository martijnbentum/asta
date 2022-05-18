import glob
import os

original_audio_directory = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/audio/'
wav_directory = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/wav/'
extra_mp3 = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/extra_mp3/'


def get_all_original_files():
	'''mp3 files of the dialect recordings'''
	fn = glob.glob(original_audio_directory + '**',recursive=True)
	return [f for f in fn if os.path.isfile(f) and f.endswith('.mp3')]

def get_extra_mp3_files():
	'''mp3 files downloaded based on the mp3 url of the soundbites meta data
	info, should be restricted to the files that were not in the
	original_audio_directory
	'''
	fn = glob.glob(extra_mp3+ '*.mp3')
	return fn

def make_wav_name(original_filename, org_directory = original_audio_directory):
	'''create a wav name, flattening the nested directory structure
	double underscore __ indicates a nested directory 
	'''
	identifier = original_filename.replace(org_directory,'')
	name = identifier.replace('/','__').replace('.mp3','.wav')
	wav_name = wav_directory + name
	return wav_name.replace(' ','_')


def convert_files(fn = None,write_files = False, overwrite = False, 
		org_directory = original_audio_directory):
	''' convert an mp3 file to a wav file mono 16K sr'''
	if not fn: fn = get_all_original_files()
	print_overwrite = False
	output = []
	for original_filename in fn:
		wav_name = make_wav_name(original_filename, org_directory)
		output.append( [original_filename, wav_name] )
		original_filename = '"' + original_filename + '"'
		c = 'sox ' + original_filename + ' -r 16000 -c 1 -b 16 ' + wav_name
		is_file = os.path.isfile(wav_name)
		if is_file: 
			m = wav_name+' already made'
			print_overwrite = True
			if overwrite: 
				os.system(c)
				m += ' OVERWRITTEN'
			print(m)
		elif write_files: 
			print(c)
			os.system(c)
	if not write_files: print('set write_files to true to write files')
	if print_overwrite: print('set overwrite to true to overwrite existing wav files')
	return output
	

