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

import string
import unittest

from graphy import common
from graphy import pie_chart
from graphy import bar_chart
from graphy import line_chart
from graphy import formatters
from graphy.backends import google_chart_api

# TODO: Once file reorganization is finished, move this into several
# smaller tests.

class TestEncoder(google_chart_api.BaseChartEncoder):
  """Simple implementation of BaseChartEncoder for testing common behavior."""
  def _GetType(self, chart):
    return {'chart_type': 'TEST_TYPE'}

  def _GetDependentAxis(self, chart):
    return chart.left


class TestChart(common.BaseChart):
  """Simple implementation of BaseChart for testing common behavior."""

  def __init__(self, points=None):
    super(TestChart, self).__init__()
    if points is not None:
      self.AddData(points)

  def AddData(self, points, color=None, label=None):
    series = common.DataSeries(points, color=color, style=None, label=label)
    self.data.append(series)
    return series


class GraphyTest(unittest.TestCase):
  """Base class for other Graphy tests."""

  def Param(self, param_name, chart=None):
    """Helper to look up a Google Chart API parameter for the given chart."""
    if chart is None:
      chart = self.chart
    params = chart.display._Params(chart)
    return params[param_name]

  def ExpectAxes(self, labels, positions):
    """Helper to test that the chart axis spec matches the expected values."""
    self.assertEqual(self.Param('chxl'), labels)
    self.assertEqual(self.Param('chxp'), positions)

  def GetChart(self, *args, **kwargs):
    """Get a chart object.  Other classes can override to change the
    type of chart being tested.
    """
    chart = TestChart(*args, **kwargs)
    chart.display = TestEncoder(chart)
    return chart

  def AddToChart(self, chart, points, color=None, label=None):
    """Add data to the chart.

    Chart is assumed to be of the same type as returned by self.GetChart().
    """
    return chart.AddData(points, color=color, label=label)


class BaseChartTest(GraphyTest):
  """Base class for all chart-specific tests"""

  def setUp(self):
    self.chart = self.GetChart()

  def assertIn(self, a, b, msg=None):
    """Just like self.assert_(a in b), but with a nicer default message."""
    if msg is None:
      msg = '"%s" not found in "%s"' % (a, b)
    self.assert_(a in b, msg)

  def assertNotIn(self, a, b, msg=None):
    """Just like self.assert_(a not in b), but with a nicer default message."""
    if msg is None:
      msg = '"%s" unexpectedly found in "%s"' % (a, b)
    self.assert_(a not in b, msg)

  def testImgAndUrlUseSameUrl(self):
    """Check that Img() and Url() return the same URL."""
    self.assertIn(self.chart.display.Url(500, 100),
                  self.chart.display.Img(500, 100))

  def testParamsAreStrings(self):
    """Test that params are all converted to strings."""
    self.chart.display.extra_params['test'] = 32
    self.assertEqual(self.Param('test'),  '32')

  def testExtraParams(self):
    self.chart.display.extra_params['test'] = 'test_param'
    self.assertEqual(self.Param('test'),  'test_param')

  def testExtraParamsOverideDefaults(self):
    self.assertNotEqual(self.Param('cht'), 'test')  # Sanity check.
    self.chart.display.extra_params['cht'] = 'test'
    self.assertEqual(self.Param('cht'), 'test')

  def testExtraParamsCanUseLongNames(self):
    self.chart.display.extra_params['color'] = 'XYZ'
    self.assertEqual(self.Param('chco'),  'XYZ')

  def testExtraParamsCanUseNewNames(self):
    """Make sure future Google Chart API features can be accessed immediately
    through extra_params.  (Double-checks that the long-to-short name
    conversion doesn't mess up the ability to use new features).
    """
    self.chart.display.extra_params['fancy_new_feature'] = 'shiny'
    self.assertEqual(self.Param('fancy_new_feature'),  'shiny')

  def testEmptyParamsDropped(self):
    """Check that empty parameters don't end up in the URL."""
    self.assertEqual(self.Param('chxt'), '')
    self.assertNotIn('chxt', self.chart.display.Url(0, 0))

  def testSizes(self):
    self.assertIn('89x102', self.chart.display.Url(89, 102))

    img = self.chart.display.Img(89, 102)
    self.assertIn('chs=89x102', img)
    self.assertIn("width=89", img)
    self.assertIn("height=102", img)

  def testChartType(self):
    self.assertEqual(self.Param('cht'), 'TEST_TYPE')

  def testChartSizeConvertedToInt(self):
    url = self.chart.display.Url(100.1, 200.2)
    self.assertIn('100x200', url)

  def testUrlBase(self):
    def assertStartsWith(actual_text, expected_start):
      message = "[%s] didn't start with [%s]" % (actual_text, expected_start)
      self.assert_(actual_text.startswith(expected_start), message)

    assertStartsWith(self.chart.display.Url(0, 0),
                     'http://chart.apis.google.com/chart')

    url_base = 'http://example.com/charts'
    self.chart.display.url_base = url_base
    assertStartsWith(self.chart.display.Url(0, 0), url_base)

  def testEnhancedEncoder(self):
    self.chart.display.enhanced_encoding = True
    self.assertEqual(self.Param('chd'), 'e:')

  def testUrlsEscaped(self):
    self.AddToChart(self.chart, [1, 2, 3])
    url = self.chart.display.Url(500, 100)
    self.assertNotIn('chd=s:', url)
    self.assertIn('chd=s%3A', url)

  def testDependentAxis(self):
    self.assertTrue(self.chart.left is self.chart.GetDependentAxis())
    self.assertTrue(self.chart.bottom is self.chart.GetIndependentAxis())

  def testCanRemoveDefaultFormatters(self):
    self.assertEqual(3, len(self.chart.formatters))
    # I don't know why you'd want to remove the default formatters like this.
    # It is just a proof that  we can manipulate the default formatters
    # through their aliases.
    self.chart.formatters.remove(self.chart.auto_color)
    self.chart.formatters.remove(self.chart.auto_legend)
    self.chart.formatters.remove(self.chart.auto_scale)
    self.assertEqual(0, len(self.chart.formatters))

  def testFormattersWorkOnCopy(self):
    """Make sure formatters can't modify the user's chart."""
    self.AddToChart(self.chart, [1])
    # By making sure our point is at the upper boundry, we make sure that both
    # line, pie, & bar charts encode it as a '9' in the simple encoding.
    self.chart.left.max = 1
    self.chart.left.min = 0
    # Sanity checks before adding a formatter.
    self.assertEqual(self.Param('chd'), 's:9')
    self.assertEqual(len(self.chart.data), 1)

    def MaliciousFormatter(chart):
      chart.data.pop() # Modify a mutable chart attribute
    self.chart.AddFormatter(MaliciousFormatter)

    self.assertEqual(self.Param('chd'), 's:', "Formatter wasn't used.")
    self.assertEqual(len(self.chart.data), 1,
                     "Formatter was able to modify original chart.")

    self.chart.formatters.remove(MaliciousFormatter)
    self.assertEqual(self.Param('chd'), 's:9',
                     "Chart changed even after removing the formatter")


