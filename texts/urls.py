from django.urls import path
from . import views

app_name = 'texts'

urlpatterns = [
	# path('',views.hello_world,name='hello_world'),
	path('',views.play,name='play'),
	path('play/',views.play,name='play'),
]
