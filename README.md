# Chemical Experiment Summariser 

The program aims to extract key information from chemical experiments using pattern matching, dependency parsing and ChemDataExtractor to try and extrat key data. 

## Instructions 

After installing the dependencies and Spacy model the script can be run in the command line. 

### Example 

Extracting data from text file 

`python experiment_summariser.py --path "experiment_notes/exercise_experimentals.txt" --output_path "output/test_"`

As there is more than one not in the file the script will number the output. The output will be in the form of a JSON file that contains the following information. 

- Method: the method of reaction, in this case the code is fine tuned to map chemical additions 
- Solution_n : The script will try to identify the chemical solutions and populate the key with the following:
  - name: name of the chemical 
  - volume: volume of the chemical that is added 
- Type: Whether continous or portional experiment

User can also input experiment notes to the command line to test the output 

`python experiment_summariser --text "Hydrogen (2) was added to Oxgen."`

This will print to the screen the output 

`{'method': 'added', '
  solution_1': 
    {'chem_1': {'name': 'nitrogen', 'volume': '(500ml)'}}, 
  'solution_2': {'chem_1': {'name': 'ethanol', 'volume': '(20ml)'}}, 
 'type': 'Unspecified', 
 'annotated': 'A large flask of liquid [nitrogen] [(500ml)] was [added] to a flask of [ethanol] [(20ml)]'
 }`

## Evaluation 

There is also an evaluation script whereby the user can quickly check the output without reading and inspect if the summariser is managing to catch everything. I implemented a very basic metric, the evaluator adds a point for every correct match. The matches are matched using Levenshtein distance, if the matched string is more that 80% similar a point is given. The evaluator also adds a point to an incorrect variable to represent incorrect or missing matches. 

### Example 

`python evaluate.py --path_to_output "output/experiment_0.json" --path_to_gold "gold_output/experiment_0.json"`

The code will print the number of correct matches and the number of incorrect/missing matches. 

