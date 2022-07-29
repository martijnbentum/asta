from django.urls import path
from . import views

app_name = 'texts'

annotate_url ='annotate/<str:location>/<str:location_type>/'
annotate_url += '<str:exclude>/<int:minimum_match>/<int:perc_lines>/'

urlpatterns = [
	# path('',views.hello_world,name='hello_world'),
	path('',views.play,name='play'),
	path('play/',views.play,name='play'),
	path('select_province/',views.select_province,name='select_province'),
	path('select_area/',views.select_area,name='select_area'),
	path('annotate/',views.annotate,name='annotate'),
	path(annotate_url,views.annotate,name='annotate'),
]
