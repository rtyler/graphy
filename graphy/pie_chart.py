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

"""Code for pie charts."""

import warnings

from graphy import common
from graphy import util


class Segment(common.DataSeries):
  """A single segment of the pie chart.

  Object attributes:
    size: relative size of the segment
    label: label of the segment (if any)
    color: color of the segment (if any)
  """
  def __init__(self, size, label=None, color=None):
    if label is not None and util._IsColor(label):
      warnings.warn('Your code may be broken! '
                    'Label looks like a hex triplet; it might be a color.  '
                    'The old argument order (color before label) is '
                    'deprecated.',
                    DeprecationWarning, stacklevel=2)
    style = common._BasicStyle(color)
    super(Segment, self).__init__([size], label=label, style=style)
    assert size >= 0

  def _GetSize(self):
    return self.data[0]

  def _SetSize(self, value):
    assert value >= 0
    self.data[0] = value

  size = property(_GetSize, _SetSize,
                  doc = """The relative size of this pie segment.""")

  # Since Segments are so simple, provide color for convenience.
  def _GetColor(self):
    return self.style.color

  def _SetColor(self, color):
    self.style.color = color

  color = property(_GetColor, _SetColor,
                   doc = """The color of this pie segment.""")


class PieChart(common.BaseChart):
  """Represent a pie chart."""

  def __init__(self, points=None, labels=None, colors=None):
    """Constructor for PieChart objects

    Args:
      data_points: A list of data points for the pie chart;
              i.e., relative sizes of the pie segments
      labels: A list of labels for the pie segments.
              TODO: Allow the user to pass in None as one of
              the labels in order to skip that label.
      colors: A list of colors for the pie segments, as hex strings
              (f.ex. '0000ff' for blue). Missing colors will be
              automatically interpolated by the server.
    """
    super(PieChart, self).__init__()
    self.formatters = []
    if points:
      # BUG: This crashes if you specify points but not labels
      self.AddSegments(points, labels, colors)

  def AddSegments(self, points, labels, colors):
    """Add more segments to this pie chart."""
    num_colors = len(colors or [])
    for i, pt in enumerate(points):
      assert pt >= 0
      label = labels[i]
      color = None
      if i < num_colors:
        color = colors[i]
      self.AddSegment(pt, label=label, color=color)

  def AddSegment(self, size, label=None, color=None):
    """Add a pie segment to this chart, and return the segment."""
    if isinstance(size, Segment):
      warnings.warn("AddSegment(segment) is deprecated.  Use AddSegment(size, "
                    "label, color) instead",  DeprecationWarning, stacklevel=2)
      segment = size
    else:
      segment = Segment(size, label=label, color=color)
    assert segment.size >= 0
    self.data.append(segment)
    return segment

  def AddSeries(self, points, color=None, style=None, markers=None, label=None):
    """DEPRECATED

    Add a new segment to the chart and return it.

    The segment must contain exactly one data point; all parameters
    other than color and label are ignored.
    """
    warnings.warn('PieChart.AddSeries is deprecated.  Call AddSegment or '
                  'AddSegments instead.', DeprecationWarning)
    return self.AddSegment(Segment(points[0], color, label))

  def SetColors(self, *colors):
    """Change the colors of this chart to the specified list of colors.

    Missing colors will be interpolated by the server.
    """
    num_colors = len(colors)
    assert num_colors <= len(self.data)
    for i,segment in enumerate(self.data):
      if i >= num_colors:
        segment.color = None
      else:
        segment.color = colors[i]
