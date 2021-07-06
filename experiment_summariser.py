import argparse
import re
import spacy
import json
from chemdataextractor.doc import Document, Paragraph
from spacy import displacy
from nltk.tokenize.punkt import PunktSentenceTokenizer

'''
The experiment summariser aims to extract key data from a 
chemistry experiment. The summariser can manage the following
scenarios: 

1. The method of experimentation is declared in the first sentence
2. All chemicals are spelt correctly and recognised by ChemDataExtractor
3. It works better if the text is in the active voice (solution1 is X to solution 2)

The program outputs a json wherby the keys represent the data that is 
being sorted after and subkey provide further information. For example 
if a solution contains more than one chemical. The summariser uses regular
expression to match chemical unit/volumes as so far the are contained within
brackets.
'''

nlp = spacy.load("en_core_web_sm")
volumes = re.compile(r"\([;×,~\+:/\w,°%.\- =]+\)")
tokenizer = PunktSentenceTokenizer()

def args():

    '''
    Arguments to be passed to the summariser
    '''

    p = argparse.ArgumentParser()
    p.add_argument('--path', type=str, help="Path to text")
    p.add_argument('--text', type=str, help="Input text")
    p.add_argument('--output_path', type=str, help="Path to output file")
    p = p.parse_args()
    return p

def fetch_text(path):

    '''
    Cleanup script for text containing multiple experiments
    seperated by empty line
    '''

    doc = open(path).read().split('\n')

    return [i for i in doc if i != '']

def format_spans(span):
    chems = []
    for i in span:
        chems.append((i.text, i.start, i.end))
        
    return chems

def remove_chems(text, sorted_chems):

    '''
    Script not in use. The script removes the chemicals from 
    the text, I implemented this to try and improve the accuracy
    of the NLP pipeline as it is unlikely the model will be able to parse
    the chemical names. It turned out it handles them pretty well 
    so the script is not in use
    '''

    phrases = []
    marker = 0
    chem_map = {}

    for idx, cem in enumerate(sorted_chems):
        chem_map[f'chem_{idx}'] = cem

        start_cem = cem[1]
        end_cem = cem[2]

        phrases.append(text[marker:start_cem])
        marker = end_cem

        if idx == len(sorted_chems)-1:
            phrases.append(text[marker:])

    return 'chem'.join(phrases), chem_map
    
def extract_chems(text):
    
    chems = Document(text).cems
    chems = format_spans(chems)
    sorted_chems = sorted(chems, key= lambda x: x[1])
    removed_chems, chem_map = remove_chems(text, sorted_chems)
    
    return removed_chems, sorted_chems, text, chem_map

def extract_cem_vols(text):
    
    '''
    The script extracts the chemical volumes from the text
    and matches them to the chemical that has already been
    identified. If the volume can not be extracted a placeholder
    is included. The chemicals are also numbered.
    '''

    chem_vol = {}

    for idx,  i in enumerate(extract_cems(text)):
        idx += 1
        chem_vol[f'chem_{idx}'] = {}

        # Regex expression matches common volume formats
        search= re.search(f"{i} \([;×,~\+:/\w,°%.\- =]+\)", text)

        if search:

            chem, vol = search.group(0).split(' (')
            vol = f'({vol}'
            chem_vol[f'chem_{idx}']['name'] = chem
            chem_vol[f'chem_{idx}']['volume'] = vol
        else:
            chem_vol[f'chem_{idx}']['name'] = i
            chem_vol[f'chem_{idx}']['volume'] = 'unspecified'

    return chem_vol

def extract_cems(text):

    '''
    Small script that extracts chemical names, it relies
    on ChemDataExtractor to identify the cheicals
    '''

    cems = Document(text).cems
    return [i.text for i in cems]

def remove_vols(text):
    
    '''
    Another script for removing tokens, this removes the volume 
    tokens. I again tried this to help out the dependency parser
    but it wasn't necessary in the end.
    '''
    text_vols = []
    
    for match in re.finditer(volumes, text):
        text_vols.append((match.group(0),match.start(), match.end()))
        
    phrases = []
    marker = 0
    vol_map = {}
    for idx, vol in enumerate(text_vols):
        vol_map[f'vol_{idx}'] = vol[0]
        
        text = re.sub(vol[0], '', text)
        
    text = re.sub("\(\)", '', text)
    text = re.sub('  ', ' ', text)
    return text, vol_map

def gather_process(text):
    
    '''
    This script tries to identify the main clause. This is 
    done by finding the root of the sentences verb phrase. 
    In theory this will describe the relation shit between
    the two noun phrases which make up the experiment. 

    args:
        text: The raw text of the epxeriment

    returns:
        process: The dictionary formatted output of the experiment 
        summariser
    '''
    first_sentence = tokenizer.tokenize(text)[0]

    process={
             'method' : None}

    doc = nlp(first_sentence)

    for idx, i in enumerate(doc):

        if i.dep_ == 'ROOT':

            if i.text not in ['added', 'evacuated']:
                continue
                
            phrase_1 = doc[:idx]

            method = i.text
            phrase_2 = doc[idx+1:]
            process['solution_1']=extract_cem_vols(doc[:idx].text)
            process['solution_2']=extract_cem_vols(doc[idx+1:].text)
            process['method']=i.text#
            process['type'] = 'Unspecified'
            break
            
    return process

def format_output_text(input_text, process):
    
    '''
    Script annotates the input text with the matched 
    entities and appends it to the json.
    '''

    for key in process:
        
        if type(process[key]) == str:
            
            if process[key] == 'Unspecified':
                continue
            
            input_text = re.sub(process[key], f"[{process[key]}]", input_text)
            
        elif type(process[key]) == dict:
            
            for subkey in process[key]:
                
                for param in process[key][subkey]:
                    
                    input_text = re.sub(process[key][subkey][param], "[{}]".format(process[key][subkey][param]), input_text)
    
    input_text = re.sub('\)\]\)', ')]', input_text)
    input_text = re.sub('\(\[\(', '[(', input_text)
    process['annotated'] = input_text
    return process, input_text

def summarise(text):
    sentences = tokenizer.tokenize(text)
    test_sentence = sentences[0] # main info
    #test_text, vols = remove_vols(test_sentence)
    process = gather_process(test_sentence)
    process, output_text=format_output_text(test_sentence, process)
    return process

def output_json(object, path):

    print('Outputting to : {}'.format(path))
    with open(path, 'w') as file:
        json.dump(object, file)

def experiment_summariser(experiment):
    
    '''
    Top level command
    '''

    mainargs = args()

    if mainargs.path:

        '''
        For bulk exports of experiments when a text 
        with multiple experiments seperated by newline 
        are present 
        '''
        experiments = fetch_text(mainargs.path)
        processes = {}
        for idx, ex in enumerate(experiments):

            process = summarise(ex)
            
            path = mainargs.output_path + str(idx) + '.json'
            output_json(process, path)  
            processes[idx]=process

        return processes

    elif mainargs.text:
        '''
        
        '''
        process = summarise(mainargs.text)
        output_json(process, mainargs.output_path)   
        return process

if __name__ == '__main__':
    experiment_summariser(args())