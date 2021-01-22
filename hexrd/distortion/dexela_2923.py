# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 15:07:34 2021

@author: Joel V. Bernier
"""
import numpy as np

from hexrd import constants
from hexrd.constants import USE_NUMBA
if USE_NUMBA:
    import numba

from .distortionabc import DistortionABC
from .registry import _RegisterDistortionClass


class Dexela_2923(DistortionABC, metaclass=_RegisterDistortionClass):

    maptype = "Dexela_2923"

    def __init__(self, params, **kwargs):
        self._params = np.asarray(params, dtype=float).flatten()

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, x):
        assert len(x) == 8, "parameter list must have len of 8"
        self._params = np.asarray(x, dtype=float).flatten()

    @property
    def is_trivial(self):
        return np.all(self.params == 0)

    def apply(self, xy_in):
        if self.is_trivial:
            return xy_in
        else:
            xy_out = np.empty_like(xy_in)
            _dexela_2923_distortion(
                xy_out, xy_in, np.asarray(self.params)
            )
            return xy_out

    def apply_inverse(self, xy_in):
        if self.is_trivial:
            return xy_in
        else:
            xy_out = np.empty_like(xy_in)
            _dexela_2923_inverse_distortion(
                xy_out, xy_in, np.asarray(self.params)
            )
            return xy_out


def _dexela_2923_distortion(out, in_, params):
    # find quadrant
    ql = _find_quadrant(in_)
    ql1 = ql == 1
    ql2 = ql == 2
    ql3 = ql == 3
    ql4 = ql == 4
    out[ql1, :] = in_[ql1] + np.tile(params[0:2], (sum(ql1), 1))
    out[ql2, :] = in_[ql2] + np.tile(params[2:4], (sum(ql2), 1))
    out[ql3, :] = in_[ql3] + np.tile(params[4:6], (sum(ql3), 1))
    out[ql4, :] = in_[ql4] + np.tile(params[6:8], (sum(ql4), 1))
    return


def _dexela_2923_inverse_distortion(out, in_, params):
    ql = _find_quadrant(in_)
    ql1 = ql == 1
    ql2 = ql == 2
    ql3 = ql == 3
    ql4 = ql == 4
    out[ql1, :] = in_[ql1] - np.tile(params[0:2], (sum(ql1), 1))
    out[ql2, :] = in_[ql2] - np.tile(params[2:4], (sum(ql2), 1))
    out[ql3, :] = in_[ql3] - np.tile(params[4:6], (sum(ql3), 1))
    out[ql4, :] = in_[ql4] - np.tile(params[6:8], (sum(ql4), 1))
    return


def _find_quadrant(xy_in):
    quad_label = np.zeros(len(xy_in), dtype=int)
    in_2_or_3 = xy_in[:, 0] < 0.
    in_1_or_4 = ~in_2_or_3
    in_3_or_4 = xy_in[:, 1] < 0.
    in_1_or_2 = ~in_3_or_4
    quad_label[np.logical_and(in_1_or_4, in_1_or_2)] = 1
    quad_label[np.logical_and(in_2_or_3, in_1_or_2)] = 2
    quad_label[np.logical_and(in_2_or_3, in_3_or_4)] = 3
    quad_label[np.logical_and(in_1_or_4, in_3_or_4)] = 4
    return quad_label


def test_disortion():
    pts = np.random.randn(16, 2)
    qi = _find_quadrant(pts)

    # test trivial
    params = np.zeros(8)
    dc = Dexela_2923(params)
    if not np.all(dc.apply(pts) - pts == 0.):
        raise RuntimeError("distortion apply failed!")
    if not np.all(dc.apply_inverse(pts) - pts == 0.):
        raise RuntimeError("distortion apply_inverse failed!")

    # test non-trivial
    params = np.random.randn(8)
    dc = Dexela_2923(params)
    ptile = np.vstack([params.reshape(4, 2)[j - 1, :] for j in qi])
    result = dc.apply(pts) - pts
    result_inv = dc.apply_inverse(pts) - pts
    if not np.all(abs(result - ptile) <= constants.epsf):
        raise RuntimeError("distortion apply failed!")
    if not np.all(abs(result_inv + ptile) <= constants.epsf):
        raise RuntimeError("distortion apply_inverse failed!")
    return True
