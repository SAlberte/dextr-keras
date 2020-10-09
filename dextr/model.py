#!/usr/bin/env python
from os.path import splitext, join
import numpy as np
from scipy import misc
from tensorflow import keras
from keras import backend as K

import tensorflow as tf
from .resnet import build_network
from .helpers import *


class DEXTR(object):
    """Pyramid Scene Parsing Network by Hengshuang Zhao et al 2017"""

    def __init__(self, nb_classes, resnet_layers, input_shape, num_input_channels=4,
                 classifier='psp', weights_path='models/dextr_pascal-sbd.h5', sigmoid=False):
        self.input_shape = input_shape
        self.num_input_channels = num_input_channels
        self.sigmoid = sigmoid
        self.model = build_network(nb_classes=nb_classes, resnet_layers=resnet_layers, num_input_channels=num_input_channels,
                                   input_shape=self.input_shape, classifier=classifier, sigmoid=self.sigmoid, output_size=self.input_shape)

        self.model.load_weights(weights_path)

    def feed_forward(self, data):

        assert data.shape == (self.input_shape[0], self.input_shape[1], self.num_input_channels)
        prediction = self.model.predict(np.expand_dims(data, 0))[0]

        return prediction
    
    def predict_mask(self, image, points, pad=50, threshold=0.8, zero_pad=True):
        points = np.array(points).astype(np.int)
        image = np.array(image)
        bbox = get_bbox(image, points=points, pad=pad, zero_pad=zero_pad)
        crop_image = crop_from_bbox(image, bbox, zero_pad=zero_pad)
        resize_image = fixed_resize(crop_image, (512, 512)).astype(np.float32)

        # Generate extreme point heat map normalized to image values
        extreme_points = points - [np.min(points[:, 0]), np.min(points[:, 1])] + [pad , pad]
        extreme_points = (512 * extreme_points * [1 / crop_image.shape[1], 1 / crop_image.shape[0]]).astype(np.int)
        extreme_heatmap = make_gt(resize_image, extreme_points, sigma=10)
        extreme_heatmap = cstm_normalize(extreme_heatmap, 255)
        
        # Concatenate inputs and convert to tensor
        input_dextr = np.concatenate((resize_image, extreme_heatmap[:, :, np.newaxis]), axis=2)

        pred = self.model.predict(input_dextr[np.newaxis, ...])[0, :, :, 0]
        result = crop2fullmask(pred, bbox, im_size=image.shape[:2], zero_pad=zero_pad, relax=pad) > threshold

        return result

    def predict(self, img):
        # Preprocess
        img = misc.imresize(img, self.input_shape)
        img = img.astype('float32')
        probs = self.feed_forward(img)
        return probs
