from texts.models import Recording
from collections import Counter
from utils import align_ocr_asr as aoa


def get_recordings_with_area_specified(only_with_ocr_available = True):
    recordings = Recording.objects.exclude(area = '')
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    return recordings

def get_recordings_with_province_specified(only_with_ocr_available = True):
    recordings = Recording.objects.exclude(province__name= None)
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    return recordings

def align_ok(recording):
    a = aoa.Align(recording)
    return a.ok and a.ocr_lines_ok

def get_all_areas(only_with_ocr_available = True):
    recordings = get_recordings_with_area_specified(only_with_ocr_available)
    areas = [x.area for x in recordings]
    return Counter(areas)

def make_area_to_recording_dict(only_with_ocr_available = True,
    only_dutch = True):
    recordings = get_recordings_with_area_specified(only_with_ocr_available)
    if only_dutch: recordings = recordings.filter(country__name = 'Netherlands')
    d = {}
    for recording in recordings:
        area = recording.area
        if area not in d.keys(): d[area] = [recording]
        else: d[area].append(recording)
    return d

def make_province_to_recording_dict(only_with_ocr_available = True,
    only_dutch = True):
    recordings = get_recordings_with_province_specified(only_with_ocr_available)
    if only_dutch: recordings = recordings.filter(country__name = 'Netherlands')
    d = {}
    for recording in recordings:
        province= recording.province.name
        if province not in d.keys(): d[province] = [recording]
        else: d[province].append(recording)
    return d

def get_recordings_with_areas_list(areas = None, recordings = None,
    only_with_ocr_available = True):
    if areas == None:
        areas = 'NBra-W,NBra-M,NBra-Z,NBra-O,NLimb-Z,NLimb-M,NLimb-N'.split(',')
    if recordings == None: 
        recordings = Recording.objects.all()
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    recordings = recordings.filter(area__in = areas) 
    return recordings

def get_recordings_with_province_list(provinces = None, recordings = None,
    only_with_ocr_available = True):
    if provinces == None:
        provinces = 'Noord-Brabant,Limburg,Gelderland'.split(',')
    if recordings == None: 
        recordings = Recording.objects.all()
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    recordings = recordings.filter(province__name__in = provinces) 
    return recordings

def get_recordings_from_country(country = 'Netherlands', recordings = None,
    only_with_ocr_available = True):
    if recordings == None: 
        recordings = Recording.objects.all()
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    return recordings.filter(country__name = 'Netherlands')


    
    
