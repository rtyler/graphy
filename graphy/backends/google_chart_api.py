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

"""Backend which can generate charts using the Google Chart API.

The only thing you should be using out of here are the helper methods:
  LineChart
  PieChart
  Sparkline
  etc.
"""

import string
import urllib
import warnings

from graphy import common
from graphy import line_chart
from graphy import bar_chart
from graphy import pie_chart


# TODO: Find a better representation
_LONG_NAMES = dict(
  client_id='chc',
  size='chs',
  chart_type='cht',
  axis_type='chxt',
  axis_label='chxl',
  axis_position='chxp',
  axis_range='chxr',
  axis_style='chxs',
  data='chd',
  label='chl',
  y_label='chly',
  data_label='chld',
  data_series_label='chdl',
  color='chco',
  extra='chp',
  right_label='chlr',
  label_position='chlp',
  y_label_position='chlyp',
  right_label_position='chlrp',
  grid='chg',
  axis='chx',
  # This undocumented parameter specifies the length of the tick marks for an
  # axis. Negative values will extend tick marks into the main graph area.
  axis_tick_marks='chxtc',
  line_style='chls',
  marker='chm',
  fill='chf',
  bar_height='chbh',
  label_color='chlc',
  signature='sig',
  output_format='chof',
  title='chtt',
  title_style='chts',
  callback='callback',
  )

""" Used for parameters which involve joining multiple values."""
_JOIN_DELIMS = dict(
  data=',',
  color=',',
  line_style='|',
  marker='|',
  axis_type=',',
  axis_range='|',
  axis_label='|',
  axis_position='|',
  axis_tick_marks='|',
  data_series_label='|',
  label='|',
  bar_height=',',
)

