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

"""Code related to bar charts."""

import copy
import warnings

from graphy import common
from graphy import util


class BarStyle(object):
  """Represents the style for bars on a BarChart.

  Any of the object attributes may be set to None, in which case the
  value will be auto-calculated.

  Object Attributes:
    bar_thickness: The thickness of a bar, in pixels.
    bar_gap: The gap between bars, in pixels.
    group_gap: The gap between groups of bars, in pixels.
  """

  _DEFAULT_GROUP_GAP = 8
  _DEFAULT_BAR_GAP = 4

  def __init__(self, bar_thickness=None,
               bar_gap=_DEFAULT_BAR_GAP, group_gap=_DEFAULT_GROUP_GAP):
    """Create a new BarStyle.

    Args:
     bar_thickness: The thickness of a bar, in pixels. Set this to None if
       you want the bar thickness to be auto-calculated (this is the default
       behaviour).
     bar_gap: The gap between bars, in pixels. Default is 4.
     group_gap: The gap between groups of bars, in pixels. Default is 8.
    """
    self.bar_thickness = bar_thickness
    self.bar_gap = bar_gap
    self.group_gap = group_gap


class BarChart(common.BaseChart):
  """Represents a bar chart.

  Object attributes:
    vertical: if True, the bars will be vertical. Default is True.
    stacked: if True, the bars will be stacked. Default is False.
    style: The BarStyle for all bars on this chart, specifying bar
      thickness and gaps between bars.
  """

  def __init__(self, points=None):
    """Constructor for BarChart objects."""
    super(BarChart, self).__init__()
    if points is not None:
      self.AddBars(points)
    self.vertical = True
    self.stacked = False
    self.style = BarStyle(None, None, None) # full auto 

  def AddBars(self, points, label=None, color=None):
    """Add a series of bars to the chart.

      points: List of y-values for the bars in this series
      label:  Name of the series (used in the legend)
      color:  Hex string, like '00ff00' for green

    This is a convenience method which constructs & appends the DataSeries for
    you.
    """
    if label is not None and util._IsColor(label):
      warnings.warn('Your code may be broken! '
                    'Label is a hex triplet.  Maybe it is a color? The '
                    'old argument order (color before label) is deprecated.',
                    DeprecationWarning, stacklevel=2)
    series = common.DataSeries(points, label=label, color=color, style=None)
    self.data.append(series)
    return series
  
  def GetDependentAxes(self):
    """Get the dependendant axes, which depend on orientation."""
    if self.vertical:
      return (self._axes[common.AxisPosition.LEFT] + 
              self._axes[common.AxisPosition.RIGHT])
    else:
      return (self._axes[common.AxisPosition.TOP] +
              self._axes[common.AxisPosition.BOTTOM])
  
  def GetIndependentAxes(self):
    """Get the independendant axes, which depend on orientation."""
    if self.vertical:
      return (self._axes[common.AxisPosition.TOP] +
              self._axes[common.AxisPosition.BOTTOM])
    else:
      return (self._axes[common.AxisPosition.LEFT] + 
              self._axes[common.AxisPosition.RIGHT])

  def GetDependentAxis(self):
    """Get the main dependendant axis, which depends on orientation."""
    if self.vertical:
      return self.left
    else:
      return self.bottom

  def GetIndependentAxis(self):
    """Get the main independendant axis, which depends on orientation."""
    if self.vertical:
      return self.bottom
    else:
      return self.left

  def GetMinMaxValues(self):
    """Get the largest & smallest bar values as (min_value, max_value)."""
    if not self.stacked:
      return super(BarChart, self).GetMinMaxValues()

    if not self.data:
      return None, None  # No data, nothing to do.
    num_bars = max(len(series.data) for series in self.data)
    positives = [0 for i in xrange(0, num_bars)]
    negatives = list(positives)
    for series in self.data:
      for i, point in enumerate(series.data):
        if point:
          if point > 0:
            positives[i] += point
          else:
            negatives[i] += point
    min_value = min(min(positives), min(negatives))
    max_value = max(max(positives), max(negatives))
    return min_value, max_value