class XYChartTest(BaseChartTest):
  """Base class for charts that display lines or points in 2d.

  Pretty much anything but the pie chart.
  """

  def testImgAndUrlUseSameUrl(self):
    """Check that Img() and Url() return the same URL."""
    super(XYChartTest, self).testImgAndUrlUseSameUrl()
    self.AddToChart(self.chart, range(0, 100))
    self.assertIn(self.chart.display.Url(500, 100),
                  self.chart.display.Img(500, 100))
    self.chart = self.GetChart([-1, 0, 1])
    self.assertIn(self.chart.display.Url(500, 100),
                  self.chart.display.Img(500, 100))

   # TODO: Once the deprecated AddSeries is removed, revisit
   # whether we need this test.
  def testAddSeries(self):
    self.chart.auto_scale.buffer = 0  # Buffer causes trouble for testing.
    self.assertEqual(self.Param('chd'), 's:')
    self.AddToChart(self.chart, (1, 2, 3))
    self.assertEqual(self.Param('chd'), 's:Af9')
    self.AddToChart(self.chart, (4, 5, 6))
    self.assertEqual(self.Param('chd'), 's:AMY,lx9')

   # TODO: Once the deprecated AddSeries is removed, revisit
   # whether we need this test.
  def testAddSeriesReturnsValue(self):
    points = (1, 2, 3)
    series = self.AddToChart(self.chart, points, '#000000')
    self.assertTrue(series is not None)
    self.assertEqual(series.data, points)
    self.assertEqual(series.color, '#000000')

  def testFlatSeries(self):
    """Make sure we handle scaling of a flat data series correctly (there are
    div by zero issues).
    """
    self.AddToChart(self.chart, [5, 5, 5])
    self.assertEqual(self.Param('chd'), 's:AAA')
    self.chart.left.min = 0
    self.chart.left.max = 5
    self.assertEqual(self.Param('chd'), 's:999')
    self.chart.left.min = 5
    self.chart.left.max = 15
    self.assertEqual(self.Param('chd'), 's:AAA')

  def testEmptyPointsStillCreatesSeries(self):
    """If we pass an empty list for points, we expect to get an empty data
    series, not nothing.  This way we can add data points later."""
    chart = self.GetChart()
    self.assertEqual(0, len(chart.data))
    data = []
    chart = self.GetChart(data)
    self.assertEqual(1, len(chart.data))
    self.assertEqual(0, len(chart.data[0].data))
    # This is the use case we are trying to serve: adding points later.
    data.append(0)
    self.assertEqual(1, len(chart.data[0].data))

  def testEmptySeriesDroppedFromParams(self):
    """By the time we make parameters, we don't want empty series to be
    included because it will mess up the indexes of other things like colors
    and makers.  They should be dropped instead."""
    self.chart.auto_scale.buffer = 0
    # Check just an empty series.
    self.AddToChart(self.chart, [], color='eeeeee')
    self.assertEqual(self.Param('chd'), 's:')
    # Now check when there are some real series in there too.
    self.AddToChart(self.chart, [1], color='111111')
    self.AddToChart(self.chart, [], color='FFFFFF')
    self.AddToChart(self.chart, [2], color='222222')
    self.assertEqual(self.Param('chd'), 's:A,9')
    self.assertEqual(self.Param('chco'), '111111,222222')

  def testDataSeriesCorrectlyConverted(self):
    # To avoid problems caused by floating-point errors, the input in this test
    # is carefully chosen to avoid 0.5 boundries (1.5, 2.5, 3.5, ...).
    chart = self.GetChart()
    chart.auto_scale.buffer = 0   # The buffer makes testing difficult.
    self.assertEqual(self.Param('chd', chart), 's:')
    chart = self.GetChart(range(0, 10))
    chart.auto_scale.buffer = 0
    self.assertEqual(self.Param('chd', chart), 's:AHOUbipv29')
    chart = self.GetChart(range(-10, 0))
    chart.auto_scale.buffer = 0
    self.assertEqual(self.Param('chd', chart), 's:AHOUbipv29')
    chart = self.GetChart((-1.1, 0.0, 1.1, 2.2))
    chart.auto_scale.buffer = 0
    self.assertEqual(self.Param('chd', chart), 's:AUp9')

  def testSeriesColors(self):
    self.AddToChart(self.chart, [1, 2, 3], '000000')
    self.AddToChart(self.chart, [4, 5, 6], 'FFFFFF')
    self.assertEqual(self.Param('chco'), '000000,FFFFFF')

  def testSeriesCaption_NoCaptions(self):
    self.AddToChart(self.chart, [1, 2, 3])
    self.AddToChart(self.chart, [4, 5, 6])
    self.assertRaises(KeyError, self.Param, 'chdl')

  def testSeriesCaption_SomeCaptions(self):
    self.AddToChart(self.chart, [1, 2, 3])
    self.AddToChart(self.chart, [4, 5, 6], label='Label')
    self.AddToChart(self.chart, [7, 8, 9])
    self.assertEqual(self.Param('chdl'), '|Label|')

  def testThatZeroIsPreservedInCaptions(self):
    """Test that a 0 caption becomes '0' and not ''.
    (This makes sure that the logic to rewrite a label of None to '' doesn't
    also accidentally rewrite 0 to '').
    """
    self.AddToChart(self.chart, [], label=0)
    self.AddToChart(self.chart, [], label=1)
    self.assertEqual(self.Param('chdl'), '0|1')

  def testSeriesCaption_AllCaptions(self):
    self.AddToChart(self.chart, [1, 2, 3], label='Its')
    self.AddToChart(self.chart, [4, 5, 6], label='Me')
    self.AddToChart(self.chart, [7, 8, 9], label='Mario')
    self.assertEqual(self.Param('chdl'), 'Its|Me|Mario')

  def testDefaultColorsApplied(self):
    self.AddToChart(self.chart, [1, 2, 3])
    self.AddToChart(self.chart, [4, 5, 6])
    self.assertEqual(self.Param('chco'), '0000ff,ff0000')

  def testAxisConstruction(self):
    axis = common.Axis()
    self.assertTrue(axis.min is None)
    self.assertTrue(axis.max is None)
    axis = common.Axis(-2, 16)
    self.assertEqual(axis.min, -2)
    self.assertEqual(axis.max, 16)

  def testShowingAxes(self):
    self.assertEqual(self.Param('chxt'), '')
    self.chart.left.min = 3
    self.chart.left.max = 5
    self.assertEqual(self.Param('chxt'), '')
    self.chart.left.labels = ['a']
    self.assertEqual(self.Param('chxt'), 'y')
    self.chart.right.labels = ['a']
    self.assertEqual(self.Param('chxt'), 'y,r')
    self.chart.left.labels = []  # Set back to the original state.
    self.assertEqual(self.Param('chxt'), 'r')

  def testAxisRanges(self):
    self.chart.left.labels = ['a']
    self.chart.bottom.labels = ['a']
    self.assertEqual(self.Param('chxr'), '')
    self.chart.left.min = -5
    self.chart.left.max = 10
    self.assertEqual(self.Param('chxr'), '0,-5,10')
    self.chart.bottom.min = 0.5
    self.chart.bottom.max = 0.75
    self.assertEqual(self.Param('chxr'), '0,-5,10|1,0.5,0.75')

  def testAxisLabels(self):
    self.ExpectAxes('', '')
    self.chart.left.labels = [10, 20, 30]
    self.ExpectAxes('0:|10|20|30', '')
    self.chart.left.label_positions = [0, 50, 100]
    self.ExpectAxes('0:|10|20|30', '0,0,50,100')
    self.chart.right.labels = ['cow', 'horse', 'monkey']
    self.chart.right.label_positions = [3.7, 10, -22.9]
    self.ExpectAxes('0:|10|20|30|1:|cow|horse|monkey',
                    '0,0,50,100|1,3.7,10,-22.9')

  def testGridBottomAxis(self):
    self.chart.bottom.min = 0
    self.chart.bottom.max = 20
    self.chart.bottom.grid_spacing = 10
    self.assertEqual(self.Param('chg'), '50,0,1,0')
    self.chart.bottom.grid_spacing = 2
    self.assertEqual(self.Param('chg'), '10,0,1,0')

  def testGridFloatingPoint(self):
    """Test that you can get decimal grid values in chg."""
    self.chart.bottom.min = 0
    self.chart.bottom.max = 8
    self.chart.bottom.grid_spacing = 1
    self.assertEqual(self.Param('chg'), '12.5,0,1,0')
    self.chart.bottom.max = 3
    self.assertEqual(self.Param('chg'), '33.3,0,1,0')

  def testGridLeftAxis(self):
    self.chart.auto_scale.buffer = 0
    self.AddToChart(self.chart, (0, 20))
    self.chart.left.grid_spacing = 5
    self.assertEqual(self.Param('chg'), '0,25,1,0')

  def testLabelGridBottomAxis(self):
    self.AddToChart(self.chart, [0, 20, 40])
    self.chart.bottom.label_gridlines = True
    self.chart.bottom.labels = ['Apple', 'Banana', 'Coconut']
    self.chart.bottom.label_positions = [1.5, 5, 8.5]
    self.chart.display._width = 320
    self.chart.display._height = 240
    self.assertEqual(self.Param('chxtc'), '0,-320')

  def testLabelGridLeftAxis(self):
    self.AddToChart(self.chart, [0, 20, 40])
    self.chart.left.label_gridlines = True
    self.chart.left.labels = ['Few', 'Some', 'Lots']
    self.chart.left.label_positions = [5, 20, 35]
    self.chart.display._width = 320
    self.chart.display._height = 240
    self.assertEqual(self.Param('chxtc'), '0,-320')

  def testLabelGridBothAxes(self):
    self.AddToChart(self.chart, [0, 20, 40])
    self.chart.left.label_gridlines = True
    self.chart.left.labels = ['Few', 'Some', 'Lots']
    self.chart.left.label_positions = [5, 20, 35]
    self.chart.bottom.label_gridlines = True
    self.chart.bottom.labels = ['Apple', 'Banana', 'Coconut']
    self.chart.bottom.label_positions = [1.5, 5, 8.5]
    self.chart.display._width = 320
    self.chart.display._height = 240
    self.assertEqual(self.Param('chxtc'), '0,-320|1,-320')

  def testDefaultDataScalingNotPersistant(self):
    """The auto-scaling shouldn't permanantly set the scale."""
    self.chart.auto_scale.buffer = 0  # Buffer just makes the math tricky here.
    # This data should scale to the simple encoding's min/middle/max values
    # (A, f, 9).
    self.AddToChart(self.chart, [1, 2, 3])
    self.assertEqual(self.Param('chd'), 's:Af9')
    # Different data that maintains the same relative spacing *should* scale
    # to the same min/middle/max.
    self.chart.data[0].data = [10, 20, 30]
    self.assertEqual(self.Param('chd'), 's:Af9')

  def FakeScale(self, data, old_min, old_max, new_min, new_max):
    self.min = old_min
    self.max = old_max
    return data

  def testDefaultDataScaling(self):
    """If you don't set min/max, it should use the data's min/max."""
    orig_scale = google_chart_api._ScaleData
    google_chart_api._ScaleData = self.FakeScale
    try:
      self.AddToChart(self.chart, [2, 3, 5, 7, 11])
      self.chart.auto_scale.buffer = 0
      # This causes scaling to happen & calls FakeScale.
      self.chart.display.Url(0, 0)
      self.assertEqual(2, self.min)
      self.assertEqual(11, self.max)
    finally:
      google_chart_api._ScaleData = orig_scale

  def testDefaultDataScalingAvoidsCropping(self):
    """The default scaling should give a little buffer to avoid cropping."""
    orig_scale = google_chart_api._ScaleData
    google_chart_api._ScaleData = self.FakeScale
    try:
      self.AddToChart(self.chart, [1, 6])
      # This causes scaling to happen & calls FakeScale.
      self.chart.display.Url(0, 0)
      buffer = 5 * self.chart.auto_scale.buffer
      self.assertEqual(1 - buffer, self.min)
      self.assertEqual(6 + buffer, self.max)
    finally:
      google_chart_api._ScaleData = orig_scale

  def testExplicitDataScaling(self):
    """If you set min/max, data should be scaled to this."""
    orig_scale = google_chart_api._ScaleData
    google_chart_api._ScaleData = self.FakeScale
    try:
      self.AddToChart(self.chart, [2, 3, 5, 7, 11])
      self.chart.left.min = -7
      self.chart.left.max = 49
      # This causes scaling to happen & calls FakeScale.
      self.chart.display.Url(0, 0)
      self.assertEqual(-7, self.min)
      self.assertEqual(49, self.max)
    finally:
      google_chart_api._ScaleData = orig_scale

  def testImplicitMinValue(self):
    """min values should be filled in if they are not set explicitly."""
    orig_scale = google_chart_api._ScaleData
    google_chart_api._ScaleData = self.FakeScale
    try:
      self.AddToChart(self.chart, [0, 10])
      self.chart.auto_scale.buffer = 0
      self.chart.display.Url(0, 0)  # This causes a call to FakeScale.
      self.assertEqual(0, self.min)
      self.chart.left.min = -5
      self.chart.display.Url(0, 0)  # This causes a call to FakeScale.
      self.assertEqual(-5, self.min)
    finally:
      google_chart_api._ScaleData = orig_scale

  def testImplicitMaxValue(self):
    """max values should be filled in if they are not set explicitly."""
    orig_scale = google_chart_api._ScaleData
    google_chart_api._ScaleData = self.FakeScale
    try:
      self.AddToChart(self.chart, [0, 10])
      self.chart.auto_scale.buffer = 0
      self.chart.display.Url(0, 0)  # This causes a call to FakeScale.
      self.assertEqual(10, self.max)
      self.chart.left.max = 15
      self.chart.display.Url(0, 0)  # This causes a call to FakeScale.
      self.assertEqual(15, self.max)
    finally:
      google_chart_api._ScaleData = orig_scale

  def testNoneCanAppearInData(self):
    """None should be a valid value in a data series.  (It means "no data at
    this point")
    """
    # Buffer makes comparison difficult because min/max aren't A & 9
    self.chart.auto_scale.buffer = 0
    self.AddToChart(self.chart, [1, None, 3])
    self.assertEqual(self.Param('chd'), 's:A_9')

  def testResolveLabelCollision(self):
    self.chart.auto_scale.buffer = 0
    self.AddToChart(self.chart, [500, 1000])
    self.AddToChart(self.chart, [100, 999])
    self.AddToChart(self.chart, [200, 900])
    self.AddToChart(self.chart, [200, -99])
    self.AddToChart(self.chart, [100, -100])
    self.chart.right.max = 1000
    self.chart.right.min = -100
    self.chart.right.labels = [1000, 999, 900, 0, -99, -100]
    self.chart.right.label_positions =  self.chart.right.labels
    separation = formatters.LabelSeparator(right=40)
    self.chart.AddFormatter(separation)
    self.assertEqual(self.Param('chxp'), '0,1000,960,900,0,-60,-100')

    # Try to force a greater spacing than possible
    separation.right = 300
    self.assertEqual(self.Param('chxp'), '0,1000,780,560,340,120,-100')

    # Cluster some values around the lower and upper threshold to verify
    # that order is preserved.
    self.chart.right.labels = [1000, 901, 900, 899, 10, 1, -50, -100]
    self.chart.right.label_positions =  self.chart.right.labels
    separation.right = 100
    self.assertEqual(self.Param('chxp'), '0,1000,900,800,700,200,100,0,-100')
    self.assertEqual(self.Param('chxl'), '0:|1000|901|900|899|10|1|-50|-100')

    # Try to adjust a single label
    self.chart.right.labels = [1000]
    self.chart.right.label_positions =  self.chart.right.labels
    self.assertEqual(self.Param('chxp'), '0,1000')
    self.assertEqual(self.Param('chxl'), '0:|1000')

  def testAdjustSingleLabelDoesNothing(self):
    """Make sure adjusting doesn't bork the single-label case."""
    self.AddToChart(self.chart, (5, 6, 7))
    self.chart.left.labels = ['Cutoff']
    self.chart.left.label_positions = [3]
    def CheckExpectations():
      self.assertEqual(self.Param('chxl'), '0:|Cutoff')
      self.assertEqual(self.Param('chxp'), '0,3')
    CheckExpectations() # Check without adjustment
    self.chart.AddFormatter(formatters.LabelSeparator(right=15))
    CheckExpectations() # Make sure adjustment hasn't changed anything

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


