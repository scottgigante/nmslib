from builtins import super
from six import with_metaclass

import abc
import logging

import numpy as np
import scipy.sparse

from sklearn.exceptions import NotFittedError

import nmslib
from . import utils, spaces

_logger = logging.getLogger("nmslib")


class _Base(with_metaclass(abc.ABCMeta, object)):
    def __init__(self, n_neighbors, space="l2", n_jobs=1):
        n_jobs = utils.parse_n_jobs(n_jobs)
        _logger.debug(
            "Init {} index with arguments "
            "n_neighbors={}, space={}, n_jobs={}".format(
                self.method, n_neighbors, space, n_jobs
            )
        )
        self.n_neighbors = n_neighbors
        self.n_jobs = n_jobs
        self.space = space
        self._fitted = False

    @utils.abstractproperty
    def method(self):
        pass

    @abc.abstractmethod
    def init_params(self, X):
        pass

    @abc.abstractmethod
    def query_params(self, X):
        pass

    @property
    def space(self):
        return self._space

    @space.setter
    def space(self, space):
        spaces.valid_space(space)
        self._space = space

    def _check_data(self, X, data_type=None):
        # convert to numpy.ndarray or scipy.sparse.csr_matrix
        if data_type is nmslib.DataType.SPARSE_VECTOR:
            X = scipy.sparse.csr_matrix(X)
        elif data_type is nmslib.DataType.DENSE_VECTOR:
            X = np.asarray(X)
        else:
            # unspecified, infer from data
            if scipy.sparse.issparse(X) or self.space in spaces.SPARSE_SPACES:
                X = scipy.sparse.csr_matrix(X)
                data_type = nmslib.DataType.SPARSE_VECTOR
            else:
                X = np.asarray(X)
                data_type = nmslib.DataType.DENSE_VECTOR
        return X, data_type

    def _check_space(self, X, space, coerce=True):
        if scipy.sparse.issparse(X):
            space = spaces.sparse_space(space, coerce=coerce)
        else:
            space = spaces.dense_space(space, coerce=coerce)
        return space

    def fit(self, X):
        self.X, self.data_type = self._check_data(X)
        _logger.debug(
            "Building {} index with {} of shape {}".format(
                self.method, type(X), X.shape
            )
        )
        space = self._check_space(self.X, self.space)
        _logger.debug(
            "Arguments space={}, data_type={}, params={}".format(
                space, self.data_type, self.init_params
            )
        )
        self.index = nmslib.init(
            method=self.method, space=space, data_type=self.data_type
        )
        self.index.addDataPointBatch(X)
        self.index.createIndex(self.init_params)
        self._fitted = True
        return self

    def kneighbors(self, X=None, n_neighbors=None):
        if X is None:
            if self._fitted:
                X = self.X
            else:
                raise NotFittedError
        elif not self._fitted:
            self.fit(X)
        else:
            X, data_type = self._check_data(X, data_type=self.data_type)
            self._check_space(X, self.space, coerce=False)
        if n_neighbors is None:
            n_neighbors = self.n_neighbors
        _logger.debug(
            "Querying {} index with {} of shape {}".format(
                self.method, type(X), X.shape
            )
        )
        _logger.debug("Arguments {}".format(self.query_params))
        self.index.setQueryTimeParams(self.query_params)
        indices, distances = zip(
            *(self.index.knnQueryBatch(X, k=n_neighbors, num_threads=self.n_jobs))
        )
        try:
            distances, indices = np.vstack(distances), np.vstack(indices)
            _logger.debug("Complete")
        except ValueError:
            raise RuntimeError("Neighbors search did not converge.")
        return distances, indices

    def kneighbors_graph(
        self, X=None, n_neighbors=None, mode="connectivity", **query_params
    ):
        if mode != "connectivity":
            raise NotImplementedError
        if self._fitted:
            if X is not None and X is not self.X:
                self.fit(X)
        if n_neighbors is None:
            n_neighbors = self.n_neighbors
        _, indices = self.kneighbors(X=X, n_neighbors=n_neighbors, **query_params)
        return scipy.sparse.coo_matrix(
            (
                np.ones(self.X.shape[0] * n_neighbors),
                (np.repeat(np.arange(self.X.shape[0]), n_neighbors), indices.flatten()),
            ),
            shape=(self.X.shape[0], self.X.shape[0]),
        )

    def save(self, filename, save_data=True):
        self.index.saveIndex(filename, save_data=save_data)

    def load(self, filename, load_data=True):
        kwargs = {"space": self.space}
        try:
            kwargs["space"] = self._check_space(self.X, self.space)
            kwargs["data_type"] = self.data_type
        except AttributeError:
            pass
        self.index = nmslib.init(method=self.method, **kwargs)
        index.loadIndex(indexLocal, load_data=True)


class SimpleInvIndex(_Base):
    @property
    def method(self):
        return "simple_invindex"

    @property
    def init_params(self):
        return {}

    @property
    def query_params(self):
        return {}


class BruteForce(_Base):
    @property
    def method(self):
        return "brute_force"

    @property
    def init_params(self):
        return {}

    @property
    def query_params(self):
        return {}


