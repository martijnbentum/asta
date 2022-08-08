from django.shortcuts import render, redirect
from . models import Recording, Transcription, Ocr, Asr, Annotation 
from . models import AnnotationUserInfo
from utils import align, select
import random, string


def home(request):
    args = {}
    print(request.user, str(request.user), str(request.user)== 'AnonymousUser')
    if str(request.user) =='AnonymousUser':
        return redirect('login')
    aui = get_annotation_user_info(request.user)
    args['annotation_user_info'] = aui
    return render(request, 'texts/home.html',args)

def help(request):
    return render(request, 'texts/help.html')

def resume(request):
    print('i am in resume view')
    aui = get_annotation_user_info(request.user)
    print('i am in resume view',aui.exclude_recordings,
        aui.exclude_transcriptions,aui.perc_lines, 
        aui.minimum_match, aui.session_key)
    return redirect('texts:annotate',
        resume = 'true',
        exclude_recordings = aui.exclude_recordings,
        exclude_transcriptions = aui.exclude_transcriptions,
        perc_lines = aui.perc_lines,
        minimum_match= aui.minimum_match,
        session_key = aui.session_key)
    

def hello_world(request):
    return render(request, 'texts/hello_world.html')

def update_annotion_user_info(aui, d):
    session_key = "".join(random.sample(string.ascii_lowercase, 21))
    aui.exclude_recordings = d['exclude_recordings']
    aui.exclude_transcriptions= d['exclude_transcriptions']
    aui.perc_lines = d['perc_lines']
    aui.minimum_match = d['minimum_match']
    aui.set_session(session_key)

def select_province(request):
    provinces = select.get_dutch_provinces()
    args = {'provinces':provinces}
    if request.method == 'POST':
        print(request.POST.keys())
        names = 'provinces,exclude_recordings,minimum_match,perc_lines'
        names += ',exclude_transcriptions'
        names = names.split(',')
        for name in names:
            print(name,request.POST[name])
        d = request.POST
        aui = get_annotation_user_info(request.user)
        update_annotion_user_info(aui,d)
        return redirect('texts:annotate',
            location = d['provinces'], 
            location_type = 'province',
            exclude_recordings = d['exclude_recordings'],
            exclude_transcriptions= d['exclude_transcriptions'],
            minimum_match = d['minimum_match'], 
            perc_lines = d['perc_lines'],
            session_key = aui.session_key)
    return render(request, 'texts/select_province.html', args)

def select_area(request):
    areas= select.get_dutch_areas()
    args = {'areas':areas}
    if request.method == 'POST':
        print(request.POST.keys())
        names = 'areas,exclude_recordings,minimum_match,perc_lines'
        names += ',exclude_transcriptions'
        names = names.split(',')
        for name in names:
            print(name,request.POST[name])
        d = request.POST
        aui = get_annotation_user_info(request.user)
        update_annotion_user_info(aui,d)
        return redirect('texts:annotate',
            location = d['areas'], 
            location_type = 'area',
            exclude_recordings = d['exclude_recordings'],
            exclude_transcriptions= d['exclude_transcriptions'],
            minimum_match = d['minimum_match'], 
            perc_lines = d['perc_lines'],
            session_key = aui.session_key)
    return render(request, 'texts/select_area.html', args)

def _handle_annotation(annotation,args):
    if annotation:
        args['corrected_transcription'] = annotation.corrected_transcription
        args['alignment'] = annotation.alignment
        args['already_annotated'] = 'true'
    else:
        args['corrected_transcription'] = ''
        args['alignment'] = ''
        args['already_annotated'] = 'false'
    return args


def get_annotation_user_info(user):
    try: user.annotationuserinfo
    except AnnotationUserInfo.DoesNotExist:
        aui = AnnotationUserInfo(user = user)
        aui.save()
    return user.annotationuserinfo

