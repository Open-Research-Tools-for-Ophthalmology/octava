"""
This test is to verify that the SOAM calculation is working correctly.

- could add more tests to test how well our SOAM calc works with small local zig-zags
"""

import pytest
import numpy as np
from modules.biomarker import BiomarkerAnalyzer

class StraightLine:
    def __init__(self, length=10, num_points=100):
        self.length = length
        self.num_points = num_points

    def generate_points(self):
        x = np.linspace(0, self.length, self.num_points)
        y = np.zeros(self.num_points)
        return np.column_stack((x, y))

class SinX:
    def __init__(self, length=10, num_points=100):
        self.length = length
        self.num_points = num_points

    def generate_points(self):
        x = np.linspace(0, self.length, self.num_points)
        y = np.sin(x)
        return np.column_stack((x, y))

class Sinx2():
    def __init__(self, length=10, num_points=100):
        self.length = length
        self.num_points = num_points
    
    def generate_points(self):
        x = np.linspace(0, self.length, self.num_points)
        y = 2 * np.sin(x)
        return np.column_stack((x, y))

def test_straight_line():  # should return 0
    straight_line = StraightLine()
    points = straight_line.generate_points()

    result = BiomarkerAnalyzer._compute_soam_from_evenly_spaced_xy(points)
    assert result == 0.0

def test_sine_wave1():  # should return a positive value
    sine_wave = SinX()
    points = sine_wave.generate_points()

    result = BiomarkerAnalyzer._compute_soam_from_evenly_spaced_xy(points)
    assert result > 0.0

def test_sine_wave2():  # should be bigger than sine_wave1
    sine_wave1 = SinX()
    points1 = sine_wave1.generate_points()
    result1 = BiomarkerAnalyzer._compute_soam_from_evenly_spaced_xy(points1)

    sine_wave2 = Sinx2()
    points2 = sine_wave2.generate_points()
    result2 = BiomarkerAnalyzer._compute_soam_from_evenly_spaced_xy(points2)

    assert result2 > result1