# Extend XYChartTest so that we pick up & repeat all the basic tests which
# LineCharts should continue to satisfy
class LineChartTest(XYChartTest):

  def GetChart(self, *args, **kwargs):
    return google_chart_api.LineChart(*args, **kwargs)

  def AddToChart(self, chart, points, color=None, label=None):
    return chart.AddLine(points, color=color, label=label)

  def testChartType(self):
    self.assertEqual(self.Param('cht'), 'lc')

  def testMarkers(self):
    x = common.Marker('x', '0000FF', 5)
    o = common.Marker('o', '00FF00', 5)
    line = common.Marker('V', 'dddddd', 1)
    self.chart.AddLine([1, 2, 3], markers=[(1, x), (2, o), (3, x)])
    self.chart.AddLine([4, 5, 6], markers=[(x, line) for x in range(3)])
    x = 'x,0000FF,0,%s,5'
    o = 'o,00FF00,0,%s,5'
    V = 'V,dddddd,1,%s,1'
    actual = self.Param('chm')
    expected = [m % i for i, m in zip([1, 2, 3, 0, 1, 2], [x, o, x, V, V, V])]
    expected = '|'.join(expected)
    error_msg = '\n%s\n!=\n%s' % (actual, expected)
    self.assertEqual(actual, expected, error_msg)

  def testLinePatterns(self):
    self.chart.AddLine([1, 2, 3])
    self.chart.AddLine([4, 5, 6], pattern=line_chart.LineStyle.DASHED)
    self.assertEqual(self.Param('chls'), '1,1,0|1,8,4')

  def testMultipleAxisLabels(self):
    self.ExpectAxes('', '')

    left_axis = self.chart.AddAxis(common.AxisPosition.LEFT,
                                   common.Axis())
    left_axis.labels = [10, 20, 30]
    left_axis.label_positions = [0, 50, 100]
    self.ExpectAxes('0:|10|20|30', '0,0,50,100')

    bottom_axis = self.chart.AddAxis(common.AxisPosition.BOTTOM,
                                     common.Axis())
    bottom_axis.labels = ['A', 'B', 'c', 'd']
    bottom_axis.label_positions = [0, 33, 66, 100]
    sub_axis = self.chart.AddAxis(common.AxisPosition.BOTTOM,
                                  common.Axis())
    sub_axis.labels = ['CAPS', 'lower']
    sub_axis.label_positions = [0, 50]
    self.ExpectAxes('0:|10|20|30|1:|A|B|c|d|2:|CAPS|lower',
                    '0,0,50,100|1,0,33,66,100|2,0,50')

    self.chart.AddAxis(common.AxisPosition.RIGHT, left_axis)
    self.ExpectAxes('0:|10|20|30|1:|10|20|30|2:|A|B|c|d|3:|CAPS|lower',
                    '0,0,50,100|1,0,50,100|2,0,33,66,100|3,0,50')
    self.assertEqual(self.Param('chxt'), 'y,r,x,x')

  def testAxisProperties(self):
    self.ExpectAxes('', '')

    self.chart.top.labels = ['cow', 'horse', 'monkey']
    self.chart.top.label_positions = [3.7, 10, -22.9]
    self.ExpectAxes('0:|cow|horse|monkey', '0,3.7,10,-22.9')

    self.chart.left.labels = [10, 20, 30]
    self.chart.left.label_positions = [0, 50, 100]
    self.ExpectAxes('0:|10|20|30|1:|cow|horse|monkey',
                    '0,0,50,100|1,3.7,10,-22.9')
    self.assertEqual(self.Param('chxt'), 'y,t')

    sub_axis = self.chart.AddAxis(common.AxisPosition.BOTTOM,
                                  common.Axis())
    sub_axis.labels = ['CAPS', 'lower']
    sub_axis.label_positions = [0, 50]
    self.ExpectAxes('0:|10|20|30|1:|CAPS|lower|2:|cow|horse|monkey',
                    '0,0,50,100|1,0,50|2,3.7,10,-22.9')
    self.assertEqual(self.Param('chxt'), 'y,x,t')

    self.chart.bottom.labels = ['A', 'B', 'C']
    self.chart.bottom.label_positions = [0, 33, 66]
    self.ExpectAxes('0:|10|20|30|1:|A|B|C|2:|CAPS|lower|3:|cow|horse|monkey',
                    '0,0,50,100|1,0,33,66|2,0,50|3,3.7,10,-22.9')
    self.assertEqual(self.Param('chxt'), 'y,x,x,t')