def annotate(request, location= '', location_type= '', exclude_recordings = 'none',
    exclude_transcriptions = 'none', minimum_match = 35, perc_lines = 20, 
    record_index = 0, line_index = 0,resume = 'false', session_key = ''):
    print('request',request.user)
    print('post',request.POST)
    aui = get_annotation_user_info(request.user)
    if request.POST:
        line_index, record_index= handle_annotate_post(request)
        location, location_type, resume = _get_info(request)
        print(location,location_type, resume, 99999)
    print('resume has this value in annotate view',resume)
    args = {'location':location,'location_type':location_type,
        'exclude_recordings':exclude_recordings,
        'exclude_transcriptions':exclude_transcriptions,
        'minimum_match':minimum_match,
        'perc_lines':perc_lines, 'record_index':record_index,
        'line_index':line_index,'annotation_user_info':aui, 'resume':resume,
        'session_key':session_key}
    args = select.args_to_ocrline(args)
    print('args',args)
    o = args['ocrline']
    annotation = load_annotation(recording=o.recording,asr=o.align.asr,
        ocrline_index= o.ocrline_index, user = request.user)
    print('annotation',annotation)
    args = _handle_annotation(annotation,args)
    return render(request, 'texts/annotate.html',args)

def _get_indices(request):
    line_index, record_index= 0,0
    try: line_index = int(request.POST['line_index'])
    except ValueError: pass
    try: record_index = int(request.POST['record_index'])
    except ValueError: pass
    return line_index, record_index

def _get_info(request):
    resume = 'false'
    location, location_type, session_key = '','',''
    if 'resume' in request.POST.keys():
        resume= request.POST['resume']
        location = request.POST['location']
        location_type = request.POST['location_type']
    return location, location_type, resume

def _get_instance(request, model, input_name):
    if input_name in request.POST.keys():
        pk = request.POST[input_name]
    else: return None
    try: return model.objects.get(pk = pk)
    except model.DoesNotExists: return None

def request_to_annotation_dict(request):
    d = {}
    d['recording'] = _get_instance(request,Recording,'recording_pk')
    d['asr'] = _get_instance(request,Asr,'asr_pk')
    d['ocrline_index'] = None
    try: d['ocrline_index']=int(request.POST['ocrline_index'])
    except ValueError: pass
    d['user'] = request.user
    d['alignment'] = request.POST['quality']
    d['corrected_transcription'] = request.POST['corrected_transcription']
    print('annotation dict', d)
    return d

def make_annotation_load_dict(annotation_dict= None, recording=None, asr=None, 
    ocrline_index = None, user = None):
    d = {}
    if annotation_dict == None:
        d = {'recording':recording, 'asr':asr, 'ocrline_index':ocrline_index,'user':user}
    else:
        for name in 'recording,asr,ocrline_index,user'.split(','):
            d[name] = annotation_dict[name]
    return d

def load_annotation(load_dict = None, recording = None, asr = None, ocrline_index = None,
    user = None):
    if load_dict == None:
        print('loading with:',recording,asr,ocrline_index,user)
        load_dict = make_annotation_load_dict(recording =recording, asr= asr, 
            ocrline_index = ocrline_index, user = user)
    try:
        annotation = Annotation.objects.get(**load_dict)
        print('loaded annotation', annotation, annotation.pk)
        return annotation
    except Annotation.DoesNotExist: 
        print('could not load annotation')
        return None
    

def load_make_annotation(annotation_dict):
    load_dict = make_annotation_load_dict(annotation_dict = annotation_dict)
    a = load_annotation(load_dict = load_dict)
    if not a:
        a= Annotation(**annotation_dict)
        a.save()
        print('made annotation:', a)
    else:
        a.alignment = annotation_dict['alignment']
        a.corrected_transcription= annotation_dict['corrected_transcription']
        a.save()
    a.add_ocrline_index_to_user_info()
    return a
        
    
def handle_annotate_post(request): 
    line_index, record_index = _get_indices(request)
    prev_next= request.POST['prev_next']
    print('prev_next',prev_next, line_index, record_index)
    if prev_next == 'previous':
        if line_index == 1:
            print('going back a recording')
            record_index -= 1 
            line_index = -1
        else: 
            line_index -= 2
            print('going back a transcription')
    if prev_next == 'none':
        print('prev_next',prev_next, line_index, record_index)
        annotation_dict = request_to_annotation_dict(request)
        print('annotation dict ---', annotation_dict)
        annotation = load_make_annotation(annotation_dict)
        print('annotation',annotation, annotation.__dict__)
    return line_index, record_index 
    
    
