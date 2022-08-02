from django.shortcuts import render, redirect
from . models import Recording, Transcription, Ocr, Asr
from utils import align, select
import random


def hello_world(request):
    return render(request, 'texts/hello_world.html')

def select_province(request):
    provinces = select.get_dutch_provinces()
    args = {'provinces':provinces}
    if request.method == 'POST':
        print(request.POST.keys())
        for name in 'provinces,exclude,minimum_match,perc_lines'.split(','):
            print(name,request.POST[name])
        d = request.POST
        return redirect('texts:annotate',location = d['provinces'], 
            location_type = 'province',exclude = d['exclude'],
            minimum_match = d['minimum_match'], perc_lines = d['perc_lines'])
    return render(request, 'texts/select_province.html', args)

def select_area(request):
    areas= select.get_dutch_areas()
    args = {'areas':areas}
    if request.method == 'POST':
        print(request.POST.keys())
        for name in 'areas,exclude,minimum_match,perc_lines'.split(','):
            print(name,request.POST[name])
        d = request.POST
        return redirect('texts:annotate',location = d['areas'], 
            location_type = 'area',exclude = d['exclude'],
            minimum_match = d['minimum_match'], perc_lines = d['perc_lines'])
    return render(request, 'texts/select_area.html', args)

def annotate(request, location= '', location_type= '', exclude = 'None',
    minimum_match = 35, perc_lines = 20, record_index = 0, line_index = 0):
    print('request',request)
    print('post',request.POST)
    if request.POST:
        line_index, record_index, annotation_dict = handle_annotate_post(request)
    args = {'location':location,'location_type':location_type,
        'exclude':exclude,'minimum_match':minimum_match,
        'perc_lines':perc_lines, 'record_index':record_index,
        'line_index':line_index}
    args = select.args_to_ocrline(args)
    return render(request, 'texts/annotate.html',args)

def play(request,pk = 2):
    post = request.method 
    if request.method == 'POST':
        if 'quality' in request.POST.keys():
            print('quality',request.POST['quality'])
        else:print(request.POST.keys(),'quality not found')
    if pk:
        recording = Recording.objects.get(pk = pk)
    else: 
        recordings = Recording.objects.filter(ocr_transcription_available=True)
        recording = random.sample(list(recordings),1)[0]
    a = align.Align(recording)
    if not hasattr(a,'ocr_lines'): o = ''
    else: o = random.sample(a.filter_ocr_lines(),1)[0]
    ocr = recording.ocrs[0]
    args = {'a':a,'o':o,'ocr':ocr,'post':post}
    return render(request, 'texts/play.html',args)


def _get_indices(request):
    line_index, record_index= 0,0
    try: line_index = int(request.POST['line_index'])
    except ValueError: pass
    try: record_index = int(request.POST['record_index'])
    except ValueError: pass
    return line_index, record_index

def _get_instance(request, model, input_name):
    if input_name in request.POST.keys():
        pk = request.POST[input_name]
    else: return None
    try: return model.objects.get(pk = pk)
    except model.DoesNotExists: return False
    
def handle_annotate_post(request): 
    line_index, record_index = _get_indices(request)
    names =  'ocr_transcription_pk,asr_transcription_pk,recording_pk'
    names = names.split(',')
    models = [Transcription,Transcription,Recording]
    d = {}
    for model,name in zip(models,names):
        instance = _get_instance(request, model,name)
        print(model,name,instance)
        d[name] = instance
    d['ocrline_index']=request.POST['ocrline_index']
    print('annotation dict', d)
    return line_index, record_index, d
    
    
