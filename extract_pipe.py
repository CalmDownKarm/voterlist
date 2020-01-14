
import re
import os
import glob
import json
import pytesseract
from PIL import Image
from tqdm import tqdm


regexes = {
    'Name': "(?<=Name)(.*)",
    'Relative': "(Father|Mother|Husband)\\\'s.*?Name.*?:(.*)",
    'Age': "Age:\s([0-9]+)",
    'Sex': "Sex:\s(MALE|FEMALE|THIRD GENDER)"
}
compiled_regexes = {k: re.compile(v) for k, v in regexes.items()}

row_sizes = {
    'row_height': 290,
    'box_width': 752,
}

voter_id_offset = {'left': 460, 'top': 0, 'right': 0, 'bottom': -200}


def get_string_from_row(row):
    '''Takes in a single row (Image Object), gets 3 text strings out'''
    box_width = row_sizes['box_width']

    return [pytesseract.image_to_string(row.crop((i * box_width, 0, (i + 1) * box_width, row.size[1])))
            for i in range(3)]


def get_voter_id(row):
    ''' Takes a row and returns voter IDs '''

    box_width = row_sizes['box_width']
    return [pytesseract.image_to_string(row.crop((i * box_width + voter_id_offset['left'],
                                                  0 +
                                                  voter_id_offset['top'], (
                                                      i + 1) * box_width + voter_id_offset['right'],
                                                  row.size[1] + voter_id_offset['bottom'])))
            for i in range(3)]


def get_first_offsets(width, height):
    # First page offsets
    return {
        #     'name and reservation status of parliamentary constituencies': (0, 300, width, 450),
        'Sections': (0, 1060, width/2-200, 1800),  # Sections in PDF
        # town,ward,police,tehsil,district,pin
        'Details': (width/2+200, 1060, width, 1800),
        # no and name of polling station
        'Polling Station': (0, 2000, width/2+50, height-1050),
        'Voters': (width/6+500, height-950, width, height-800)
    }


def get_voter_offsets(width, height):
    return {
        'header': (0, 0, width, 200),
        # As close to row lines as possible
        'rows': (101, 210, width-120, height-370),
    }


def handle_sheet(filename):
    '''Takes a filename and returns a list of strings inside it'''
    image = Image.open(filename)
    width, height = image.size
    if os.path.basename(filename) == 'page_1.png':
        return {
            k: pytesseract.image_to_string(image.crop(v))
            for k, v in get_first_offsets(width, height).items()
        }
    else:
        #         import pdb; pdb.set_trace()
        header, all_rows = (image.crop(v)
                            for v in get_voter_offsets(width, height).values())
        rows = [all_rows.crop((0, i * row_sizes['row_height'], all_rows.size[0],
                               (i+1) * row_sizes['row_height'])) for i in range(10)]
        strings = [get_string_from_row(row) for row in rows]
        # Tanzil's
        voter_ids = [get_voter_id(row) for row in rows]
        cleaned_vid = []
        temp = []
        # cleaning the Voter IDs extracted
        for row_ids in voter_ids:
            for data in row_ids:
                data = data.split('\n')
                for stuff in data:
                    if len(stuff) == 10:
                        temp.append(stuff)
                        continue
                    
                    temp.append('')
                    
            cleaned_vid.append(temp)
            temp = []

        print('LOOK HERE -------------------------------------------------------------------------------------')
        print(cleaned_vid)
        print('LOOK HERE ---------------------------------------------------------------------------------------')

        #  code
        all_strings = [item for sublist in strings for item in sublist]
        regexes = [[regex.search(string_)[0] if regex.search(
            string_) else None for regex in compiled_regexes.values()] for string_ in all_strings]
        return{
            'Header': pytesseract.image_to_string(header),
            'Strings': strings,
            "Regexes": regexes
        }


'''This is a dumb, lazy approach'''
num_files = sorted([int(re.search('[0-9]+', filename)[0])
                    for filename in glob.glob('./*.png')])
usable_files = [f'page_{num}.png' for num in num_files[:-1] if num != 2]
for file in tqdm(usable_files):
    with open(file+'.json', 'w') as f:
        json.dump(handle_sheet(file), f)
