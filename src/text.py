import random
from faker import Faker
import re
import pandas as pd
import os

politician = pd.read_csv('data/TWFU-PoliticianData.csv', skiprows=1)

faker = Faker('th')

def arabic2th(n):
    """
    Convert an Arabic numeral to a Thai numeral.

    Args:
        n (str): An Arabic numeral as a string.

    Returns:
        str: The corresponding Thai numeral as a string.
    """
    return chr(ord(n)+(ord('๑')-ord('1')))


def get_token_text(token: str):
    """Get text from token"""
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
    if re.match(r'paragraph_\d+', token):
        n = re.findall(r'paragraph_(\d+)', token)[0]
        n = int(n)
        return faker.paragraph(n)
    if re.match(r'words_\d+', token):
        n = re.findall(r'words_(\d+)', token)[0]
        n = int(n)
        return ''.join(faker.words(n))
    return 'dummy'


def get_doc_md(template):
    """
    Return markdown text with tokens replaced by their corresponding values.

    Args:
        template (str): A string containing markdown text with tokens to be replaced.

    Returns:
        str: A string containing the updated markdown text with tokens replaced by their corresponding values.
    """
    
    # define a function to replace each token with its corresponding value
    def replace_token(match):
        token = match.group(0)
        return get_token_text(token)
    
    # replace all tokens in the template string with their corresponding values
    return re.sub('\{[^\}]*\}', replace_token, template)

def parse_string(value_str):
    """
    Parse a string and attempt to convert it to a boolean, integer, or float value.

    Args:
        value_str (str): The string to parse.

    Returns:
        bool, int, float, or str: The parsed value. If the string cannot be parsed as a boolean, integer, or float, the original string is returned.

    Examples:
        >>> parse_string('true')
        True
        >>> parse_string('123')
        123
        >>> parse_string('3.14')
        3.14
        >>> parse_string('hello')
        'hello'
    """
    if value_str.lower() == 'true':
        return True
    elif value_str.lower() == 'false':
        return False
    try:
        return int(value_str)
    except ValueError:
        pass
    try:
        return float(value_str)
    except ValueError:
        pass
    return value_str


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
