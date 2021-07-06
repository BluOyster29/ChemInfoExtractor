import argparse 
from fuzzywuzzy import fuzz
import json

'''
This program runs a short and basic test to get a 
quick idea, without having to read the output, if 
the extractor is improving/regressing. The output
will be a positive integer. The higher 'score' 
means larger amount of positive extractions. 
Higher 'incorrect' implies missing or incorrect matches

'''

def args():

    """
    Arguments provided by user
    """

    p = argparse.ArgumentParser()
    p.add_argument('--path_to_output', type=str)
    p.add_argument('--path_to_gold', type=str)
    p = p.parse_args()
    return p

def load_object(path):

    # loads the json file into a py dict format

    return json.load(open(path))

def solution_test(process, experiment, score, incorrect):
    
    chem_names = []
    chem_vols = []
    for item in experiment:
        chem_names.append(process[item]['name'])

    for item in process:

        for c in chem_names:
            if fuzz.ratio(process[item].get('name'),c) > 80:
                score+=1
            else:
                incorrect+=1
    return score, incorrect

def evaluate_output(experiment_output, gold_output):
    
    """
    Basic script for testing the output of the info extractor. If 
    a key is an 80% match for the actual answer we are awarded a 
    point, likewise if it is under 80% we may consider that it is 
    probably the wrong answer so we will add a point to incorrect.
    This is just a simple method so far to generate some metrics 
    and find out if it might be improving

    args:
        experiment_output: loaded json object of the experiment output
        gold_out: same format but the golden standard manually created

    returns: 
        score: positive score of the amount of correct strings
        incorrect: number of missing or incorrect matches
    
    """

    results = {}
    score = 0
    incorrect = 0
    for key in gold_output:

        test_key = experiment_output.get(key)

        if not test_key:
            results[key] = 'missing'
            continue

        if type(test_key) == str:

            test_distance = fuzz.ratio(experiment_output[key], gold_output[key])

            if test_distance > 80:
                score += 1
                
            else:
                incorrect += 1
        elif type(test_key) == dict:

            score, incorrect = solution_test(experiment_output[key], gold_output[key], score, incorrect)
    return score, incorrect, results

def evaluate(args):
    mainargs = args()
    experiment_output = load_object(mainargs.path_to_output)
    gold_test = load_object(mainargs.path_to_gold)
    score, incorrect, results = evaluate_output(experiment_output, gold_test)

    print('\nCorrect Extractions: {}'.format(score))
    print('Incorrect Extractions : {}\n'.format(incorrect))
    return score, incorrect



if __name__ == '__main__':

    evaluate(args)
    