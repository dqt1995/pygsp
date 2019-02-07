# -*- coding: utf-8 -*-

"""
Test suite for the learning module of the pygsp package.

"""

import unittest

import numpy as np

from pygsp import graphs, filters, learning


class TestCase(unittest.TestCase):

    def test_regression_tikhonov_1(self):
        """Solve a trivial regression problem."""
        G3 = graphs.Ring(N=8)
        signal = np.array([0, np.nan, 4, np.nan, 4, np.nan, np.nan, np.nan])
        mask = np.array([True, False, True, False, True, False, False, False])
        recovery0 = np.array([0, 2, 4, 4, 4, 3, 2, 1])
        recovery1 = learning.regression_tikhonov(G3, signal, mask, tau=0)
        np.testing.assert_allclose(recovery0, recovery1)

        # Test the numpy solution
        W = G3.W.toarray()
        G4 = graphs.Graph(W)
        recovery2 = learning.regression_tikhonov(G4, signal, mask, tau=0)
        np.testing.assert_allclose(recovery0, recovery2)

    def test_regression_tikhonov_2(self):
        """Solve a regression problem with a constraint."""
        # Create the graph
        G = graphs.Sensor(N=100)
        G.estimate_lmax()

        # Create a smooth signal
        def filt(x):
            return 1 / (1+10*x)
        filt = filters.Filter(G, filt)
        rs = np.random.RandomState(1)
        signal = filt.analyze(rs.randn(G.N, 5))

        # Make the input signal
        mask = rs.uniform(0, 1, [G.N]) > 0.5
        measurements = signal.copy()
        measurements[~mask] = np.nan

        # Solve the problem
        recovery0 = learning.regression_tikhonov(G, measurements, mask, tau=0)
        recovery1 = np.zeros(recovery0.shape)
        for i in range(recovery0.shape[1]):
            recovery1[:, i] = learning.regression_tikhonov(
                    G, measurements[:, i], mask, tau=0)

        G2 = graphs.Graph(G.W.toarray())
        G2.estimate_lmax()
        recovery2 = learning.regression_tikhonov(G2, measurements, mask, tau=0)
        recovery3 = np.zeros(recovery0.shape)
        for i in range(recovery0.shape[1]):
            recovery3[:, i] = learning.regression_tikhonov(
                    G2, measurements[:, i], mask, tau=0)

        np.testing.assert_allclose(recovery0, recovery1)
        np.testing.assert_allclose(recovery0, recovery2)
        np.testing.assert_allclose(recovery0, recovery3)

    def test_regression_tikhonov_3(self):
        """Solve a relaxed regression problem."""
        TAU = 3.5

        # Create the graph
        G = graphs.Sensor(N=100)
        G.estimate_lmax()

        # Create a smooth signal
        def filt(x):
            return 1 / (1+10*x)
        filt = filters.Filter(G, filt)
        rs = np.random.RandomState(1)
        signal = filt.analyze(rs.randn(G.N, 6))

        # Make the input signal
        mask = rs.uniform(0, 1, G.N) > 0.5
        measurements = signal.copy()
        measurements[~mask] = 0

        L = G.L.toarray()
        recovery = np.matmul(np.linalg.inv(np.diag(1*mask) + TAU * L),
                             (mask * measurements.T).T)

        # Solve the problem
        recovery0 = learning.regression_tikhonov(
                G, measurements, mask, tau=TAU)
        recovery1 = np.zeros(recovery0.shape)
        for i in range(recovery0.shape[1]):
            recovery1[:, i] = learning.regression_tikhonov(
                    G, measurements[:, i], mask, TAU)

        G2 = graphs.Graph(G.W.toarray())
        G2.estimate_lmax()
        recovery2 = learning.regression_tikhonov(G2, measurements, mask, TAU)
        recovery3 = np.zeros(recovery0.shape)
        for i in range(recovery0.shape[1]):
            recovery3[:, i] = learning.regression_tikhonov(
                    G2, measurements[:, i], mask, TAU)

        np.testing.assert_allclose(recovery, recovery0, atol=1e-5)
        np.testing.assert_allclose(recovery, recovery1, atol=1e-5)
        np.testing.assert_allclose(recovery, recovery2, atol=1e-5)
        np.testing.assert_allclose(recovery, recovery3, atol=1e-5)

    def test_classification_tikhonov(self):
        """Solve a classification problem."""
        G = graphs.Logo()
        signal = np.zeros([G.N], dtype=int)
        signal[G.info['idx_s']] = 1
        signal[G.info['idx_p']] = 2

        # Make the input signal
        np.random.seed(seed=1)
        mask = np.random.uniform(0, 1, G.N) > 0.3

        measures = signal.copy()
        measures[~mask] = -1

        # Solve the classification problem
        recovery = learning.classification_tikhonov(G, measures, mask, tau=0)
        recovery = np.argmax(recovery, axis=1)

        np.testing.assert_array_equal(recovery, signal)

        # test the function witht the simplex projection
        recovery2 = learning.classification_tikhonov_simplex(
                G, measures, mask, tau=0.1)

        # Assert that the probabilities sums to 1
        np.testing.assert_allclose(np.sum(recovery2, axis=1),1)

        # Check the quality of the solution
        recovery3 = np.argmax(recovery2, axis=1)
        np.testing.assert_allclose(signal, recovery3)


suite = unittest.TestLoader().loadTestsFromTestCase(TestCase)
