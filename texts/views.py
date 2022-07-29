from django.shortcuts import render, redirect
from . models import Recording, Transcription
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


    
    
    
    
