from texts.models import Recording, AnnotationUserInfo
from collections import Counter
from utils import align
import numpy as np
import time


def get_recordings_with_area_specified(only_with_ocr_available = True):
    '''select set of recordings that have a value for area.'''
    recordings = Recording.objects.exclude(area = '')
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    return recordings

def get_recordings_with_province_specified(only_with_ocr_available = True):
    '''select set of recordings that have a value for province.'''
    recordings = Recording.objects.exclude(province__name= None)
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    return recordings

def align_ok(recording):
    '''check whether a recording has an ok align object associated.
    (future: align is specified with recording and Asr object)
    '''
    a = align.Align(recording)
    return a.ok and a.ocr_lines_ok

def get_all_areas(only_with_ocr_available = True):
    '''return the set of areas specified in the recordings'''
    recordings = get_recordings_with_area_specified(only_with_ocr_available)
    areas = [x.area for x in recordings]
    return Counter(areas)

def make_area_to_recording_dict(only_with_ocr_available = True,
    only_dutch = True):
    '''return a dict with area names as keys and 
    associated recordings lists as values.
    '''
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
    '''return a dict with province names as keys and 
    associated recordings lists as values.
    '''
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
    '''return recordings linked to an area in a list of areas.
    areas       list of area names to be matched
    recordings  set of recordings to matched with area names list
    '''
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
    '''return recordings linked to an province in a list of provinces.
    provinces   list of province names to be matched
    recordings  set of recordings to matched with area names list
    '''
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
    '''return recordings linked to a given country.'''
    if recordings == None: 
        recordings = Recording.objects.all()
    if only_with_ocr_available:
        recordings = recordings.filter(ocr_transcription_available = True)
    return recordings.filter(country__name = 'Netherlands')

def filter_ocr_lines_without_start_end_times(ols):
    '''remove ocr lines (transcription) that do not have an start and or
    end time.
    '''
    output = []
    for ol in ols:
        if type(ol.start_time) == float and type(ol.end_time) == float:
            output.append(ol)
    return output

def filter_ocr_lines_indices(ols, exclude_indices): 
    '''
    filter ocr lines (transcriptions based on a set of exclude indices.
    an ocr line has a property ocrline_index that represents the index
    of that line in the set of ocr_lines in an align object.
    '''
    return [ol for ol in ols if ol.ocrline_index not in exclude_indices]

def ocr_lines_to_indices(ols):
    ''' return a list of indices given a list of ocr lines (transcriptions).'''
    return [ol.ocrline_index for ol in ols]

def get_ocr_line(align, location = 'first', maximum_align_mismatch = 55, 
        ols = None):
    '''
    get a specific (i.e. first middle last orc line given a specific
    misamtch threshold
    align                   align object
    location                first middle or last
    maximum_align_mismatch  the maximum mismatch number
    ols                     list of ocr lines (mismatch threshold is not used)
    '''
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
        
def sample_ocr_lines(align, min_lines = 30, max_lines=60, perc_lines = 20,
    maximum_align_mismatch = 55, exclude_indices = []):
    '''
    return a list of ocr lines based on selection criteria.
    align           align object
    min_lines       the minimum number of ocr lines (transcriptions)
    max_lines       the maximum number of ocr lines (transcriptions)
    perc_lines      the percentage of ocr lines (transcriptions) given the
                    total number of ocr lines of an align object
                    if this is lower or higher than min / max lines it gets
                    overruled
    maximum_al...   the threshold value for mismatching between asr and ocr
                    transcriptions (if mismatch is very high there is no reason
                    to annotate)
    exclude_in...   ocr line (transcription) indices that should be excluded
                    (because they are already annotated)
    '''
    ols=align.filter_ocr_lines(mismatch_threshold = maximum_align_mismatch)
    if len(ols) == 0: return []
    ols = filter_ocr_lines_without_start_end_times(ols)
    ols = filter_ocr_lines_indices(ols, exclude_indices)
    n = int(len(align.ocr_lines) * (perc_lines/100))
    if n < min_lines: n = min_lines
    if n > max_lines: n = max_lines
    if len(ols) <= n: return ols
    output = []
    start, end = 0, len(ols) -1
    indices = np.linspace(start,end,n,dtype = int)
    for index in indices:
        output.append(ols[index])
    return output

    
