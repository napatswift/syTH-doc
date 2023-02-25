from PIL import Image, ImageFont, ImageDraw
import mistune
import re
import random
import pandas as pd
from faker import Faker
import os
import argparse
import json
import augraphy as ag
import numpy as np
import cv2

aug_pipeline = ag.AugmentationSequence([
    ag.LowInkRandomLines(),
    ag.PencilScribbles(size_range=(10, 50), stroke_count_range=(1, 3), count_range=(1, 3), thickness_range=(1, 2), p=.5),
    ag.Gamma(gamma_range=(.1,.3)),
    ag.LowInkPeriodicLines(),
])

def arabic2th(n):
    return chr(ord(n)+(ord('๑')-ord('1')))

class DocTemplate:
    def __init__(self,):
        template_fpath = [os.path.join('templates', fname)
                          for fname in os.listdir('templates/')
                          if fname.endswith('.md')]
        self.templates = [open(fp).read() for fp in template_fpath]
        self.next = 0

    def gen(self):
        template = self.templates[self.next]
        self.next = (self.next + 1) % len(self.templates)
        return template

politician = pd.read_csv('data/TWFU-PoliticianData.csv', skiprows=1)
doc_template_gen = DocTemplate()
faker=Faker('th')

def get_token_text(token: str):
    assert token[0] == '{' and token[-1] == '}'
    token = token[1:-1]
    if token == 'number':
        if random.random() > 0.5:
            return str(random.randint(0, 50))
        return str(random.randint(0, 1000))
    if token == 'number_th':
        num = str(random.randint(0, 50))
        return ''.join([arabic2th(n) for n in num])
    if token == 'pm_id':
        return '%03d' % random.randint(0, 1000)
    if token == 'pm_name_lastname':
        if random.random() > 0.5:
            sample = politician.sample(3)
            title = sample.iloc[0]['title']
            name = sample.iloc[1]['name']
            lastname = sample.iloc[2]['lastname']
        else:
            title = random.choice(['นาย', 'นาง', 'นางสาว', 'พลตำรวจ'])
            name = faker.first_name()
            lastname = faker.last_name()
        return f'{title}{name} {lastname}'
    if token == 'party':
        text = politician[~politician.party.isna()].party.sample().iloc[0]
        return text
    if token == 'vote':
        return random.choice(['เห็นด้วย', 'ไม่เห็นด้วย', 'เห็นไม่ด้วย', '-'])
    if token == 'phonenumber_th':
        return ''.join([arabic2th(n) if n.isdigit() else n for n in faker.phone_number()])
    if token == 'month':
        return faker.month_name()
    return 'dummy'
    
def get_doc_md(template):
    """return markdown text"""
    tokens = re.findall('\{[^\}]*\}', template)
    for token in tokens:
        template=template.replace(token, get_token_text(token), 1)
    return template

def get_font():
    fpaths = random.choice(['fonts/THSarabun.ttf', 'fonts/THSarabun Bold.ttf'])
    return ImageFont.truetype(fpaths, size=random.randrange(26, 28))

def create_paper(
    width=1156,
    height=1636,
    color='#fff'
):
    return Image.new('RGB', (width, height,), color)


def put_text(canvas, x, y, text, font):
    words = text.split()
    curr_x = x
    word_bbox = []
    for i in range(len(words)):
        word = words[i]
        canvas.text((curr_x, y), word, fill='black', font=font)
        
        x0,y0,x1,y1 = canvas.textbbox((curr_x, y), word, font=font)
        word_bbox.append(dict(polygon=[x0, y0, x1, y0, x1, y1, x0, y1],
                              bbox=[x0,y0,x1,y1],
                              text=word))
        curr_x = x1
        if i+1 < len(words):
            curr_x += font.getlength(' ')

    return word_bbox


def generate():
    markdown_parser = mistune.create_markdown(plugins=['table'], renderer='ast')
    paper = create_paper()
    canvas = ImageDraw.Draw(paper)
    font = get_font()
    parsed_components = markdown_parser(get_doc_md(doc_template_gen.gen()))
    line_height = font.size + 6
    position_start={'x': 120, 'y': 150}
    curr=position_start.copy()
    
    text_bbox = []
    for component in parsed_components:
        if component['type'] == 'paragraph':
            for c_comp in component['children']:
                #canvas.text(list(curr.values()), c_comp['text'], fill='black', font=font)
                args = {**curr, 'text': c_comp['text'], 'font': font, 'canvas': canvas}
                text_bbox.extend(put_text(**args))
                curr['y'] += line_height

        elif component['type'] == 'table':
            # get number of column
            col_num = None
            col_ratio = []
            ## get config
            for c_comp in component['children']:
                if c_comp['type'] == 'table_head':
                    # count number of columns
                    col_num = len(c_comp['children'])
                    for cell in c_comp['children']:
                        col_ratio.append(float(cell['children'][0]['text']))
                    assert 1 == sum(col_ratio), 'the ratio should add up to 1'
            ####################

            table_start = position_start['x']
            table_size = paper.size[0] - table_start*2
            
            column_widths = [cr*table_size for cr in col_ratio]
            
            for c_comp in component['children']:
                for row in c_comp['children']:
                    # skip header
                    if c_comp['type'] == 'table_head':
                        continue
                    
                    for i, cell in enumerate(row['children']):
                        if len(cell['children']) == 0: continue
                            
                        ## position
                        cell_x_start = sum(column_widths[:i])
                        if i != 0: cell_x_start += 5
                        cell_width = column_widths[i]
                        x = table_start+cell_x_start
                        ####################
                        
                        text = cell['children'][0]['text']
                        
                        ## alignment of text
                        if cell['align'] == 'right':
                            text_w = font.getlength(text)
                            x = x + cell_width - text_w
                        elif cell['align'] == 'center':
                            text_w = font.getlength(text)
                            x = x + cell_width/2 - text_w/2
                        ####################
                        
                        args = {
                                'x': x,
                                'y': curr['y'],
                                'text': text,
                                'font': font,
                                'canvas': canvas
                               }
                        text_bbox.extend(put_text(**args))

                    curr['y'] += line_height

        elif component['type'] == 'block_html':
            tags = re.findall(r'<([^>/]+)/?>', component['text'])
            for tag in tags:
                # if the tag is <br> or <br/> then add line
                if tag == 'br':
                    curr['y'] += line_height
        else:
            print(component)

    return paper, text_bbox

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample_number', default=10, type=int)
    parser.add_argument('--copy', default=3, type=int)
    parser.add_argument('--output_dir', default='output')

    args = parser.parse_args()
    
    img_dir = 'imgs'

    os.makedirs(os.path.join(args.output_dir, img_dir), exist_ok=True)
    
    img_counter = 0

    image_bbox_list = []

    for i in range(args.sample_number):
        img, bboxes = generate()

        metadata = dict(
            instances=bboxes,
            width=img.size[0],
            height=img.size[1]
        )
        
        for j in range(args.copy):
            img_path = os.path.join(img_dir, f'img_{img_counter}.jpg')
            aug_img = aug_pipeline(np.array(img))[0]

            cv2.imwrite(os.path.join(args.output_dir, img_path), aug_img)

            m = metadata.copy()
            m['image_path'] = img_path
            image_bbox_list.append(m)
            img_counter += 1

    with open(os.path.join(args.output_dir, 'gt.json',), 'w') as fp:
        json.dump(image_bbox_list, fp, ensure_ascii=False,)