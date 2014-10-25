# (C) British Crown Copyright 2014, Met Office
#
# This file is part of Iris.
#
# Iris is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Iris is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Iris.  If not, see <http://www.gnu.org/licenses/>.
"""
Unit tests for the
`iris.aux_factory.HybridPressureFactory` class.

"""

from __future__ import (absolute_import, division, print_function)

# Import iris.tests first so that some things can be initialised before
# importing anything else.
import iris.tests as tests

import mock

import numpy as np

import iris
from iris.aux_factory import HybridPressureFactory


class Test___init__(tests.IrisTest):
    def setUp(self):
        self.delta = mock.Mock(units=iris.unit.Unit('Pa'), nbounds=0)
        self.sigma = mock.Mock(units=iris.unit.Unit('1'), nbounds=0)
        self.surface_air_pressure = mock.Mock(units=iris.unit.Unit('Pa'),
                                              nbounds=0)

    def test_insufficient_coords(self):
        with self.assertRaises(ValueError):
            HybridPressureFactory()
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=None, sigma=self.sigma,
                surface_air_pressure=None)
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=None, sigma=None,
                surface_air_pressure=self.surface_air_pressure)

    def test_incompatible_delta_units(self):
        self.delta.units = iris.unit.Unit('m')
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=self.delta, sigma=self.sigma,
                surface_air_pressure=self.surface_air_pressure)

    def test_incompatible_sigma_units(self):
        self.sigma.units = iris.unit.Unit('Pa')
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=self.delta, sigma=self.sigma,
                surface_air_pressure=self.surface_air_pressure)

    def test_incompatible_surface_air_pressure_units(self):
        self.surface_air_pressure.units = iris.unit.Unit('unknown')
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=self.delta, sigma=self.sigma,
                surface_air_pressure=self.surface_air_pressure)

    def test_different_pressure_units(self):
        self.delta.units = iris.unit.Unit('hPa')
        self.surface_air_pressure.units = iris.unit.Unit('Pa')
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=self.delta, sigma=self.sigma,
                surface_air_pressure=self.surface_air_pressure)

    def test_too_many_delta_bounds(self):
        self.delta.nbounds = 4
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=self.delta, sigma=self.sigma,
                surface_air_pressure=self.surface_air_pressure)

    def test_too_many_sigma_bounds(self):
        self.sigma.nbounds = 4
        with self.assertRaises(ValueError):
            HybridPressureFactory(
                delta=self.delta, sigma=self.sigma,
                surface_air_pressure=self.surface_air_pressure)

    def test_factory_metadata(self):
        factory = HybridPressureFactory(
            delta=self.delta, sigma=self.sigma,
            surface_air_pressure=self.surface_air_pressure)
        self.assertEqual(factory.standard_name, 'air_pressure')
        self.assertIsNone(factory.long_name)
        self.assertIsNone(factory.var_name)
        self.assertEqual(factory.units, self.delta.units)
        self.assertEqual(factory.units, self.surface_air_pressure.units)
        self.assertIsNone(factory.coord_system)
        self.assertEqual(factory.attributes, {})


class Test_dependencies(tests.IrisTest):
    def setUp(self):
        self.delta = mock.Mock(units=iris.unit.Unit('Pa'), nbounds=0)
        self.sigma = mock.Mock(units=iris.unit.Unit('1'), nbounds=0)
        self.surface_air_pressure = mock.Mock(units=iris.unit.Unit('Pa'),
                                              nbounds=0)

    def test_value(self):
        kwargs = dict(delta=self.delta,
                      sigma=self.sigma,
                      surface_air_pressure=self.surface_air_pressure)
        factory = HybridPressureFactory(**kwargs)
        self.assertEqual(factory.dependencies, kwargs)