# Extend LineChartTest so that we pick up & repeat all the line tests which
# Sparklines should continue to satisfy
class SparklineTest(LineChartTest):

  def GetChart(self, *args, **kwargs):
    return google_chart_api.Sparkline(*args, **kwargs)

  def testChartType(self):
    self.assertEqual(self.Param('cht'), 'lfi')


# Extend XYChartTest so that we pick up & repeat all the basic tests which
# BarCharts should continue to satisfy
class BarChartTest(XYChartTest):

  def GetChart(self, *args, **kwargs):
    return google_chart_api.BarChart(*args, **kwargs)

  def AddToChart(self, chart, points, color=None, label=None):
    return chart.AddBars(points, color=color, label=label)

  def testChartType(self):
    def Check(vertical, stacked, expected_type):
      self.chart.vertical = vertical
      self.chart.stacked = stacked
      self.assertEqual(self.Param('cht'), expected_type)
    Check(vertical=True,  stacked=True,  expected_type='bvs')
    Check(vertical=True,  stacked=False, expected_type='bvg')
    Check(vertical=False, stacked=True,  expected_type='bhs')
    Check(vertical=False, stacked=False, expected_type='bhg')

  def testSingleBarCase(self):
    """Test that we can handle a bar chart with only a single bar."""
    self.AddToChart(self.chart, [1])
    self.assertEqual(self.Param('chd'), 's:A')

  def testHorizontalScaling(self):
    """Test the scaling works correctly on horizontal bar charts (which have
    min/max on a different axis than other charts).
    """
    self.AddToChart(self.chart, [3])
    self.chart.vertical = False
    self.chart.bottom.min = 0
    self.chart.bottom.max = 3
    self.assertEqual(self.Param('chd'), 's:9')  # 9 is far right edge.
    self.chart.bottom.max = 6
    self.assertEqual(self.Param('chd'), 's:f')  # f is right in the middle.

  def testZeroPoint(self):
    self.AddToChart(self.chart, [-5, 0, 5])
    self.assertEqual(self.Param('chp'), str(.5))    # Auto scaling.
    self.chart.left.min = 0
    self.chart.left.max = 5
    self.assertRaises(KeyError, self.Param, 'chp')  # No negative values.
    self.chart.left.min = -5
    self.assertEqual(self.Param('chp'), str(.5))    # Explicit scaling.
    self.chart.left.max = 15
    self.assertEqual(self.Param('chp'), str(.25))   # Different zero point.
    self.chart.left.max = -1
    self.assertEqual(self.Param('chp'), str(1))     # Both negative values.

  def testLabelsInCorrectOrder(self):
    """Test that we reverse labels for horizontal bar charts
    (Otherwise they are backwards from what you would expect)
    """
    self.chart.left.labels = [1, 2, 3]
    self.chart.vertical = True
    self.assertEqual(self.Param('chxl'), '0:|1|2|3')
    self.chart.vertical = False
    self.assertEqual(self.Param('chxl'), '0:|3|2|1')

  def testLabelRangeDefaultsToDataScale(self):
    """Test that if you don't set axis ranges, they default to the data
    scale.
    """
    self.chart.auto_scale.buffer = 0  # Buffer causes trouble for testing.
    self.AddToChart(self.chart, [1, 5])
    self.chart.left.labels = (1, 5)
    self.chart.left.labels_positions = (1, 5)
    self.assertEqual(self.Param('chxr'), '0,1,5')

  def testDefaultBarStyle(self):
    self.assertNotIn('chbh', self.chart.display._Params(self.chart))
    self.chart.display.style = bar_chart.BarStyle(None, None, None)
    self.assertNotIn('chbh', self.chart.display._Params(self.chart))
    self.chart.display.style = bar_chart.BarStyle(10, 3, 6)
    self.assertNotIn('chbh', self.chart.display._Params(self.chart))
    self.AddToChart(self.chart, [1, 2, 3])
    self.assertEqual(self.Param('chbh'), '10,3,6')
    self.chart.display.style = bar_chart.BarStyle(10)
    self.assertEqual(self.Param('chbh'), '10,4,8')

  def testAutoBarSizing(self):
    self.AddToChart(self.chart, [1, 2, 3])
    self.AddToChart(self.chart, [4, 5, 6])
    self.chart.display.style = bar_chart.BarStyle(None, 3, 6)
    self.chart.display._width = 100
    self.chart.display._height = 1000
    self.chart.stacked = False
    self.assertEqual(self.Param('chbh'), '13,3,6')
    self.chart.stacked = True
    self.assertEqual(self.Param('chbh'), '31,3')
    self.chart.vertical = False
    self.chart.stacked = False
    self.assertEqual(self.Param('chbh'), '163,3,6')
    self.chart.stacked = True
    self.assertEqual(self.Param('chbh'), '331,3')
    self.chart.display._height = 1
    self.assertEqual(self.Param('chbh'), '1,3')

  def testAutoBarSpacing(self):
    self.AddToChart(self.chart, [1, 2, 3])
    self.AddToChart(self.chart, [4, 5, 6])
    self.chart.display.style = bar_chart.BarStyle(10, 1, None)
    self.assertEqual(self.Param('chbh'), '10,1,2')
    self.chart.display.style = bar_chart.BarStyle(10, None, 2)
    self.assertEqual(self.Param('chbh'), '10,1,2')
    self.chart.display.style = bar_chart.BarStyle(10, None, 1)
    self.assertEqual(self.Param('chbh'), '10,0,1')

  def testStackedDataScaling(self):
    self.AddToChart(self.chart, [10, 20, 30])
    self.AddToChart(self.chart, [-5, -10, -15])
    self.chart.stacked = True
    self.assertEqual(self.Param('chd'), 's:iu6,PJD')
    self.chart.stacked = False
    self.assertEqual(self.Param('chd'), 's:iu6,PJD')

    self.chart = self.GetChart()
    self.chart.stacked = True
    self.AddToChart(self.chart, [10, 20, 30])
    self.AddToChart(self.chart, [5, -10, 15])
    self.assertEqual(self.Param('chd'), 's:Xhr,SDc')
    self.AddToChart(self.chart, [-15, -10, -45])
    self.assertEqual(self.Param('chd'), 's:lrx,iYo,VYD')
    # TODO: Figure out how to deal with missing data points, test them

  def testNegativeBars(self):
    self.chart.stacked = True
    self.AddToChart(self.chart, [-10,-20,-30])
    self.assertEqual(self.Param('chd'), 's:oVD')
    self.AddToChart(self.chart, [-1,-2,-3])
    self.assertEqual(self.Param('chd'), 's:pZI,531')
    self.chart.stacked = False
    self.assertEqual(self.Param('chd'), 's:pWD,642')

  def testDependentAxis(self):
    self.chart.vertical = True
    self.assertTrue(self.chart.left is self.chart.GetDependentAxis())
    self.assertTrue(self.chart.bottom is self.chart.GetIndependentAxis())
    self.chart.vertical = False
    self.assertTrue(self.chart.bottom, self.chart.GetDependentAxis())
    self.assertTrue(self.chart.left, self.chart.GetIndependentAxis())


