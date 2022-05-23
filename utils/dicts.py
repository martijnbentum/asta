
#fr refers to french language
country_dict = {'nl':'Netherlands','be':'Belgium','fr':'Belgium','de':'Germany'}

#province dict
t = {'Lb':'Limburg','Ov':'Overijssel','Dr':'Drenthe'}
t.update({'BeAnt':'Belgisch Antwerpen','BeLb':'Belgisch Limburg'})
t.update({'Gn':'Groningen','Gl':'Gelderland','ZH':'Zuid-Holland'})
t.update({'Zh,NH':'Zuid-Holland,Noord-Holland'})
t.update({'BeOv':'Belgisch Oost-Vlaanderen','NH':'Noord-Holland'})
t.update({'BeWv':'Belgisch West-Vlaanderen','Ze':'Zeeland'})
t.update({'NB':'Noord-Brabant','Fr':'Friesland','BeBr':'Vlaams Brabant'})
t.update({'Fl,Ov':'Flevoland,Overijssel','Fl':'Flevoland','Ut':'Utrecht'})
t.update({'FrVl':'Friesland,Vlieland','ZH,NH':'Zuid-Holland,Noord-Holland'})
t.update({'WaBr':'Waals Brabant','Ri':'Noordrijn-Westfalen'})
t.update({'BeLb, Luik':'Luik,Belgisch Limburg','BeLu':'Luik'})
t.update({'Be, Luik':'Luik','BeHe':'Henegouwen','Fra':'Hauts-de-France'})
t.update({'Belb':'Belgisch Limburg','Dui':'Noordrijn-Westfalen'})
province_dict = t

# meta_data_header_to_english
t = {'id':'id','recid':'record_id', 'audiofilepath':'original_audio_filename'}
t.update({'kloekecode':'kloekecode','streek':'area'})
t.update({'openamedatum':'recording_date','duur':'duration','geslacht':'sex'})
t.update({'geboortejaar':'date_of_birth'})
t.update({'leeftijd':'age','opnameaard':'recording_type'})
meta_data_header_to_english = t

#recording_type 
t = {'monoloog en gesprek':'monologue,conversation'}
t.update({'gesprek':'conversation'})
t.update({'gesprek en lijst':'conversation,word list'})
t.update({'vragenlijst':'questionnaire'})
t.update({'gesprek aard opname is zeer informatief':'conversation'})
t.update({'gesprek ; (2e haspel: prenten benoemen)':'conversation'})
t.update({'vraaggesprek':'interview'})
t.update({'gesprek en lied':'conversation,song'})
t.update({'gesprek, lijst, lied/gedicht':'conversation,word list,song,poetry'})
t.update({'Voorlezen bestaand verhaal':'read aloud story'})
t.update({'gesprek en tekst':'conversation,text'})
t.update({'gesprek en fragment toneelstuk':'conversation,theater play'})
t.update({'grotendeels monoloog':'monologue'})
t.update({'lijst en voordracht':'word list,presentation'})
t.update({'gesprek en monoloog':'monologue,conversation'})
t.update({'gesprek en vragenlijst':'monologue,conversation'})
t.update({'gesprek en woordenlijst':'monologue,word list'})
t.update({'Praatje voor de RONO; radio-uitzending':'radio broadcast'})
t.update({'lied of gedicht':'song,poetry'})
t.update({'gesprek en lied/gedicht':'conversation,song,poetry'})
t.update({'Poelman is het meest aan het woord':'conversation,monologue'})
t.update({'gesprek, wel wat eenzijdig':'conversation'})
t.update({'monoloog':'monologue'})
t.update({'voornamelijk monoloog':'monologue'})
t.update({'Voorlezen bestaand verhaal en gesprek':'read aloud story,conversation'})
t.update({'Verhalende monoloog':'monologue'})
t.update({'Gespreksleider interviewt informant':'interview'})
t.update({'monoloog en lied/gedicht':'monologue,song,poetry'})
t.update({'monoloog en lied':'monologue,song'})
t.update({"vraag en antwoord, voornamelijk 'dialoog' ":'interview,conversation'})
t.update({"vraag en antwoord":'interview'})
t.update({'verklarend vanuit het dialect':'explanation'})
t.update({'monoloog':'monologue'})
t.update({'vraagzinnen':'questions'})
t.update({'lied':'song'})
t.update({'preek':'sermon'})
t.update({'12 stukjes monoloog+klinkerillustratie':'monologue,vowel demonstration'})
t.update({'monoloog, gesprek, lijst, lied':'monologue,conversation,word list,song'})
t.update({'monoloog, gesprek, lijst':'monologue,conversation,word list'})
t.update({'gesprek en toneelstuk':'conversation,theater play'})
t.update({'gesprek en fragment toneelstuk':'conversation,theater play'})
t.update({'gesprek en gedicht':'conversation,poetry'})
t.update({'voorlezen verhaal':'read aloud story'})
t.update({'monoloog en vragenlijst':'monologue,questionnaire'})
t.update({'monoloog en gesprek; voorlezen gedicht':'monologue,conversation,poetry'})
t.update({'Woordenlijst':'word list'})
t.update({'hoofdzakelijk monoloog':'monologue'})
t.update({'monoloog en gesprek; voorlezen gedicht ':'monologue,conversation,poetry'})
t.update({'verhalende monoloog':'monologue'})
t.update({'':''})
recording_type_dict = t

#gender
gender_dict = {'man':'male','vrouw':'female','man; vrou':'male,female','':''}
