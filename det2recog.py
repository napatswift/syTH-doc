import json
import numpy as np
import cv2
import os
from tqdm import tqdm
import imgaug.augmenters as iaa
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage
from random import randint, shuffle

IMG_ID  = 0
AUG_SEQ = iaa.Sequential([
    iaa.Dropout(p=(.0, .0015)),
    iaa.GammaContrast((1, 8)),
    iaa.AddToBrightness((10,40)),
    iaa.BlendAlphaSimplexNoise(iaa.GammaContrast(10)),
    iaa.Pad((0, 10), pad_mode=['linear_ramp', 'constant']),
    iaa.Rotate((-5, 5),),
    iaa.MultiplyHueAndSaturation((0.5, 1.5), per_channel=True),
])

def get_bbox_and_text(rect_text_list):
    text_list = []
    bbox_list = []
    for rect_text in rect_text_list:
        if 'text' not in rect_text.keys(): continue
        if not check_size(rect_text['bbox']): continue
        text_list.append(rect_text['text'])
        bbox_list.append(rect_text['bbox'])
    return bbox_list, text_list

def check_size(bbox):
    x0, y0, x1, y1 = bbox
    return (x1-x0) * (y1-y0) > 100

def save_image(filename: str, bbox: BoundingBox, img: np.array):
    assert isinstance(bbox, BoundingBox)
    assert isinstance(img, np.ndarray)
    r = 250/bbox.width
    w = bbox.width * r
    h = bbox.height * r
    print(r)
    text_img = img[bbox.y1_int:bbox.y2_int, bbox.x1_int:bbox.x2_int, :]
    return cv2.imwrite(filename,
                       cv2.resize(text_img, (int(w), int(h))))

def get_bboxes_aug(bboxes, texts, shape):
    if randint(0, 100) < 50:
      bboxes = [(x0-randint(1, 8),
                 y0-randint(1, 8),
                 x1+randint(1, 8),
                 y1+randint(1, 8)) for x0, y0, x1, y1 in bboxes]
    return BoundingBoxesOnImage([BoundingBox(*b, t) for b, t in zip(bboxes, texts)], shape=shape)

def cvt(dir_name, data_list, matadata_fpath):
    global IMG_ID

    def _helper_save_image(image, bboxes):
      global IMG_ID
      aug_image, aug_bboxes = AUG_SEQ(image=image, bounding_boxes=bboxes)
      aug_bboxes: BoundingBoxesOnImage = aug_bboxes.remove_out_of_image(True, True)
      for bbox in aug_bboxes.bounding_boxes:
        try:
          img_name = f'{IMG_ID}.jpeg'
          save_image(os.path.join(img_dir, img_name), bbox, aug_image)
          fp_metadata.write(f'{img_name},{bbox.label}\n',)
          IMG_ID += 1
        except:
           pass
        assert IMG_ID < 100

    fp_metadata = open(matadata_fpath, 'a')
    img_dir = os.path.join(f'{dir_name}_recog', 'imgs',)
    for data in tqdm(data_list):
      bbox_list, text_list = get_bbox_and_text(data['instances'])
      image = cv2.imread(os.path.join(dir_name, 'imgs', data['img_path']))
      bboxes_augimg = get_bboxes_aug(bbox_list, text_list, image.shape)
      for _ in range(2):
        _helper_save_image(image, bboxes_augimg)
    fp_metadata.close()

if __name__ == '__main__':
    dir_name = 'output/thvl'
    data = json.load(open(os.path.join(dir_name, 'textdet_train.json')))
    img_dir = os.path.join(f'{dir_name}_recog', 'imgs',)
    matadata_fpath = os.path.join(img_dir, 'metadata.csv')
    os.makedirs(img_dir, exist_ok=True)
    with open(matadata_fpath, 'w') as fp:
        fp.write('file_name,text\n')
    shuffle(data['data_list'])
    cvt(dir_name, data['data_list'][:10], matadata_fpath)

            



        
