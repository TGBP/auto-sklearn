import abc
from typing import Any, Dict, List, Tuple

import numpy as np

import scipy.sparse

from autosklearn.pipeline.components.data_preprocessing.data_preprocessing \
    import DataPreprocessor
from autosklearn.util.data import predict_RAM_usage


def perform_one_hot_encoding(
    sparse: bool,
    categorical: List[bool],
    data: List
) -> Tuple[List, bool]:
    predicted_RAM_usage = float(
        predict_RAM_usage(data[0], categorical)) / 1024 / 1024

    if predicted_RAM_usage > 1000:
        sparse = True

    rvals = []
    if any(categorical):
        encoder = DataPreprocessor(
            categorical_features=categorical, force_sparse_output=sparse)
        rvals.append(encoder.fit_transform(data[0]))
        for d in data[1:]:
            rvals.append(encoder.transform(d))

        if not sparse and scipy.sparse.issparse(rvals[0]):
            for i in range(len(rvals)):
                rvals[i] = rvals[i].todense()
    else:
        rvals = data

    return rvals, sparse


class AbstractDataManager():
    __metaclass__ = abc.ABCMeta

    def __init__(self, name: str):

        self._data = dict()  # type: Dict
        self._info = dict()  # type: Dict
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def data(self) -> Dict[str, np.ndarray]:
        return self._data

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    @property
    def feat_type(self) -> List[str]:
        return self._feat_type

    @feat_type.setter
    def feat_type(self, value: List[str]) -> None:
        self._feat_type = value

    @property
    def encoder(self) -> DataPreprocessor:
        return self._encoder

    @encoder.setter
    def encoder(self, value: DataPreprocessor) -> DataPreprocessor:
        self._encoder = value

    def perform1HotEncoding(self) -> None:
        sparse = True if self.info['is_sparse'] == 1 else False
        has_missing = True if self.info['has_missing'] else False
        to_encode = ['categorical']
        if has_missing:
            to_encode += ['binary']
        encoding_mask = [feat_type.lower() in to_encode
                         for feat_type in self.feat_type]

        data = [self.data['X_train']]
        if 'X_valid' in self.data:
            data.append(self.data['X_valid'])
        if 'X_test' in self.data:
            data.append(self.data['X_test'])
        data, sparse = perform_one_hot_encoding(
            sparse=sparse, categorical=encoding_mask,
            data=data)

        self.info['is_sparse'] = 1 if sparse else 0
        self.data['X_train'] = data[0]
        if 'X_valid' in self.data and 'X_test' in self.data:
            self.data['X_valid'] = data[1]
            self.data['X_test'] = data[2]
        elif 'X_valid' in self.data:
            self.data['X_valid'] = data[1]
        elif 'X_test' in self.data:
            self.data['X_test'] = data[1]

    def __repr__(self) -> str:
        return 'DataManager : ' + self.name

    def __str__(self) -> str:
        val = 'DataManager : ' + self.name + '\ninfo:\n'
        for item in self.info:
            val = val + '\t' + item + ' = ' + str(self.info[item]) + '\n'
        val = val + 'data:\n'

        for subset in self.data:
            val = val + '\t%s = %s %s %s\n' % (subset, type(self.data[subset]),
                                               str(self.data[subset].shape),
                                               str(self.data[subset].dtype))
            if isinstance(self.data[subset], scipy.sparse.spmatrix):
                val = val + '\tdensity: %f\n' % \
                            (float(len(self.data[subset].data)) /
                             self.data[subset].shape[0] /
                             self.data[subset].shape[1])
        val = val + 'feat_type:\t' + str(self.feat_type) + '\n'
        return val
