from . import read_tsv
from . import read_kloeke
# from django.core.exceptions import DoesNotExist
from texts.models import Country


def load_city():
	pass

def load_area():
	pass

def load_country():
	for name in 'Netherlands,Belgium,Germany'.split(','):
		try: Country.objects.get(name = name)
		except Country.DoesNotExist:
			print('creating country',name)
			c = Country(name=name)
			c.save()
		else:print(name,'already exists')
	


