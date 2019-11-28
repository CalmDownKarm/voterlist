
import re
import os
import glob
import json
import pytesseract
from PIL import Image
from tqdm import tqdm

row_height = 590
rows_start = 330
left_margin_rows = 220
right_margin_rows = 245
box_width = 1500



def get_string_from_row(row):
    '''Takes in a single row (Image Object), gets 3 text strings out'''
    return [pytesseract.image_to_string(row.crop((i * box_width, 0 ,(i + 1) * box_width, row_height))) for i in range(3)]



regexes = {
    'Name': "(?<=Name)(.*)",
    'Relative': "(Father|Mother|Husband)\\\'s.*?Name.*?:(.*)",
    'Age': "Age:\s([0-9]+)",
    'Sex': "Sex:\s(MALE|FEMALE)"
}
compiled_regexes = {k:re.compile(v) for k,v in regexes.items()}
def handle_sheet(filename):
    '''Takes a filename and returns a list of strings inside it'''
    image = Image.open(filename)
    width, height = image.size
    header_box = (0,0,width, 320)
    footer_box = (0, 6220, width, height)
    rows = [image.crop((left_margin_rows, rows_start+ (i-1)*row_height, width-right_margin_rows, rows_start+ i*row_height)) for i in range(1, 11)]
    strings = [get_string_from_row(row) for row in rows]
    all_strings = [item for sublist in strings for item in sublist]
    regexes = [[regex.search(string_)[0] if regex.search(string_) else None for regex in compiled_regexes.values()] for string_ in all_strings]
    return{
        'Header': pytesseract.image_to_string(image.crop(header_box)),
        'Footer': pytesseract.image_to_string(image.crop(footer_box)),
#         'Rows': rows,
        'Strings': strings,
        "Regexes": regexes
    }


'''This is a dumb, lazy approach'''
num_files = sorted([int(re.search('[0-9]+', filename)[0]) for filename in glob.glob('./*.png')])
usable_files = [f'page_{num}.png' for num in num_files[2:-1]]
for file in tqdm(usable_files):
    with open(file+'.json', 'w') as f:
        json.dump(handle_sheet(file), f)





