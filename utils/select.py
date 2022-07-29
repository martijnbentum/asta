from texts.models import Recording
from collections import Counter
from utils import align
import random


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
    a = align.Align(recording)
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

def filter_ocr_lines_without_start_end_times(ols):
    output = []
    for ol in ols:
        if type(ol.start_time) == float and type(ol.end_time) == float:
            output.append(ol)
    return output

def filter_ocr_lines_indices(ols, exclude_indices): 
    return [ol for ol in ols if ol.ocrline_index not in exclude_indices]

def ocr_lines_to_indices(ols):
    return [ol.ocrline_index for ol in ols]

def get_ocr_line(align, location = 'first', maximum_align_mismatch = 55, 
        ols = None):
    if not align.ok: return None
    if ols == None:
        ols=align.filter_ocr_lines(mismatch_threshold = maximum_align_mismatch)
    ols = filter_ocr_lines_without_start_end_times(ols)
    if len(ols) == 0:
        return None
    if location == 'first': n = 0
    if location == 'middle': n = int(len(ols)/2)
    if location == 'last': n = -1
    return ols[n]
        
def sample_ocr_lines(align, min_lines = 30, max_lines=100, perc_lines = 20,
    maximum_align_mismatch = 55, exclude_indices = []):
    ols=align.filter_ocr_lines(mismatch_threshold = maximum_align_mismatch)
    if len(ols) == 0: return []
    ols = filter_ocr_lines_without_start_end_times(ols)
    ols = filter_ocr_lines_indices(ols, exclude_indices)
    n = int(len(align.ocr_lines) * (perc_lines/100))
    if n < min_lines: n = min_lines
    if n > max_lines: n = max_lines
    if len(ols) <= n: return ols
    output = [ols.pop(0),ols.pop(int(len(ols)/2)), ols.pop(-1)]
    output += random.sample(ols,n-3)
    return output

    
def get_dutch_provinces():
    recordings = get_recordings_from_country(country='Netherlands')
    return dict(Counter([x.province.name for x in recordings if x.province]))

def get_dutch_areas():
    recordings = get_recordings_from_country(country='Netherlands')
    return dict(Counter([x.area for x in recordings if x.area]))
    
    
'''
def args_to_ocrline(request, location= '', location_type= '', exclude = 'None',
    minimum_match = 35, perc_lines = 20, record_index = 0, line_index = 0):
'''
def args_to_ocrline(args):
    print(args)
    if args['location_type'] == 'area':
        recordings = get_recordings_with_areas_list([args['location']])
    if args['location_type'] == 'province':
        recordings = get_recordings_with_province_list([args['location']])
    recording = recordings[args['record_index']]
    mismatch = 100 - args['minimum_match']
    print('mismatch',mismatch)
    ocr_lines = sample_ocr_lines(recording.align, 
        maximum_align_mismatch = mismatch,perc_lines = args['perc_lines'])
    print('n ocr lines',len(ocr_lines))
    if args['line_index'] >= len(ocr_lines) or len(ocr_lines) == 0: 
        print(recording)
        args['record_index'] +=1
        if args['record_index'] >= recordings.count(): 
            return 'done with all recordings'
        args['line_index'] = 0
        return args_to_ocrline(args)
    args['ocrline'] = ocr_lines[args['line_index']]
    args['nocrlines'] = len(ocr_lines)
    args['line_index'] +=1
    print(args)
    return args
    
    
    

    