class BaseChartEncoder(object):

  """Base class for encoders which turn chart objects into Google Chart URLS.

  Object attributes:
    extra_params: Dict to add/override specific chart params.  Of the
                  form param:string, passed directly to the Google Chart API.
                  For example, 'cht':'lti' becomes ?cht=lti in the URL.
    url_base: The prefix to use for URLs.  If you want to point to a different
              server for some reason, you would override this.
    formatters: TODO: Need to explain how these work, and how they are
                different from chart formatters.
    enhanced_encoding: If True, uses enhanced encoding.  If
                       False, simple encoding is used.
    escape_url: If True, URL will be properly escaped.  If False, characters
                like | and , will be unescapped (which makes the URL easier to
                read).
  """

  def __init__(self, chart):
    self.extra_params = {}  # You can add specific params here.
    self.url_base = 'http://chart.apis.google.com/chart'
    self.formatters = self._GetFormatters()
    self.chart = chart
    self.enhanced_encoding = False
    self.escape_url = True  # You can turn off URL escaping for debugging.
    self._width = 0   # These are set when someone calls Url()
    self._height = 0

  def Url(self, width, height):
    """Get the URL for our graph."""
    self._width = width
    self._height = height
    params = self._Params(self.chart)
    return _EncodeUrl(self.url_base, params, self.escape_url)

  def Img(self, width, height):
    """Get an image tag for our graph."""
    url = self.Url(width, height)
    tag = "<img src='%s' width=%s height=%s alt='chart'/>"
    return tag % (url, width, height)

  def _GetType(self, chart):
    """Return the correct chart_type param for the chart."""
    raise NotImplementedError

  def _GetFormatters(self):
    """Get a list of formatter functions to use for encoding."""
    formatters = [self._GetLegendParams,
                  self._GetDataSeriesParams,
                  self._GetAxisParams,
                  self._GetGridParams,
                  self._GetType,
                  self._GetExtraParams,
                  self._GetSizeParams,
                  ]
    return formatters

  def _Params(self, chart):
    """Collect all the different params we need for the URL.  Collecting
    all params as a dict before converting to a URL makes testing easier.
    """
    chart = chart.GetFormattedChart()
    params = {}
    def Add(new_params):
      params.update(_ShortenParameterNames(new_params))

    for formatter in self.formatters:
      Add(formatter(chart))

    for key in params:
      params[key] = str(params[key])
    return params

  def _GetSizeParams(self, chart):
    """Get the size param."""
    return {'size': '%sx%s' % (int(self._width), int(self._height))}

  def _GetExtraParams(self, chart):
    """Get any extra params (from extra_params)."""
    return self.extra_params

  def _GetDataSeriesParams(self, chart):
    """Collect params related to the data series."""
    y_min, y_max = chart.GetDependentAxis().min, chart.GetDependentAxis().max
    series_data = []
    colors = []
    styles = []
    markers = []
    for i, series in enumerate(chart.data):
      data = series.data
      if not data:  # Drop empty series.
        continue
      series_data.append(data)
      colors.append(series.color)
      style = series.style
      if style:
        styles.append('%s,%s,%s' % (style.width, style.on, style.off))
      else:
        # If one style is missing, they must all be missing
        # TODO: Add a test for this; throw a more meaningful exception
        assert (not styles)

      for x, marker in series.markers:
        args = [marker.shape, marker.color, i, x, marker.size]
        markers.append(','.join(str(arg) for arg in args))

    encoder = self._GetDataEncoder(chart)
    result = _EncodeData(chart, series_data, y_min, y_max, encoder)
    result.update(_JoinLists(color      = colors,
                             line_style = styles,
                             marker     = markers))
    return result

  def _GetDataEncoder(self, chart):
    """Get a class which can encode the data the way the user requested."""
    if not self.enhanced_encoding:
      return _SimpleDataEncoder()
    return _EnhancedDataEncoder()

  def _GetLegendParams(self, chart):
    """Get params for showing a legend."""
    if chart._show_legend:
      return _JoinLists(data_series_label = chart._legend_labels)
    return {}

  def _GetAxisLabelsAndPositions(self, axis, chart):
    """Return axis.labels & axis.label_positions."""
    return axis.labels, axis.label_positions

  def _GetAxisParams(self, chart):
    """Collect params related to our various axes (x, y, right-hand)."""
    axis_types = []
    axis_ranges = []
    axis_labels = []
    axis_label_positions = []
    axis_label_gridlines = []
    mark_length = max(self._width, self._height)
    for i, axis_pair in enumerate(a for a in chart._GetAxes() if a[1].labels):
      axis_type_code, axis = axis_pair
      axis_types.append(axis_type_code)
      if axis.min is not None or axis.max is not None:
        assert axis.min is not None  # Sanity check: both min & max must be set.
        assert axis.max is not None
        axis_ranges.append('%s,%s,%s' % (i, axis.min, axis.max))

      labels, positions = self._GetAxisLabelsAndPositions(axis, chart)
      if labels:
        axis_labels.append('%s:' % i)
        axis_labels.extend(labels)
      if positions:
        positions = [i] + list(positions)
        axis_label_positions.append(','.join(str(x) for x in positions))
      if axis.label_gridlines:
        axis_label_gridlines.append("%d,%d" % (i, -mark_length))

    return _JoinLists(axis_type       = axis_types,
                      axis_range      = axis_ranges,
                      axis_label      = axis_labels,
                      axis_position   = axis_label_positions,
                      axis_tick_marks = axis_label_gridlines,
                     )

  def _GetGridParams(self, chart):
    """Collect params related to grid lines."""
    x = 0
    y = 0
    if chart.bottom.grid_spacing:
      # min/max must be set for this to make sense.
      assert(chart.bottom.min is not None)
      assert(chart.bottom.max is not None)
      total = float(chart.bottom.max - chart.bottom.min)
      x = 100 * chart.bottom.grid_spacing / total
    if chart.left.grid_spacing:
      # min/max must be set for this to make sense.
      assert(chart.left.min is not None)
      assert(chart.left.max is not None)
      total = float(chart.left.max - chart.left.min)
      y = 100 * chart.left.grid_spacing / total
    if x or y:
      return dict(grid = '%.3g,%.3g,1,0' % (x, y))
    return {}


class LineChartEncoder(BaseChartEncoder):

  """Helper class to encode LineChart objects into Google Chart URLs."""

  def _GetType(self, chart):
    return {'chart_type': 'lc'}


class SparklineEncoder(BaseChartEncoder):

  """Helper class to encode Sparkline objects into Google Chart URLs."""

  def _GetType(self, chart):
    return {'chart_type': 'lfi'}