class Test_make_coord(tests.IrisTest):
    @staticmethod
    def coords_dims_func(coord):
        mapping = dict(level_pressure=(0,), sigma=(0,),
                       surface_air_pressure=(1, 2))
        return mapping[coord.name()]

    def setUp(self):
        self.delta = iris.coords.DimCoord(
            [0.0, 1.0, 2.0], long_name='level_pressure', units='Pa')
        self.sigma = iris.coords.DimCoord(
            [1.0, 0.9, 0.8], long_name='sigma')
        self.surface_air_pressure = iris.coords.AuxCoord(
            np.arange(4).reshape(2, 2), 'surface_air_pressure',
            units='Pa')

    def test_points_only(self):
        # Determine expected coord by manually broadcasting coord points
        # knowing the dimension mapping.
        delta_pts = self.delta.points[..., np.newaxis, np.newaxis]
        sigma_pts = self.sigma.points[..., np.newaxis, np.newaxis]
        surf_pts = self.surface_air_pressure.points[np.newaxis, ...]
        expected_points = delta_pts + sigma_pts * surf_pts
        expected_coord = iris.coords.AuxCoord(expected_points,
                                              standard_name='air_pressure',
                                              units='Pa')
        factory = HybridPressureFactory(
            delta=self.delta, sigma=self.sigma,
            surface_air_pressure=self.surface_air_pressure)
        derived_coord = factory.make_coord(self.coords_dims_func)
        self.assertEqual(expected_coord, derived_coord)

    def test_none_delta(self):
        delta_pts = 0
        sigma_pts = self.sigma.points[..., np.newaxis, np.newaxis]
        surf_pts = self.surface_air_pressure.points[np.newaxis, ...]
        expected_points = delta_pts + sigma_pts * surf_pts
        expected_coord = iris.coords.AuxCoord(expected_points,
                                              standard_name='air_pressure',
                                              units='Pa')
        factory = HybridPressureFactory(
            sigma=self.sigma, surface_air_pressure=self.surface_air_pressure)
        derived_coord = factory.make_coord(self.coords_dims_func)
        self.assertEqual(expected_coord, derived_coord)

    def test_none_sigma(self):
        delta_pts = self.delta.points[..., np.newaxis, np.newaxis]
        sigma_pts = 0
        surf_pts = self.surface_air_pressure.points[np.newaxis, ...]
        expected_points = delta_pts + sigma_pts * surf_pts
        expected_coord = iris.coords.AuxCoord(expected_points,
                                              standard_name='air_pressure',
                                              units='Pa')
        factory = HybridPressureFactory(
            delta=self.delta, surface_air_pressure=self.surface_air_pressure)
        derived_coord = factory.make_coord(self.coords_dims_func)
        self.assertEqual(expected_coord, derived_coord)

    def test_none_surface_air_pressure(self):
        # Note absence of broadcasting as multidimensional coord
        # is not present.
        expected_points = self.delta.points
        expected_coord = iris.coords.AuxCoord(expected_points,
                                              standard_name='air_pressure',
                                              units='Pa')
        factory = HybridPressureFactory(delta=self.delta, sigma=self.sigma)
        derived_coord = factory.make_coord(self.coords_dims_func)
        self.assertEqual(expected_coord, derived_coord)

    def test_with_bounds(self):
        self.delta.guess_bounds(0)
        self.sigma.guess_bounds(0.5)
        # Determine expected coord by manually broadcasting coord points
        # and bounds based on the dimension mapping.
        delta_pts = self.delta.points[..., np.newaxis, np.newaxis]
        sigma_pts = self.sigma.points[..., np.newaxis, np.newaxis]
        surf_pts = self.surface_air_pressure.points[np.newaxis, ...]
        expected_points = delta_pts + sigma_pts * surf_pts
        delta_vals = self.delta.bounds.reshape(3, 1, 1, 2)
        sigma_vals = self.sigma.bounds.reshape(3, 1, 1, 2)
        surf_vals = self.surface_air_pressure.points.reshape(1, 2, 2, 1)
        expected_bounds = delta_vals + sigma_vals * surf_vals
        expected_coord = iris.coords.AuxCoord(expected_points,
                                              standard_name='air_pressure',
                                              units='Pa',
                                              bounds=expected_bounds)
        factory = HybridPressureFactory(
            delta=self.delta, sigma=self.sigma,
            surface_air_pressure=self.surface_air_pressure)
        derived_coord = factory.make_coord(self.coords_dims_func)
        self.assertEqual(expected_coord, derived_coord)


class Test_update(tests.IrisTest):
    def setUp(self):
        self.delta = mock.Mock(units=iris.unit.Unit('Pa'), nbounds=0)
        self.sigma = mock.Mock(units=iris.unit.Unit('1'), nbounds=0)
        self.surface_air_pressure = mock.Mock(units=iris.unit.Unit('Pa'),
                                              nbounds=0)

        self.factory = HybridPressureFactory(
            delta=self.delta, sigma=self.sigma,
            surface_air_pressure=self.surface_air_pressure)

    def test_good_delta(self):
        new_delta_coord = mock.Mock(units=iris.unit.Unit('Pa'), nbounds=0)
        self.factory.update(self.delta, new_delta_coord)
        self.assertIs(self.factory.delta, new_delta_coord)

    def test_bad_delta(self):
        new_delta_coord = mock.Mock(units=iris.unit.Unit('1'), nbounds=0)
        with self.assertRaises(ValueError):
            self.factory.update(self.delta, new_delta_coord)

    def test_alternative_bad_delta(self):
        new_delta_coord = mock.Mock(units=iris.unit.Unit('Pa'), nbounds=4)
        with self.assertRaises(ValueError):
            self.factory.update(self.delta, new_delta_coord)

    def test_good_surface_air_pressure(self):
        new_surface_p_coord = mock.Mock(units=iris.unit.Unit('Pa'), nbounds=0)
        self.factory.update(self.surface_air_pressure, new_surface_p_coord)
        self.assertIs(self.factory.surface_air_pressure, new_surface_p_coord)

    def test_bad_surface_air_pressure(self):
        new_surface_p_coord = mock.Mock(units=iris.unit.Unit('km'), nbounds=0)
        with self.assertRaises(ValueError):
            self.factory.update(self.surface_air_pressure, new_surface_p_coord)

    def test_non_dependency(self):
        old_coord = mock.Mock()
        new_coord = mock.Mock()
        orig_dependencies = self.factory.dependencies
        self.factory.update(old_coord, new_coord)
        self.assertEqual(orig_dependencies, self.factory.dependencies)

    def test_none_delta(self):
        self.factory.update(self.delta, None)
        self.assertIsNone(self.factory.delta)

    def test_none_sigma(self):
        self.factory.update(self.sigma, None)
        self.assertIsNone(self.factory.sigma)

    def test_insufficient_coords(self):
        self.factory.update(self.delta, None)
        with self.assertRaises(ValueError):
            self.factory.update(self.surface_air_pressure, None)


if __name__ == "__main__":
    tests.main()
