from PIL import Image, ImageFont, ImageDraw
import mistune
import re
import os
import argparse
import json
import augraphy as ag
import numpy as np
import cv2
import attacut
from text import *
from paper import *
from font import get_font
from tqdm import trange

import warnings

warnings.filterwarnings('ignore', category=np.RankWarning)


def get_augmenter():
    return ag.AugmentationSequence([
        ag.LowInkRandomLines(count_range=(10, 15), noise_probability=0.5),
        ag.PencilScribbles(size_range=(10, 50),
                           stroke_count_range=(1, 3),
                           count_range=(1, 3),
                           thickness_range=(1, 2),
                           p=.5),
        ag.Gamma(gamma_range=(.1, .3)),
        ag.BleedThrough(),
        ag.LowInkPeriodicLines(),
        ag.LightingGradient(p=0.8),
    ])


def put_text(canvas: ImageDraw, x: float, y: float, text: str, font: ImageFont):
    """
    Write text on a PIL ImageDraw object at the specified coordinates and return the bounding box of each word.

    Args:
        canvas (ImageDraw): The ImageDraw object to write the text on.
        x (float): The x-coordinate to start writing the text.
        y (float): The y-coordinate to start writing the text.
        text (str): The text to write.
        font (ImageFont): The font to use for writing the text.

    Returns:
        list: A list of dictionaries, where each dictionary contains the bounding box and polygon of a word, as well as the text of the word.

    Raises:
        TypeError: If the `canvas` argument is not an instance of `PIL.ImageDraw.ImageDraw`, or if the `font` argument is not an instance of `PIL.ImageFont.ImageFont`.
    """

    words = text.split()
    curr_x = x
    word_bbox = []
    for i in range(len(words)):
        word = words[i]
        canvas.text((curr_x, y), word, fill='black', font=font)

        x0, y0, x1, y1 = canvas.textbbox((curr_x, y), word, font=font)
        word_bbox.append(dict(polygon=[x0, y0, x1, y0, x1, y1, x0, y1],
                              bbox=[x0, y0, x1, y1],
                              text=word))
        curr_x = x1
        if i+1 < len(words):
            curr_x += font.getlength(' ')

    return word_bbox


def split_text_into_lines(word_list, font, max_x):
    """
    Splits a list of words into lines based on a maximum width constraint

    Args:
        word_list (List[str]): The list of words to split into lines
        font (ImageFont): The font used to measure the width of each word
        max_x (float): The maximum line width

    Returns:
        List[str]: A list of strings, where each string represents a 
                   line of text that fits within the maximum width
    """

    lines = []  # list to hold the lines of text
    line = ''   # variable to hold the current line being built

    # loop over each word in the list of words
    for word in word_list:
        # if adding the word to the current line would keep it within the maximum width,
        # add the word to the line
        if font.getlength(line + word) < max_x:
            line += word
        # otherwise, add the current line to the list of lines and start a new line with the word
        else:
            lines.append(line)
            line = word

    # add the final line to the list of lines (if it exists)
    if line:
        lines.append(line)

    return lines


def render_config(component):
    assert isinstance(component, dict)
    assert component['type'] == 'doc_config'

    config = dict()
    for k, v in component['children'].items():
        config[k] = parse_string(v)

    return config


