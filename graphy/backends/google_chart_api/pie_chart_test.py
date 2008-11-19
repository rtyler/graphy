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

"""Unittest for Graphy and Google Chart API backend."""

from graphy import graphy_test
from graphy import pie_chart
from graphy.backends import google_chart_api
from graphy.backends.google_chart_api import base_encoder_test


# Extend BaseChartTest so that we pick up & repeat all the line tests which
# Pie Charts should continue to satisfy
class PieChartTest(base_encoder_test.BaseChartTest):

  def GetChart(self, *args, **kwargs):
    return google_chart_api.PieChart(*args, **kwargs)

  def AddToChart(self, chart, points, color=None, label=None):
    return chart.AddSegment(pie_chart.Segment(points[0], color, label))

  def testCanRemoveDefaultFormatters(self):
    # Override this test, as pie charts don't have default formatters.
    pass

  def testChartType(self):
    self.chart.display.is3d = False
    self.assertEqual(self.Param('cht'), 'p')
    self.chart.display.is3d = True
    self.assertEqual(self.Param('cht'), 'p3')

  def testEmptyChart(self):
    self.assertEqual(self.Param('chd'), 's:')
    self.assertEqual(self.Param('chco'), '')
    self.assertEqual(self.Param('chl'), '')

  def testChartCreation(self):
    self.chart = self.GetChart([1,2,3], ['Mouse', 'Cat', 'Dog'])
    self.assertEqual(self.Param('chd'), 's:Up9')
    self.assertEqual(self.Param('chl'), 'Mouse|Cat|Dog')
    self.assertEqual(self.Param('cht'), 'p')
    # TODO: Get 'None' labels to work and test them

  def testAddSegment(self):
    self.chart = self.GetChart([1,2,3], ['Mouse', 'Cat', 'Dog'])
    self.chart.AddSegment(pie_chart.Segment(4, label='Horse'))
    self.assertEqual(self.Param('chd'), 's:Pfu9')
    self.assertEqual(self.Param('chl'), 'Mouse|Cat|Dog|Horse')

  def testAddMultipleSegments(self):
    self.chart.AddSegments([1,2,3],
                           ['Mouse', 'Cat', 'Dog'],
                           ['ff0000', '00ff00', '0000ff'])
    self.assertEqual(self.Param('chd'), 's:Up9')
    self.assertEqual(self.Param('chl'), 'Mouse|Cat|Dog')
    self.assertEqual(self.Param('chco'), 'ff0000,00ff00,0000ff')
    # skip two colors
    self.chart.AddSegments([4,5,6], ['Horse', 'Moose', 'Elephant'], ['cccccc'])
    self.assertEqual(self.Param('chd'), 's:KUfpz9')
    self.assertEqual(self.Param('chl'), 'Mouse|Cat|Dog|Horse|Moose|Elephant')
    self.assertEqual(self.Param('chco'), 'ff0000,00ff00,0000ff,cccccc')

  def testSetColors(self):
    self.assertEqual(self.Param('chco'), '')
    self.chart.AddSegment(pie_chart.Segment(1, label='Mouse'))
    self.chart.AddSegment(pie_chart.Segment(5, label='Moose'))
    self.chart.SetColors('000033', '0000ff')
    self.assertEqual(self.Param('chco'), '000033,0000ff')
    self.chart.AddSegment(pie_chart.Segment(6, label='Elephant'))
    self.assertEqual(self.Param('chco'), '000033,0000ff')

  def testHugeSegmentSizes(self):
    self.chart = self.GetChart([1000000000000000L,3000000000000000L],
                                      ['Big', 'Uber'])
    self.assertEqual(self.Param('chd'), 's:U9')
    self.chart.display.enhanced_encoding = True
    self.assertEqual(self.Param('chd'), 'e:VV..')

  def testSetSegmentSize(self):
    segment1 = pie_chart.Segment(1)
    self.chart.AddSegment(segment1)
    segment2 = pie_chart.Segment(2)
    self.chart.AddSegment(segment2)
    self.assertEqual(self.Param('chd'), 's:f9')
    segment2.size = 3
    self.assertEquals(segment1.size, 1)
    self.assertEquals(segment2.size, 3)
    self.assertEqual(self.Param('chd'), 's:U9')

  def testNegativeSegmentSizes(self):
    self.assertRaises(AssertionError, self.GetChart,
                      [-5, 10], ['Negative', 'Positive'])
    self.chart = self.GetChart()
    self.assertRaises(AssertionError, pie_chart.Segment, -5, '0000ff', 'Dummy')
    segment = self.chart.AddSegment(pie_chart.Segment(10, '0000ff', 'Dummy'))
    self.assertRaises(AssertionError, segment._SetSize, -5)


if __name__ == '__main__':
  graphy_test.main()