class BarChartEncoder(BaseChartEncoder):

  """Helper class to encode BarChart objects into Google Chart URLs.

  Object attributes:
    style: The BarStyle for all bars on this chart.
  """

  def __init__(self, chart, style=None):
    """Construct a new BarChartEncoder.

    Args:
      style: The BarStyle for all bars on this chart, if any.
    """
    super(BarChartEncoder, self).__init__(chart)
    self.style = style

  def _GetType(self, chart):
    #         Vertical Stacked Type
    types = {(True,    False): 'bvg',
             (True,    True):  'bvs',
             (False,   False): 'bhg',
             (False,   True):  'bhs'}
    return {'chart_type': types[(chart.vertical, chart.stacked)]}

  def _GetAxisLabelsAndPositions(self, axis, chart):
    """Reverse labels on the y-axis in horizontal bar charts.
    (Otherwise the labels come out backwards from what you would expect)
    """
    if not chart.vertical and axis == chart.left:
      # The left axis of horizontal bar charts needs to have reversed labels
      return reversed(axis.labels), reversed(axis.label_positions)
    return axis.labels, axis.label_positions

  def _GetFormatters(self):
    out = super(BarChartEncoder, self)._GetFormatters()
    out.append(self._ZeroPoint)
    out.append(self._ApplyBarStyle)
    return out

  def _ZeroPoint(self, chart):
    """Get the zero-point if any bars are negative."""
    # (Maybe) set the zero point.
    min, max = chart.GetDependentAxis().min, chart.GetDependentAxis().max
    out = {}
    if min < 0:
      if max < 0:
        out['chp'] = 1
      else:
        out['chp'] = -min/float(max - min)
    return out

  def _ApplyBarStyle(self, chart):
    """If bar style is specified, fill in the missing data and apply it."""
    # sanity checks
    if self.style is None or not chart.data:
      return {}
    if self.style.bar_thickness is None and \
       self.style.bar_gap is None and \
       self.style.group_gap is None:
      return {}
    # fill in missing values
    bar_gap = self.style.bar_gap
    group_gap = self.style.group_gap
    bar_thickness = self.style.bar_thickness
    if bar_gap is None and group_gap is not None:
      bar_gap = max(0, group_gap // 2)
    if group_gap is None and bar_gap is not None:
      group_gap = int(bar_gap * 2)
    if bar_thickness is None:
      if chart.vertical:
        space = self._width
      else:
        space = self._height
      assert(space is not None)
      if chart.stacked:
        num_bars = max(len(series.data) for series in chart.data)
        bar_thickness = (space - bar_gap * (num_bars - 1)) // num_bars
      else:
        num_bars = sum(len(series.data) for series in chart.data)
        num_groups = len(chart.data)
        space_left = (space - bar_gap * (num_bars - num_groups) -
                      group_gap * (num_groups - 1))
        bar_thickness = space_left // num_bars
      bar_thickness = max(1, bar_thickness)
    # format the values
    spec = [bar_thickness]
    if bar_gap is not None:
      spec.append(bar_gap)
      if group_gap is not None and not chart.stacked:
        spec.append(group_gap)
    return _JoinLists(bar_height = spec)


class PieChartEncoder(BaseChartEncoder):
  """Helper class for encoding PieChart objects into Google Chart URLs.

  Object Attributes:
    is3d: if True, draw a 3d pie chart. Default is False.
  """

  def __init__(self, chart, is3d=False):
    """Construct a new PieChartEncoder.

    Args:
      is3d: if True, draw a 3d pie chart. Default is False.
    """
    super(PieChartEncoder, self).__init__(chart)
    self.is3d = is3d

  def _GetType(self, chart):
    if self.is3d:
      return {'chart_type': 'p3'}
    else:
      return {'chart_type': 'p'}

  def _GetDataSeriesParams(self, chart):
    """Collect params related to the data series."""
    points = []
    labels = []
    colors = []
    for segment in chart.data:
      if segment:
        points.append(segment.size)
        labels.append(segment.label or '_')
        if segment.color:
          colors.append(segment.color)

    if points:
      max_val = max(points)
    else:
      max_val = 1
    encoder = self._GetDataEncoder(chart)
    result = _EncodeData(chart, [points], 0, max_val, encoder)
    result.update(_JoinLists(color=colors, label=labels))
    return result


class _SimpleDataEncoder:

  """Encode data using simple encoding.  Out-of-range data will
  be dropped (encoded as '_').
  """

  # TODO: merge this with the cs_client implementation.
  def __init__(self):
    self.prefix = 's:'
    self.code = string.ascii_uppercase + string.ascii_lowercase + string.digits
    self.min = 0
    self.max = len(self.code) - 1

  def Encode(self, data):
    return ''.join(self._EncodeItem(i) for i in data)

  def _EncodeItem(self, x):
    if x is None:
      return '_'
    x = int(round(x))
    if x < self.min or x > self.max:
      return '_'
    return self.code[int(x)]


class _EnhancedDataEncoder:

  """Encode data using enhanced encoding.  Out-of-range data will
  be dropped (encoded as '_').
  """

  def __init__(self):
    self.prefix = 'e:'
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits \
            + '-.'
    self.code = [x + y for x in chars for y in chars]
    self.min = 0
    self.max = len(self.code) - 1

  def Encode(self, data):
    return ''.join(self._EncodeItem(i) for i in data)

  def _EncodeItem(self, x):
    if x is None:
      return '__'
    x = int(round(x))
    if x < self.min or x > self.max:
      return '__'
    return self.code[int(x)]


def _EncodeUrl(base, params, escape_url):
  """Escape params, combine and append them to base to generate a full URL."""
  real_params = []
  for key, value in params.iteritems():
    if escape_url:
      value = urllib.quote(value)
    if value:
      real_params.append('%s=%s' % (key, value))
  if real_params:
    return '%s?%s' % (base, '&'.join(real_params))
  else:
    return base


def _ShortenParameterNames(params):
  """Shorten long parameter names (like size) to short names (like chs)."""
  out = {}
  for name, value in params.iteritems():
    short_name = _LONG_NAMES.get(name, name)
    if short_name in out:
      # params can't have duplicate keys, so the caller  must have specified
      # a parameter using both long & short names, like
      # {'size': '300x400', 'chs': '800x900'}.  We don't know which to use.
      raise KeyError('Both long and short version of parameter %s (%s) '
        'found.  It is unclear which one to use.' % (name, short_name))
    out[short_name] = value
  return out


def _StrJoin(delim, data):
  """String-ize & join data."""
  return delim.join(str(x) for x in data)


def _JoinLists(**args):
  """Take a dictionary of {long_name:values}, and join the values.

    For each long_name, join the values into a string according to
    _JOIN_DELIMS.  If values is empty or None, replace with an empty string.

    Returns:
      A dictionary {long_name:joined_value} entries.
  """
  out = {}
  for key, val in args.items():
    if val:
      out[key] = _StrJoin(_JOIN_DELIMS[key], val)
    else:
      out[key] = ''
  return out


def _EncodeData(chart, series, y_min, y_max, encoder):
  """Format the given data series in plain or extended format.

  Use the chart's encoder to determine the format. The formatted data will
  be scaled to fit within the range of values supported by the chosen
  encoding.

  Args:
    chart: The chart.
    series: A list of the the data series to format; each list element is
           a list of data points.
    y_min: Minimum data value. May be None if y_max is also None
    y_max: Maximum data value. May be None if y_min is also None
  Returns:
    A dictionary with one key, 'data', whose value is the fully encoded series.
  """
  assert (y_min is None) == (y_max is None)
  if y_min is not None:
    def _ScaleAndEncode(series):
      series = _ScaleData(series, y_min, y_max, encoder.min, encoder.max)
      return encoder.Encode(series)
    encoded_series = [_ScaleAndEncode(s) for s in series]
  else:
    encoded_series = [encoder.Encode(s) for s in series]
  result = _JoinLists(**{'data': encoded_series})
  result['data'] = encoder.prefix + result['data']
  return result


def _ScaleData(data, old_min, old_max, new_min, new_max):
  """Scale the input data so that the range old_min-old_max maps to
  new_min-new_max.
  """
  def ScalePoint(x):
    if x is None:
      return None
    return scale * x + translate

  if old_min == old_max:
    scale = 1
  else:
    scale = (new_max - new_min) / float(old_max - old_min)
  translate = new_min - scale * old_min
  return map(ScalePoint, data)


def _GetChartFactory(chart_class, display_class):
  """Create a factory method for instantiating charts with displays.

  Returns a method which, when called, will create & return a chart with
  chart.display already populated.
  """
  def Inner(*args, **kwargs):
    chart = chart_class(*args, **kwargs)
    chart.display = display_class(chart)
    return chart
  return Inner

# These helper methods make it easy to get chart objects with display
# objects already setup.  For example, this:
#   chart = google_chart_api.LineChart()
# is equivalent to:
#   chart = line_chart.LineChart()
#   chart.display = google_chart_api.LineChartEncoder()
#
# (If there's some chart type for which a helper method isn't available, you
# can always just instantiate the correct encoder manually, like in the 2nd
# example above).
LineChart = _GetChartFactory(line_chart.LineChart, LineChartEncoder)
Sparkline = _GetChartFactory(line_chart.Sparkline, SparklineEncoder)
BarChart  = _GetChartFactory(bar_chart.BarChart, BarChartEncoder)
PieChart  = _GetChartFactory(pie_chart.PieChart, PieChartEncoder)
