from django.urls import path
from . import views

app_name = 'texts'

annotate_url ='annotate/<str:location>/<str:location_type>/'
annotate_url += '<str:exclude_recordings>/<int:minimum_match>/<int:perc_lines>/'
annotate_url += '<str:exclude_transcriptions>/'

urlpatterns = [
	# path('',views.hello_world,name='hello_world'),
	path('',views.play,name='play'),
	path('play/',views.play,name='play'),
	path('select_province/',views.select_province,name='select_province'),
	path('select_area/',views.select_area,name='select_area'),
	path('annotate/',views.annotate,name='annotate'),
	path('annotate/<str:resume>',views.annotate,name='annotate'),
	path('home/',views.home,name='home'),
	path('help/',views.help,name='help'),
	path('resume/',views.resume,name='resume'),
	path(annotate_url,views.annotate,name='annotate'),
]
