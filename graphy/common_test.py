#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for common.py."""

from graphy import common
from graphy import graphy_test
from graphy.backends import google_chart_api


class CommonTest(graphy_test.GraphyTest):

  def setUp(self):
    self.chart = google_chart_api.LineChart()

  def testDependentAxis(self):
    self.assertTrue(self.chart.left is self.chart.GetDependentAxis())
    self.assertTrue(self.chart.bottom is self.chart.GetIndependentAxis())
  
  def testAxisAssignment(self):
    """Make sure axis assignment works properly"""
    new_axis = common.Axis()
    self.chart.top = new_axis
    self.assertTrue(self.chart.top is new_axis)
    new_axis = common.Axis()
    self.chart.bottom = new_axis
    self.assertTrue(self.chart.bottom is new_axis)
    new_axis = common.Axis()
    self.chart.left = new_axis
    self.assertTrue(self.chart.left is new_axis)
    new_axis = common.Axis()
    self.chart.right = new_axis
    self.assertTrue(self.chart.right is new_axis)

  def testAxisConstruction(self):
    axis = common.Axis()
    self.assertTrue(axis.min is None)
    self.assertTrue(axis.max is None)
    axis = common.Axis(-2, 16)
    self.assertEqual(axis.min, -2)
    self.assertEqual(axis.max, 16)

  def testGetDependentIndependentAxes(self):
    c = self.chart
    self.assertEqual([c.left, c.right], c.GetDependentAxes())
    self.assertEqual([c.top, c.bottom], c.GetIndependentAxes())
    right2 = c.AddAxis(common.AxisPosition.RIGHT, common.Axis())
    bottom2 = c.AddAxis(common.AxisPosition.BOTTOM, common.Axis())
    self.assertEqual([c.left, c.right, right2], c.GetDependentAxes())
    self.assertEqual([c.top, c.bottom, bottom2], c.GetIndependentAxes())


if __name__ == '__main__':
  graphy_test.main()
