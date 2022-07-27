from django.shortcuts import render
from . models import Recording, Transcription
from utils import align_ocr_asr as aoa
import random


def hello_world(request):
    return render(request, 'texts/hello_world.html')

def play(request,pk = 2):
    post = request.method 
    if request.method == 'POST':
        if 'quality' in request.POST.keys():print('quality',request.POST['quality'])
        else:print(request.POST.keys(),'quality not found')
    if pk:
        recording = Recording.objects.get(pk = pk)
    else: 
        recordings = Recording.objects.filter(ocr_transcription_available=True)
        recording = random.sample(list(recordings),1)[0]
    a = aoa.Align(recording)
    if not hasattr(a,'ocr_lines'): o = ''
    else: o = random.sample(a.filter_ocr_lines(),1)[0]
    ocr = recording.ocrs[0]
    args = {'a':a,'o':o,'ocr':ocr,'post':post}
    return render(request, 'texts/play.html',args)


    
    
    
