# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
import numpy as np
import glob
try:
    from astropy.tests.compat import assert_allclose
except ImportError:
    from numpy.testing.utils import assert_allclose
from astropy.tests.helper import raises
from os.path import basename, dirname, join
from ..file_lines import file_lines
from ..median import median
from ..pcomp import pcomp
from ..smooth import smooth
from ..uniq import uniq


class TestPydl(object):
    """Test the top-level pydl functions.
    """

    def setup(self):
        self.data_dir = join(dirname(__file__), 't')

    def teardown(self):
        pass

    def test_file_lines(self):
        #
        # Find the test files
        #
        fileglob = join(self.data_dir, 'this-file-contains-*-lines.txt')
        plainfiles = glob.glob(fileglob)
        gzfiles = glob.glob(fileglob+'.gz')
        for p in plainfiles:
            n = file_lines(p)
            number_of_lines = int(basename(p).split('-')[3])
            assert n == number_of_lines
        for p in gzfiles:
            n = file_lines(p, compress=True)
            number_of_lines = int(basename(p).split('-')[3])
            assert n == number_of_lines
        #
        # Test list passing
        #
        n = file_lines(plainfiles)
        number_of_lines = [int(basename(p).split('-')[3]) for p in plainfiles]
        assert n == number_of_lines
        n = file_lines(gzfiles, compress=True)
        number_of_lines = [int(basename(p).split('-')[3]) for p in gzfiles]
        assert n == number_of_lines
        #
        # Make sure empty files work
        #
        n = file_lines(join(self.data_dir, 'this-file-is-empty.txt'))
        assert n == 0

    def test_median(self):
        odd_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                            dtype=np.float32)
        even_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                             dtype=np.float32)
        assert median(odd_data) == 7
        assert median(odd_data, even=True) == 7
        assert median(even_data) == 7
        assert median(even_data, even=True) == 6.5
        assert (median(odd_data, 3) == odd_data).all()
        with raises(ValueError):
            foo = median(np.ones((9, 9, 9)), 3)
        odd_data2 = np.vstack((odd_data, odd_data, odd_data, odd_data, odd_data))
        assert (median(odd_data2, 3) == odd_data2).all()
        assert (median(odd_data2, axis=0) == odd_data).all()
        assert (median(odd_data2, axis=1) ==
                7*np.ones((odd_data2.shape[0],), dtype=odd_data2.dtype)).all()

    def test_pcomp(self):
        test_data_file = join(self.data_dir, 'pcomp_data.txt')
        test_data = np.loadtxt(test_data_file, dtype='d', delimiter=',')
        pcomp_data = test_data[0:20, :]
        m = 4
        n = 20
        means = np.tile(pcomp_data.mean(0), 20).reshape(pcomp_data.shape)
        newarray = pcomp_data - means
        foo = pcomp(newarray, covariance=True)
        #
        # This array is obtained from the IDL version of PCOMP.
        # It is only accurate up to an overall sign on each column.
        #
        derived = test_data[20:40, :]
        for k in range(m):
            assert_allclose(abs(foo.derived[:, k]), abs(derived[:, k]), 1e-4)
        coefficients = test_data[40:44, :]
        coefficientsT = coefficients.T
        for k in range(m):
            assert_allclose(abs(foo.coefficients[:, k]),
                            abs(coefficientsT[:, k]),
                            1e-4)
        eigenvalues = test_data[44, :]
        assert_allclose(foo.eigenvalues, eigenvalues, 1e-4)
        variance = test_data[45, :]
        assert_allclose(foo.variance, variance, 1e-4)

    def test_smooth(self):
        test_data_file = join(self.data_dir, 'smooth_data.txt')
        noise = np.loadtxt(test_data_file, dtype='d')
        #
        # Test smooth function
        #
        x = 8.0*np.arange(100)/100.0 - 4.0
        y = np.sin(x) + 0.1*noise
        s = smooth(y, 5)
        assert s.shape == (100,)
        s_edge = smooth(y, 5, True)
        assert s_edge.shape == (100,)
        s_w = smooth(y, 1)
        assert (s_w == y).all()

    def test_uniq(self):
        items = np.array([1, 2, 3, 1, 5, 6, 1, 7, 3, 2, 5, 9, 11, 1])
        items_sorted = np.sort(items)
        items_argsorted = np.argsort(items)
        #
        # Test pre-sorted array.
        #
        u1 = uniq(items_sorted)
        assert (u1 == np.array([3, 5, 7, 9, 10, 11, 12, 13])).all()
        #
        # Test arg-sorted array.
        #
        u2 = uniq(items, items_argsorted)
        assert (u2 == np.array([13, 9, 8, 10, 5, 7, 11, 12])).all()
        assert (items_sorted[u1] == items[u2]).all()
        #
        # Test degenerate case of all identical items.
        #
        identical_items = np.ones((10,), dtype=items.dtype)
        u = uniq(identical_items)
        assert (u == np.array([9])).all()
        u = uniq(identical_items, np.arange(10, dtype=items.dtype))
        assert (u == np.array([9])).all()