# Extend BaseChartTest so that we pick up & repeat all the line tests which
# Pie Charts should continue to satisfy
class PieChartTest(BaseChartTest):

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


class LineStyleTest(GraphyTest):

  def testPresets(self):
    """Test selected traits from the preset line styles."""
    self.assertEqual(0, line_chart.LineStyle.solid.off)
    self.assert_(line_chart.LineStyle.dashed.off > 0)
    self.assert_(line_chart.LineStyle.solid.width <
                 line_chart.LineStyle.thick_solid.width)


class EncoderTest(GraphyTest):

  def setUp(self):
    self.simple = google_chart_api._SimpleDataEncoder()

  def testEmpty(self):
    self.assertEqual('', self.simple.Encode([]))

  def testSingle(self):
    self.assertEqual('A', self.simple.Encode([0]))

  def testFull(self):
    full = string.ascii_uppercase + string.ascii_lowercase + string.digits
    self.assertEqual(full, self.simple.Encode(range(0, 62)))

  def testRoundingError(self):
    """Scaling might give us some rounding error.  Make sure that the encoder
    deals with it properly.
    """
    a = [-1, 0, 0, 1, 60, 61, 61, 62]
    b = [-0.999999, -0.00001, 0.00001, 0.99998,
         60.00001, 60.99999, 61.00001, 61.99998]
    self.assertEqual(self.simple.Encode(a), self.simple.Encode(b))

  def testFloats(self):
    ints   = [1, 2, 3, 4]
    floats = [1.1, 2.1, 3.1, 4.1]
    self.assertEqual(self.simple.Encode(ints), self.simple.Encode(floats))

  def testOutOfRangeDropped(self):
    """Confirm that values outside of min/max are left blank."""
    nums = [-79, -1, 0, 1, 61, 62, 1012]
    self.assertEqual('__AB9__', self.simple.Encode(nums))

  def testNoneDropped(self):
    """Confirm that the value None is left blank."""
    self.assertEqual('_JI_H', self.simple.Encode([None, 9, 8, None, 7]))