class HNSW(_Base):
    def __init__(
        self,
        n_neighbors,
        M=None,
        efConstruction=None,
        post=0,
        maxM0=None,
        maxM=None,
        mult=None,
        delaunay_type=2,
        skip_optimized_index=None,
        space="l2",
        n_jobs=1,
    ):
        self._M = M
        self._efConstruction = efConstruction
        self._post = post
        self._maxM0 = maxM0
        self._maxM = maxM
        self._mult = mult
        self._delaunay_type = delaunay_type
        self._skip_optimized_index = skip_optimized_index
        return super().__init__(n_neighbors=n_neighbors, space=space, n_jobs=n_jobs)

    def kneighbors(self, X, n_neighbors=None, efSearch=None):
        self._efSearch = efSearch
        return super().kneighbors(X, n_neighbors=n_neighbors)

    @property
    def method(self):
        return "hnsw"

    @property
    def init_params(self):
        params = {"indexThreadQty": self.n_jobs}
        if self._M is not None:
            params["M"] = self._M
        if self._efConstruction is not None:
            params["efConstruction"] = self._efConstruction
        if self._post is not None:
            params["post"] = self._post
        if self._maxM0 is not None:
            params["maxM0"] = self._maxM0
        if self._maxM is not None:
            params["maxM"] = self._maxM
        if self._mult is not None:
            params["mult"] = self._mult
        if self._delaunay_type is not None:
            params["delaunay_type"] = self._delaunay_type
        if self._skip_optimized_index is not None:
            params["skip_optimized_index"] = self._skip_optimized_index
        return params

    @property
    def query_params(self):
        params = {}
        if self._efSearch is not None:
            params["efSearch"] = self._efSearch
        return params


class SWGraph(_Base):
    def __init__(self, n_neighbors, NN=None, efConstruction=None, space="l2", n_jobs=1):
        self._NN = NN
        self._efConstruction = efConstruction
        return super().__init__(n_neighbors=n_neighbors, space=space, n_jobs=n_jobs)

    def kneighbors(self, X, n_neighbors=None, efSearch=None):
        self._efSearch = efSearch
        return super().kneighbors(X, n_neighbors=n_neighbors)

    @property
    def method(self):
        return "sw-graph"

    @property
    def init_params(self):
        params = {"indexThreadQty": self.n_jobs}
        if self._NN is not None:
            params["NN"] = self._NN
        if self._efConstruction is not None:
            params["efConstruction"] = self._efConstruction
        return params

    @property
    def query_params(self):
        params = {}
        if self._efSearch is not None:
            params["efSearch"] = self._efSearch
        return params


class VPTree(_Base):
    def __init__(
        self, n_neighbors, chunkBucket=None, bucketSize=None, space="l2", n_jobs=1
    ):
        self._chunkBucket = chunkBucket
        self._bucketSize = bucketSize
        return super().__init__(n_neighbors=n_neighbors, space=space, n_jobs=n_jobs)

    def kneighbors(
        self,
        X,
        n_neighbors=None,
        alphaLeft=None,
        alphaRight=None,
        maxLeavesToVisit=None,
    ):
        self._alphaLeft = alphaLeft
        self._alphaRight = alphaRight
        self._maxLeavesToVisit = maxLeavesToVisit
        return super().kneighbors(X, n_neighbors=n_neighbors)

    @property
    def method(self):
        return "vptree"

    @property
    def init_params(self):
        params = {}
        if self._chunkBucket is not None:
            params["chunkBucket"] = self._chunkBucket
        if self._bucketSize is not None:
            params["bucketSize"] = self._bucketSize
        return params

    @property
    def query_params(self):
        params = {}
        if self._alphaLeft is not None:
            params["alphaLeft"] = self._alphaLeft
        if self._alphaRight is not None:
            params["alphaRight"] = self._alphaRight
        if self._maxLeavesToVisit is not None:
            params["maxLeavesToVisit"] = self._maxLeavesToVisit
        return params


class NAPP(_Base):
    def __init__(
        self,
        n_neighbors,
        numPivot=None,
        numPivotIndex=None,
        chunkIndexSize=None,
        space="l2",
        n_jobs=1,
    ):
        self._numPivot = numPivot
        self._numPivotIndex = numPivotIndex
        self._chunkIndexSize = chunkIndexSize
        return super().__init__(n_neighbors=n_neighbors, space=space, n_jobs=n_jobs)

    def kneighbors(self, X, n_neighbors=None, numPivotSearch=None):
        self._numPivotSearch = numPivotSearch
        return super().kneighbors(X, n_neighbors=n_neighbors)

    @property
    def method(self):
        return "napp"

    @property
    def init_params(self):
        params = {"indexThreadQty": self.n_jobs}
        if self._numPivot is not None:
            params["numPivot"] = self._numPivot
        if self._numPivotIndex is not None:
            params["numPivotIndex"] = self._numPivotIndex
        if self._chunkIndexSize is not None:
            params["chunkIndexSize"] = self._chunkIndexSize
        return params

    @property
    def query_params(self):
        params = {}
        if self._numPivotSearch is not None:
            params["numPivotSearch"] = self._numPivotSearch
        return params


class SeqSearch(_Base):
    def __init__(
        self, n_neighbors, multiThread=None, threadQty=None, space="l2", n_jobs=1
    ):
        self._numPivot = numPivot
        self._numPivotIndex = numPivotIndex
        self._chunkIndexSize = chunkIndexSize
        return super().__init__(n_neighbors=n_neighbors, space=space, n_jobs=n_jobs)

    def kneighbors(self, X, n_neighbors=None, numPivotSearch=None):
        self._numPivotSearch = numPivotSearch
        return super().kneighbors(X, n_neighbors=n_neighbors)

    @property
    def method(self):
        return "seq_search"

    @property
    def init_params(self):
        params = {"threadQty": self.n_jobs, "multiThread": self.n_jobs != 1}
        return params

    @property
    def query_params(self):
        params = {}
        return params
