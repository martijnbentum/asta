from django.shortcuts import render
from . models import Recording
from utils import align_ocr_asr as aoa

# Create your views here.

def hello_world(request):
    return render(request, 'texts/hello_world.html')

def play(request,pk = 2):
    recording = Recording.objects.get(pk = pk)
    a = aoa.Align(recording)
    o = a.ocr_lines[0]
    ocr = recording.ocrs[0]
    args = {'a':a,'o':o,'ocr':ocr}
    return render(request, 'texts/play.html',args)


    
    