class EnhandedEncoderTest(GraphyTest):

  def setUp(self):
    self.encoder = google_chart_api._EnhancedDataEncoder()

  def testEmpty(self):
    self.assertEqual('', self.encoder.Encode([]))

  def testFull(self):
    full = ''.join(self.encoder.code)
    self.assertEqual(full, self.encoder.Encode(range(0, 4096)))

  def testOutOfRangeDropped(self):
    nums = [-79, -1, 0, 1, 61, 4096, 10012]
    self.assertEqual('____AAABA9____', self.encoder.Encode(nums))

  def testNoneDropped(self):
    self.assertEqual('__AJAI__AH', self.encoder.Encode([None, 9, 8, None, 7]))


class InlineLegendTest(GraphyTest):

  def setUp(self):
    self.chart = self.GetChart()
    self.chart.formatters.append(formatters.InlineLegend)
    self.AddToChart(self.chart, [1, 2, 3], label='A')
    self.AddToChart(self.chart, [4, 5, 6], label='B')
    self.chart.auto_scale.buffer = 0

  def testLabelsAdded(self):
    self.assertEqual(self.Param('chxl'), '0:|A|B')

  def testLabelPositionedCorrectly(self):
    self.assertEqual(self.Param('chxp'), '0,3,6')
    self.assertEqual(self.Param('chxr'), '0,1,6')

  def testRegularLegendSuppressed(self):
    self.assertRaises(KeyError, self.Param, 'chdl')


