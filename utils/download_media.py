import os
 
original_audio_directory = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/wav/'
goal_audio_directory = 'media/audio/'

original_ocr_directory = '/vol/bigdata2/corpora2/CLARIAH-PLUS/ASTA/'
original_ocr_directory += 'transcriptions/1001:2_Transcripties_geanonimiseerd/'
goal_ocr_directory = 'media/ocr/'

def make_new_audio_filename(filename):
    filename = filename.replace(original_audio_directory,'')
    filename = filename.replace('/','_')
    filename = filename.replace(' ','_')
    filename = goal_audio_directory + filename
    return filename


def download_audio_recording(recording):
    f = recording.wav_filename
    filename = make_new_audio_filename(f)
    if os.path.isfile(filename): 
        print(filename,'already exists, doing nothing')
        return 
    command = 'cp "' + f + '" ' + filename
    print(command)
    os.system(command)

def make_new_ocr_filename(filename):
    filename = filename.replace(original_ocr_directory,'')
    filename = filename.replace('/','_')
    filename = goal_ocr_directory + filename
    return filename

def download_ocr(ocr):
    f = ocr.image_full_path
    filename = make_new_ocr_filename(f)
    if os.path.isfile(filename): 
        print(filename,'already exists, doing nothing')
        return
    command = 'cp ' + f + ' ' + filename
    os.system(command)

def download_all_ocrs_recording(recording):
    for ocr in recording.ocrs:
        download_ocr(ocr)


def download_media_all_recordings():
    from texts.models import Recording
    recordings = Recording.objects.all()
    for i,recording in enumerate(recordings):
        print(i,recording, recordings.count())
        download_audio_recording(recording)
        download_all_ocrs_recording(recording)

def check_audio_downloads():
    from texts.models import Recording
    recordings = Recording.objects.all()
    ok, not_ok = [], []
    for i,recording in enumerate(recordings):
        f = recording.original_audio_filename
        filename = make_new_audio_filename(f)
        if os.path.isfile(filename): ok.append(recording)
        else: not_ok.append(recording)
    return ok, not_ok
    
    
