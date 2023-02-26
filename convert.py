import json

def cvt(fpath):
  with open(fpath, 'r') as fp:
      data = json.load(fp)
  for img in data['data_list']:
    img['img_path'] = img['image_path']
    del img['text']

  with open(fpath, 'w') as fp:
     json.dump(data, fp, ensure_ascii=False)

cvt('thvl/textdet_test.json')
cvt('thvl/textdet_train.json')