def generate(parsed_components):
    paper = create_paper()
    canvas = ImageDraw.Draw(paper)
    font = get_font()
    position_start = {'x': 120, 'y': 150, }
    paper_config = {'max_x': paper.size[0] - 120, 'lineHeight': font.size + 6}
    curr = position_start.copy()

    def maybe_new_font(font):
        if random.random() < 0.5:
            return get_font()
        return font

    text_bbox = []
    for (i, component) in enumerate(parsed_components):
        if component['type'] == 'paragraph':
            for c_comp in component['children']:
                if c_comp['type'] == 'doc_config':
                    paper_config.update(render_config(c_comp))
                    if i == 0:
                        paper = create_paper(width=paper_config.get('paperWidth'),
                                             height=paper_config.get(
                                                 'paperHeight'),
                                             color=paper_config.get('paperColor'))
                        canvas = ImageDraw.Draw(paper)
                        position_start = {'x': paper_config.get(
                            'marginX', 0), 'y': paper_config.get('marginY', 0)}
                        paper_config['max_x'] = paper.size[0] - \
                            position_start['x']
                        curr = position_start.copy()
                    continue    
            
                font = maybe_new_font(font)
                text = c_comp['text']
                if curr['x'] + font.getlength(text) > paper_config['max_x']:
                    word_list = attacut.tokenize(text)
                    line_list = split_text_into_lines(
                        word_list, font, paper_config['max_x'] - curr['x'])
                else:
                    line_list = [text]

                for line in line_list:
                    args = {**curr, 'text': line,
                            'font': font, 'canvas': canvas}
                    text_bbox.extend(put_text(**args))
                    curr['y'] += paper_config['lineHeight']

        elif component['type'] == 'table':
            # get number of column
            col_ratio = []
            # get config
            for c_comp in component['children']:
                if c_comp['type'] == 'table_head':
                    for cell in c_comp['children']:
                        col_ratio.append(float(cell['children'][0]['text']))
                    assert 1 == sum(col_ratio), 'the ratio should add up to 1'
            ####################

            table_start = paper_config.get('marginX', position_start['x'])
            table_size = paper.size[0] - table_start * 2

            column_widths = [cr*table_size for cr in col_ratio]

            for c_comp in component['children']:
                for row in c_comp['children']:
                    # skip header
                    if c_comp['type'] == 'table_head':
                        continue

                    for i, cell in enumerate(row['children']):
                        font = maybe_new_font(font)

                        if len(cell['children']) == 0:
                            continue

                        # position
                        cell_x_start = sum(column_widths[:i])
                        if i != 0:
                            cell_x_start += 5
                        cell_width = column_widths[i]
                        x = table_start+cell_x_start
                        ####################

                        text = cell['children'][0]['text']

                        # alignment of text
                        if cell['align'] == 'right':
                            text_w = font.getlength(text)
                            x = x + cell_width - text_w
                        elif cell['align'] == 'center':
                            text_w = font.getlength(text)
                            x = x + cell_width/2 - text_w/2
                        else:
                            x = x + 5

                        # center_y
                        t_x0, t_y0, t_x1, t_y1 = font.getbbox(text)
                        center_y = curr['y'] + \
                            paper_config['lineHeight']/2 - t_y1/2
                        ####################

                        args = {
                            'x': x,
                            'y': center_y,
                            'text': text,
                            'font': font,
                            'canvas': canvas
                        }

                        text_bbox.extend(put_text(**args))

                    y0 = curr['y']
                    for i in range(len(row['children'])):
                        x0 = table_start + sum(column_widths[:i])
                        x1 = x0 + column_widths[i]
                        if paper_config.get('tableOutline', False):
                            canvas.rectangle((x0, y0, x1, y0 + paper_config['lineHeight']),
                                             None,
                                             'black',
                                             paper_config.get('tableOutlineWidth', 1))
                    curr['y'] += paper_config['lineHeight']

        elif component['type'] == 'block_html':
            tags = re.findall(r'<([^>/]+)/?>', component['text'])
            for tag in tags:
                # if the tag is <br> or <br/> then add line
                if tag == 'br':
                    curr['y'] += paper_config['lineHeight']
        else:
            print(component)
    for tbox in text_bbox:
        tbox['bbox_label'] = 0
        tbox['ignore'] = False
    return paper, text_bbox


def plugin_doc_config(md):
    def parse(block, m, state):
        configs = m.group(1)
        configs = dict(re.findall('([^=]+)=([^,]+),?', configs))
        return 'doc_config', configs

    def after_parse(md, tokens, state):
        return tokens

    CONFIG = r'\\c:([^ \n]+)'

    md.inline.register_rule('doc_config', CONFIG, parse)
    # md.before_render_hooks.append(after_parse)
    md.inline.rules.append('doc_config')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample_number', default=10, type=int)
    parser.add_argument('--copy', default=1, type=int)
    parser.add_argument('--output_dir', default='output/thvl')
    parser.add_argument('--split_train_test', action='store_true')
    parser.add_argument('--train_size', type=float, default=0.8)

    args = parser.parse_args()

    img_dir = 'imgs'

    os.makedirs(os.path.join(args.output_dir, img_dir), exist_ok=True)

    markdown_parser = mistune.create_markdown(
        plugins=['table', plugin_doc_config], renderer='ast')
    doc_template_gen = DocTemplate()

    img_counter = 0

    image_bbox_list = []
    try:
        for i in trange(args.sample_number):
            img, bboxes = generate(markdown_parser(
                get_doc_md(doc_template_gen.gen())))

            metadata = dict(
                instances=bboxes,
                width=img.size[0],
                height=img.size[1]
            )

            for j in range(args.copy):
                img_name = f'img_{img_counter}.jpg'
                img_path = os.path.join(img_dir, img_name)
                aug_img = get_augmenter()(np.array(img))[0]

                cv2.imwrite(os.path.join(args.output_dir, img_path), aug_img)

                m = metadata.copy()
                m['img_path'] = img_name
                image_bbox_list.append(m)
                img_counter += 1
    except KeyboardInterrupt:
        pass

    train_size = int(len(image_bbox_list) * args.train_size)
    metainfo = dict(dataset_type='TextDetDataset',
                    task_name='textdet', category=dict(id=0, name='text'))

    if args.split_train_test:
        with open(os.path.join(args.output_dir, 'textdet_train.json',), 'w') as fp:
            json.dump(dict(metainfo=metainfo, data_list=image_bbox_list[:train_size]),
                      fp, ensure_ascii=False,)

        with open(os.path.join(args.output_dir, 'textdet_test.json',), 'w') as fp:
            json.dump(dict(metainfo=metainfo, data_list=image_bbox_list[train_size:]),
                      fp, ensure_ascii=False,)
    else:
        with open(os.path.join(args.output_dir, 'textdet_train.json',), 'w') as fp:
            json.dump(dict(metainfo=metainfo, data_list=image_bbox_list),
                      fp, ensure_ascii=False,)
