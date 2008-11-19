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

"""Tests for the formatters."""

from graphy import formatters
from graphy import graphy_test
from graphy.backends import google_chart_api


class InlineLegendTest(graphy_test.GraphyTest):

  def setUp(self):
    self.chart = google_chart_api.LineChart()
    self.chart.formatters.append(formatters.InlineLegend)
    self.chart.AddLine([1, 2, 3], label='A')
    self.chart.AddLine([4, 5, 6], label='B')
    self.chart.auto_scale.buffer = 0

  def testLabelsAdded(self):
    self.assertEqual(self.Param('chxl'), '0:|A|B')

  def testLabelPositionedCorrectly(self):
    self.assertEqual(self.Param('chxp'), '0,3,6')
    self.assertEqual(self.Param('chxr'), '0,1,6')

  def testRegularLegendSuppressed(self):
    self.assertRaises(KeyError, self.Param, 'chdl')


if __name__ == '__main__':
  graphy_test.main()