def get_dutch_provinces():
    '''return a dict linking province name to the linked recordings.'''
    recordings = get_recordings_from_country(country='Netherlands')
    return dict(Counter([x.province.name for x in recordings if x.province]))

def get_dutch_areas():
    '''return a dict linking area name to the linked recordings.'''
    recordings = get_recordings_from_country(country='Netherlands')
    return dict(Counter([x.area for x in recordings if x.area]))

def get_recordings_with_location_info(args):
    '''
    return recordings based on provided location info (location = name) 
    and location_type (i.e. area or province )
    args        dict with info extracted from django request object
                to select requested recordings
    '''
    if args['location_type'] == 'area':
        recordings = get_recordings_with_areas_list([args['location']])
    if args['location_type'] == 'province':
        recordings = get_recordings_with_province_list([args['location']])
    return recordings

def get_all_finished_recording_pks_from_all_users(args):
    '''return list of recording pks (database ids) that are annotated.
    a recording is considered annotated if a user annotated all transcription
    in a given annotation session this does not mean all transcriptions
    (i.e. ocr lines) are annotated.
    args        dict with info extracted from django request object
                to select requested recordings
    '''
    output = []
    for aui in AnnotationUserInfo.objects.all():
        if aui.finished_recording_pks: 
            pks = aui.get_finished_recording_pks(args['session_key'])
            pks = [pk for pk in pks if pk not in output]
            output.extend(pks)
    return output

def filter_recordings_with_exclude_recording(args, recordings):    
    '''
    return recordings based on exclude setting (in args dict).
    recordings can be exclude because user annotated them or anyone
    annotated them.
    a recording is considered annotated if a user annotated all transcription
    in a given annotation session this does not mean all transcriptions
    (i.e. ocr lines) are annotated.
    args        dict with info extracted from django request object
                to select requested recordings
    '''
    aui = args['annotation_user_info']
    exclude = args['exclude_recordings']
    if exclude == 'none': 
        print('not excluding recordings')
        return recordings
    if exclude == 'annotated by me': 
        print('exclude recordings annotated by me')
        finished_pks = aui.get_finished_recording_pks(args['session_key'])
        print('finished pks',finished_pks)
    elif exclude == 'annotated by anyone':
        print('exclude recordings annotated by anyone')
        finished_pks = get_all_finished_recording_pks_from_all_users(args)
    else: raise ValueError(exclude, 'unknown value')
    temp = [x for x in recordings if x.pk not in finished_pks]
    print('exclude recordings',exclude,finished_pks,len(temp),len(recordings))
    if temp: recordings = temp
    return recordings

    
def get_recordings_with_annotation_user_info(args):
    '''
    return recordings based on information provided by the user.
    handles the resume case whereby the last state from an annotation run
    is reloaded
    args        dict with info extracted from django request object
                to select requested recordings
    '''
    aui = args['annotation_user_info']
    if args['resume'] == 'true' and aui.current_recording: 
        args['location'] = aui.current_location
        args['location_type'] = aui.current_location_type
    recordings = get_recordings_with_location_info(args)
    recordings = filter_recordings_with_exclude_recording(args, recordings)
    if args['resume'] == 'true' and aui.current_recording:
        print('resuming from last point',args['resume'])
        args['resume'] = 'false'
        print(args['resume'])
        pks = [x.pk for x in recordings]
        args['record_index'] = pks.index(aui.current_recording.pk)
        print(pks,args['record_index'],aui.current_recording,
            aui.current_recording.pk)
        try: args['record_index'] = pks.index(aui.current_recording.pk) 
        except ValueError: pass
        else: args['line_index'] = aui.current_line_index 
    return recordings, args

