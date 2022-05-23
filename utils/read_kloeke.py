from . import dicts

filename = 'data/2022_KloekeCodes_eWND_utf8.txt'

def load_kloeke_codes():
	t = open(filename).read().split('\n')
	t = [x.split('\t') for x in t if x]
	header = t[0]
	data = t[1:]
	return header, data

def handle_kloeke_codes():
	header, data = load_kloeke_codes()
	output = []
	for line in data:
		output.append(line_to_dict(line,header))
	return output


def line_to_dict(line,header):
	d = {}
	for i,column_name in enumerate(header):
		if column_name == 'point':
			latitude, longitude = line[i].split(',')
			d['latitude'] = float(latitude.strip())
			d['longitude'] = float(longitude.strip())
		elif column_name == 'country':
			d['country'] = dicts.country_dict[line[i].lower()]
		elif column_name == 'dictionary': continue
		elif column_name == 'province':
			d['province'] = dicts.province_dict[line[i]]
		else:
			d[column_name] = line[i]
	return d