class UtilTest(GraphyTest):

  """Test the various utility functions."""

  def testScaleIntegerData(self):
    scale = google_chart_api._ScaleData
    # Identity
    self.assertEqual([1, 2, 3], scale([1, 2, 3], 1, 3, 1, 3))
    self.assertEqual([-1, 0, 1], scale([-1, 0, 1], -1, 1, -1, 1))

    # Translate
    self.assertEqual([4, 5, 6], scale([1, 2, 3], 1, 3, 4, 6))
    self.assertEqual([-3, -2, -1], scale([1, 2, 3], 1, 3, -3, -1))

    # Scale
    self.assertEqual([1, 3.5, 6], scale([1, 2, 3], 1, 3, 1, 6))
    self.assertEqual([-6, 0, 6], scale([1, 2, 3], 1, 3, -6, 6))

    # Scale and Translate
    self.assertEqual([100, 200, 300], scale([1, 2, 3], 1, 3, 100, 300))

  def testScaleDataWithDifferentMinMax(self):
    scale = google_chart_api._ScaleData
    self.assertEqual([1.5, 2, 2.5], scale([1, 2, 3], 0, 4, 1, 3))
    self.assertEqual([-2, 2, 6], scale([0, 2, 4], 1, 3, 0, 4))

  def testScaleFloatingPointData(self):
    scale = google_chart_api._ScaleData
    data = [-3.14, -2.72, 0, 2.72, 3.14]
    scaled_e = 5 + 5 * 2.72 / 3.14
    expected_data = [0, 10 - scaled_e, 5, scaled_e, 10]
    actual_data = scale(data, -3.14, 3.14, 0, 10)
    for expected, actual in zip(expected_data, actual_data):
      self.assertAlmostEqual(expected, actual)

  def testScaleDataOverRealRange(self):
    scale = google_chart_api._ScaleData
    self.assertEqual([0, 30.5, 61], scale([1, 2, 3], 1, 3, 0, 61))

  def testScalingLotsOfData(self):
    data = range(0, 100)
    expected = range(-100, 100, 2)
    actual = google_chart_api._ScaleData(data, 0, 100, -100, 100)
    self.assertEqual(expected, actual)

  def testLongNames(self):
    params = dict(size='S', data='D', chg='G')
    params = google_chart_api._ShortenParameterNames(params)
    self.assertEqual(dict(chs='S', chd='D', chg='G'), params)

  def testCantUseBothLongAndShortName(self):
    """Make sure we don't let the user specify both the long and the short
    version of a parameter.  (If we did, which one would we pick?)
    """
    params = dict(size='long', chs='short')
    self.assertRaises(KeyError, google_chart_api._ShortenParameterNames, params)


if __name__ == '__main__':
  unittest.main()