def get_exclude_indices_based_on_all_users(recording,args):
    '''
    return a list of ocr line (transcriptions) indices that should be skipped
    for this annotation run.
    args        dict with info extracted from django request object
                to select requested recordings
    '''
    exclude_indices= []
    for aui in AnnotationUserInfo.objects.all():
            if aui == args['annotation_user_info']:
                sk = args['session_key']
                indices = aui.recording_to_finished_ocrline_indices(recording,sk)
            else:
                indices = aui.recording_to_finished_ocrline_indices(recording)
            if indices:
                exclude_indices.extend(indices)
    return exclude_indices

def make_exclude_indices_with_exclude_transcriptions(args,recording):
    '''
    return a list of ocr line (transcriptions) indices that should be skipped
    for this annotation run.
    switches between exclude settings for transcriptions, either excluding
    transcriptions (ocr line) annotated by the user or by anyone or not
    skipping any transcriptions
    args        dict with info extracted from django request object
                to select requested recordings
    '''
    aui = args['annotation_user_info']
    exclude = args['exclude_transcriptions']
    indices = []
    if exclude == 'none': pass
    elif exclude == 'annotated by me' and aui.finished_recording_pks:
        sk = args['session_key']
        indices = aui.recording_to_finished_ocrline_indices(recording,sk)
    elif exclude == 'annotated by anyone':
        indices = get_exclude_indices_based_on_all_users(recording,args)
    return indices

def _update_annotation_user_info(args,recording):
    '''
    update the annotation user info with the current state.
    the annotation user info object is a django model that saves state
    of annotating for a given user, this allows selected parameters
    to persist between multiple submits (each annotation) and allows
    the user to resume at a later time
    '''
    aui = args['annotation_user_info']
    aui.current_line_index = args['line_index']
    aui.current_recording= recording
    aui.current_location = args['location']
    aui.current_location_type = args['location_type']
    aui.save()

def args_to_ocrline(args):
    '''
    updates the arg dict to render annotate template.
    the args dict provides information to select a transcription (i.e.
    an ocr line of an align object of a given recording. Based on this
    information an ocr line (transcription) is selected.
    The selected information is stored in the args dict and returned to
    the view to be rendered in the annotate template
    args        dict with info extracted from django request object
                to select requested recordings
    '''
    start = time.time()
    print(args, delta(start))
    aui = args['annotation_user_info']
    recordings, args = get_recordings_with_annotation_user_info(args)
    recording = recordings[args['record_index']]
    pks = [x.pk for x in recordings]
    print('select recording | pk',recording.pk, recording,
        'i',args['record_index'],'pk',aui.current_recording.pk,
        aui.current_recording, pks)
    mismatch = 100 - args['minimum_match']
    print('mismatch',mismatch,delta(start))
    exclude_indices= make_exclude_indices_with_exclude_transcriptions(args, 
        recording)
    print('exclude indices:',exclude_indices)
    min_lines = aui.min_lines if aui.min_lines else 10
    max_lines = aui.max_lines if aui.max_lines else 30
    ocr_lines = sample_ocr_lines(recording.align, 
        maximum_align_mismatch = mismatch,perc_lines = args['perc_lines'],
        exclude_indices = exclude_indices,min_lines =min_lines,
        max_lines=max_lines)
    if args['line_index'] < 0: args['line_index'] = len(ocr_lines) -1
    print('n ocr lines',len(ocr_lines),delta(start))
    if args['line_index'] >= len(ocr_lines) or len(ocr_lines) == 0: 
        print(recording, recordings)
        args['annotation_user_info'].add_finished_recording_pk(recording)
        args['record_index'] +=1
        if type(recordings) ==list: n_recordings = len(recordings) 
        else: n_recordings = recordings.count()
        if args['record_index'] >= n_recordings: 
            return 'done with all recordings'
        args['line_index'] = 0
        return args_to_ocrline(args)
    _update_annotation_user_info(args,recording)
    print('ocr_lines indices',[x.ocrline_index for x in ocr_lines])
    print('line_index',args['line_index'])
    args['ocrline'] = ocr_lines[args['line_index']]
    args['nocrlines'] = len(ocr_lines)
    args['line_index'] +=1
    print(args,delta(start))
    return args
    
    
def delta(start):
    '''helper function to show the amount of time elapsed.
    start       time in seconds to compute the delta
    '''
    return time.time() - start
    

    
