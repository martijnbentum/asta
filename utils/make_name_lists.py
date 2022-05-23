from . import read_tsv
from . import read_kloeke

def make_province_list(soundbites_metadata = None, kloeke = None):
	if not soundbites_metadata: 
		soundbites_metadata, _ = read_tsv.soundbites_to_metadata()
	if not kloeke:
		kloeke = read_kloeke.handle_kloeke_codes()
	provinces = []
	for line in soundbites_metadata + kloeke:
		if ',' in line['province']:
			for province in line['province'].split(','):
				if province not in provinces: provinces.append(province)
		elif line['province'] not in provinces: 
			provinces.append(line['province'])
	return provinces

def _add_to_city_list(city,city_list):
	names = [x['name'] for x in city_list]
	if not city['name'] in names: city_list.append(city)

def _make_city(city_str, kloeke_str,province_str):
	if '/' in city_str:
		name, alt_name = city_str.split('/')
	else: name, alt_name = city_str.strip(), ''
	city = {'name':name.strip(),'alternative_name':alt_name.strip()}
	city['kloeke'] = kloeke_str
	city['province'] = province_str
	return city

def _add_csv_city(city_csv,kloeke_csv,province_csv,city_list):
	cs = city_csv.split(',')
	ks = kloeke_csv.split(',')
	ps = province_csv.split(',')
	for city_str,kloeke_str,province_str in zip(cs,ks,ps):
		city = _make_city(city_str, kloeke_str,province_str)
		_add_to_city_list(city,city_list)
	

def make_city_list_sb(soundbites_metadata = None):
	if not soundbites_metadata: 
		soundbites_metadata, _ = read_tsv.soundbites_to_metadata()
	cities = []
	for line in soundbites_metadata:
		city_str = line['city']
		kloeke_str = line['kloekecode']
		province_str = line['province']
		if city_str == 'Cabauw' and province_str == 'Utrecht':
			kloeke_str = 'K021a'
		if ',' in city_str:
			_add_csv_city(city_str,kloeke_str,province_str,cities)
		else: 
			city = _make_city(city_str,kloeke_str,province_str)
			_add_to_city_list(city,cities)
	return cities

def make_city_list_kloeke(kloeke = None):
	if not kloeke:
		kloeke = read_kloeke.handle_kloeke_codes()
	for d in kloeke:
		name = d['place']
		if not '/' in name: 
			d['name']= name
			continue
		d['name']= name.split('/')[0].strip()
		d['alternative_name'] = name.split('/')[1].strip()
		if len(name.split('/')) > 2:
			d['other_alternative_names'] = ' / '.join(name.split('/')[2:])
	return kloeke

def make_kloeke_dict():
	kloeke = make_city_list_kloeke()
	output = {}
	for d in kloeke:
		output[d['kloeke']] = d
	return output

def compare_soundbites_cities_with_kloeke(soundbites_metadata=None):
	city_sb = make_city_list_sb(soundbites_metadata)
	city_kloeke = make_city_list_kloeke()
	matches,partial_c,partial_k,not_found = [],[],[],[]
	for city in city_sb:
		name, kloeke = city['name'], city['kloeke'].lower()
		found = False
		for k in city_kloeke:
			if name == k['name'] and kloeke == k['kloeke'].lower():found = True
			if name == k['name'] and kloeke == k['kloeke'].lower():
				matches.append([city,k])
			elif name == k['name']:partial_c.append([city,k])
			elif kloeke == k['kloeke'].lower():partial_k.append([city,k])
		
		if not found: not_found.append([city,k])
	return matches,partial_c,partial_k,not_found
	


