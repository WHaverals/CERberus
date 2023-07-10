import re
import Levenshtein
from typing import Dict
import pandas as pd
import json

import re
import Levenshtein
from typing import Dict
import pandas as pd
import json

def cer(reference: str, hypothesis: str, 
        ignore_punctuation: bool = False, 
        ignore_case: bool = False, 
        ignore_whitespace: bool = False, 
        ignore_numbers: bool = False,
        ignore_chars: str = None,
        ignore_newlines_and_returns: bool = False,
        debug: bool = True,
        return_char_stats: bool = True,
        unicode_ranges: Dict[str, list] = {},
        discard_lines_with_chars: str = None,
        replace_chars: str = None,
        replacement_chars: str = None,
        save_path: str = None) -> Dict[str, float]:

    # If replace_chars and replacement_chars are provided, make the replacements in both strings
    if replace_chars is not None and replacement_chars is not None:
        reference = reference.replace(replace_chars, replacement_chars)
        hypothesis = hypothesis.replace(replace_chars, replacement_chars)

    # Split reference and hypothesis into lines
    reference_lines = reference.splitlines()
    hypothesis_lines = hypothesis.splitlines()

    # Keep track of original number of lines
    original_lines_count = len(reference_lines)

    # If discard_chars is provided, exclude corresponding lines in both strings if either contains any of the specified characters
    if discard_lines_with_chars is not None:
        combined_lines = list(zip(reference_lines, hypothesis_lines))
        combined_lines = [lines for lines in combined_lines if not any(char in lines[0] for char in discard_lines_with_chars) and not any(char in lines[1] for char in discard_lines_with_chars)]

        # Unzip the lines back into separate lists
        reference_lines, hypothesis_lines = zip(*combined_lines)

    # Calculate the number of lines discarded
    discarded_lines_count = original_lines_count - len(reference_lines)
    print(f"Discarded lines: {discarded_lines_count}")
    
    # Join the lines back into a single string
    reference = "\n".join(reference_lines)
    hypothesis = "\n".join(hypothesis_lines)
    
    if ignore_case:
        reference = reference.lower()
        hypothesis = hypothesis.lower()

    if ignore_punctuation:
        reference = re.sub(r'[^\w\s]', '', reference)
        hypothesis = re.sub(r'[^\w\s]', '', hypothesis)
        
    if ignore_whitespace:
        reference = re.sub(r'\s', '', reference)
        hypothesis = re.sub(r'\s', '', hypothesis)
        
    if ignore_numbers:
        reference = re.sub(r'\d', '', reference)
        hypothesis = re.sub(r'\d', '', hypothesis)
        
    # if ignore_chars is specified, remove each of these characters from both strings
    if ignore_chars is not None:
        for char in ignore_chars:
            reference = reference.replace(char, '')
            hypothesis = hypothesis.replace(char, '')
            
    # Ignore newline and carriage return characters if ignore_newlines_and_returns is True
    if ignore_newlines_and_returns: # <- New condition
        reference = reference.replace('\n', ' ').replace('\r', '')
        hypothesis = hypothesis.replace('\n', ' ').replace('\r', '')
    
    if len(reference) == 0:
        raise ValueError("Reference string length cannot be zero.")

    numCor, numSub, numIns, numDel, alignments = levenshtein(reference, hypothesis)

    if debug:
        print("Alignment table:")
        for a in alignments:
            print(a)

    numCount = len(reference)

    cer_value = round(((numSub + numIns + numDel) / numCount)*100, 2)

    # Prepare the results dictionary
    results = {
        'CER': cer_value,
        'numCor': numCor,
        'numSub': numSub,
        'numIns': numIns,
        'numDel': numDel,
        'numCount': numCount,
        'original_lines_count': original_lines_count,
        'discarded_lines_count': discarded_lines_count
    }

    # Initialize character statistics dictionary
    char_stats = {}

    # Add a function to check if a character belongs to a specific Unicode range
    def in_unicode_range(char: str, ranges: list) -> bool:
        code_point = ord(char)
        return any(start <= code_point <= end for start, end in ranges)

    # Initialize a dictionary for character block statistics
    block_stats = {key: {'count': 0, 'correct': 0, 'incorrect': 0} for key in unicode_ranges}
    
    # Initialize confusion statistics dictionary
    confusion_stats = {}
    
    # Iterate over alignments and update block statistics
    for char1, char2, operation in alignments:
        if char1 != '_':
            for block_name, ranges in unicode_ranges.items():
                if in_unicode_range(char1, ranges):
                    block_stats[block_name]['count'] += 1
                    if operation == 'equal':
                        block_stats[block_name]['correct'] += 1
                    else:
                        block_stats[block_name]['incorrect'] += 1
                    break

            # Update char_stats dictionary
            if char1 not in char_stats:
                char_stats[char1] = {'count': 0, 'correct': 0, 'incorrect': 0}

            char_stats[char1]['count'] += 1

            if operation == 'equal':
                char_stats[char1]['correct'] += 1
            else:
                char_stats[char1]['incorrect'] += 1

            # Update confusion_stats dictionary
            if operation == 'substitution' or operation == 'insertion' or operation == 'deletion':
                if char1 not in confusion_stats:
                    confusion_stats[char1] = {}
                if char2 not in confusion_stats[char1]:
                    confusion_stats[char1][char2] = 0
                confusion_stats[char1][char2] += 1
                
    # Compute precision for each character block
    for block, stats in block_stats.items():
        total = stats['correct'] + stats['incorrect']
        if total > 0:
            stats['correct_ratio'] = round((stats['correct'] / total * 100), 2)
            stats['incorrect_ratio'] = round((stats['incorrect'] / total * 100), 2)
        else:
            stats['correct_ratio'] = None
            stats['incorrect_ratio'] = None

    # Convert block_stats to a pandas DataFrame
    block_stats_df = pd.DataFrame.from_dict(block_stats, orient='index')

    # Convert block_stats_df to a list of dictionaries and include it in the results
    results['blockStats'] = block_stats_df.reset_index().rename(columns={"index": "Block"}).to_dict('records')

    # Compute precision for each character
    for char, stats in char_stats.items():
        stats['correct_ratio'] = round((stats['correct'] / (stats['correct'] + stats['incorrect']) * 100), 2)
        stats['incorrect_ratio'] = round((stats['incorrect'] / (stats['correct'] + stats['incorrect']) * 100), 2)
        
    # Convert char_stats to a pandas DataFrame and sort it
    char_stats_df = pd.DataFrame.from_dict(char_stats, orient='index').sort_values(['count', 'correct_ratio'], ascending=[False, False])

    # Include charStats in the results if return_char_stats is True
    if return_char_stats:
        results['charStats'] = char_stats_df.reset_index().rename(columns={"index": "Character"}).to_dict('records')

    # Convert confusion_stats to a pandas DataFrame and compute ratio
    # ! ratio here is the confusion count between a specific pair of characters to the total count of all confusions for that specific, correct character
    confusion_data = []
    for correct_char, generated_chars in confusion_stats.items():
        total_confusion_count = sum(generated_chars.values())
        for generated_char, count in generated_chars.items():
            ratio = round((count / total_confusion_count * 100), 2)
            confusion_data.append([correct_char, generated_char, count, ratio])
    confusion_df = pd.DataFrame(confusion_data, columns=['correct', 'generated', 'count', 'ratio'])


    # Convert DataFrame to a list of dictionaries
    confusion_dict_list = confusion_df.to_dict('records')
    results['confusionStats'] = confusion_dict_list

    if save_path is not None:
        results_dict = results.copy()  # Copy the results to not modify the original
        results_dict['blockStats'] = results_dict['blockStats'].to_dict()
        if 'charStats' in results_dict:
            results_dict['charStats'] = results_dict['charStats'].to_dict()
        
        with open(save_path, 'w') as f:
            json.dump(results_dict, f, indent=4)
    
    return results


def levenshtein(s1: str, s2: str) -> [int, int, int, int, list]:
    edit_ops = Levenshtein.editops(s1, s2)
    opcodes = Levenshtein.opcodes(edit_ops, s1, s2)
    numSub = sum(1 for op in edit_ops if op[0] == 'replace')
    numIns = sum(1 for op in edit_ops if op[0] == 'insert')
    numDel = sum(1 for op in edit_ops if op[0] == 'delete')

    alignments = []
    for opcode, i1, i2, j1, j2 in opcodes:
        if opcode == 'replace':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                alignments.append((s1[i], s2[j], 'substitution'))
        elif opcode == 'insert':
            for j in range(j1, j2):
                alignments.append(('_', s2[j], 'insertion'))
        elif opcode == 'delete':
            for i in range(i1, i2):
                alignments.append((s1[i], '_', 'deletion'))
        elif opcode == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                alignments.append((s1[i], s2[j], 'equal'))

    numCor = len(s1) - numSub - numDel

    return numCor, numSub, numIns, numDel, alignments