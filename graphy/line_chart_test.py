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

"""Tests for line_chart.py."""

from graphy import line_chart
from graphy import graphy_test


class LineStyleTest(graphy_test.GraphyTest):

  def testPresets(self):
    """Test selected traits from the preset line styles."""
    self.assertEqual(0, line_chart.LineStyle.solid.off)
    self.assert_(line_chart.LineStyle.dashed.off > 0)
    self.assert_(line_chart.LineStyle.solid.width <
                 line_chart.LineStyle.thick_solid.width)


