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

"""Tests for pie_chart.py."""

from graphy import pie_chart
from graphy import graphy_test


class PieChartTest(graphy_test.GraphyTest):

  def testNegativeSegmentSizes(self):
    self.assertRaises(AssertionError, pie_chart.PieChart,
                      [-5, 10], ['Negative', 'Positive'])
    chart = pie_chart.PieChart()
    self.assertRaises(AssertionError, pie_chart.Segment, -5, '0000ff', 'Dummy')
    segment = chart.AddSegment(10, color='0000ff', label='Dummy')
    self.assertRaises(AssertionError, segment._SetSize, -5)


if __name__ == '__main__':
  graphy_test.main()
