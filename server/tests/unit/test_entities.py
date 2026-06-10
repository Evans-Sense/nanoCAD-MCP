from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.entities import (
    CadArc,
    CadCircle,
    CadColor,
    CadLayer,
    CadLine,
    CadPolyline,
    CadText,
    EntityHandle,
    LayerName,
    Point2D,
)


class TestPoint2D:
    def test_create(self) -> None:
        p = Point2D(x=1.0, y=2.0)
        assert p.x == 1.0
        assert p.y == 2.0
        assert p.as_tuple() == (1.0, 2.0)

    def test_iter(self) -> None:
        p = Point2D(x=1.0, y=2.0)
        xs, ys = list(p)
        assert xs == 1.0
        assert ys == 2.0

    def test_frozen(self) -> None:
        Point2D(x=1.0, y=2.0)
        with pytest.raises(ValidationError):
            Point2D(x="not_a_number", y=2.0)  # type: ignore[arg-type]


class TestCadColor:
    def test_by_index(self) -> None:
        c = CadColor.by_index(7)
        assert c.color_index == 7

    def test_by_rgb(self) -> None:
        c = CadColor.by_rgb(255, 0, 0)
        assert c.red == 255
        assert c.green == 0
        assert c.blue == 0
        assert c.color_index is None

    def test_by_layer(self) -> None:
        c = CadColor.by_layer()
        assert c.color_index == 256

    def test_invalid_rgb(self) -> None:
        with pytest.raises(ValidationError):
            CadColor.by_rgb(300, 0, 0)

    def test_invalid_index(self) -> None:
        with pytest.raises(ValidationError):
            CadColor.by_index(999)


class TestCadLine:
    def test_create(self) -> None:
        line = CadLine(
            start=Point2D(x=0.0, y=0.0),
            end=Point2D(x=10.0, y=10.0),
        )
        assert line.entity_type == "LINE"
        assert line.start.x == 0.0
        assert line.end.y == 10.0
        assert str(line.layer) == "0"

    def test_with_handle(self) -> None:
        line = CadLine(
            start=Point2D(x=0.0, y=0.0),
            end=Point2D(x=10.0, y=10.0),
            handle=EntityHandle(value="ABC123"),
        )
        assert str(line.handle) == "ABC123"  # type: ignore[union-attr]


class TestCadCircle:
    def test_create(self) -> None:
        circle = CadCircle(
            center=Point2D(x=5.0, y=5.0),
            radius=10.0,
        )
        assert circle.entity_type == "CIRCLE"
        assert circle.radius == 10.0

    def test_zero_radius(self) -> None:
        with pytest.raises(ValidationError):
            CadCircle(center=Point2D(x=0.0, y=0.0), radius=0.0)

    def test_negative_radius(self) -> None:
        with pytest.raises(ValidationError):
            CadCircle(center=Point2D(x=0.0, y=0.0), radius=-1.0)


class TestCadArc:
    def test_create(self) -> None:
        arc = CadArc(
            center=Point2D(x=0.0, y=0.0),
            radius=5.0,
            start_angle=0.0,
            end_angle=180.0,
        )
        assert arc.entity_type == "ARC"
        assert arc.start_angle == 0.0
        assert arc.end_angle == 180.0


class TestCadPolyline:
    def test_create(self) -> None:
        poly = CadPolyline(
            vertices=[
                Point2D(x=0.0, y=0.0),
                Point2D(x=10.0, y=0.0),
                Point2D(x=10.0, y=10.0),
            ],
            closed=True,
        )
        assert poly.entity_type == "POLYLINE"
        assert len(poly.vertices) == 3
        assert poly.closed is True

    def test_min_vertices(self) -> None:
        with pytest.raises(ValidationError):
            CadPolyline(vertices=[Point2D(x=0.0, y=0.0)])


class TestCadText:
    def test_create(self) -> None:
        text = CadText(
            insertion=Point2D(x=1.0, y=1.0),
            content="Hello",
            height=2.5,
        )
        assert text.entity_type == "TEXT"
        assert text.content == "Hello"
        assert text.height == 2.5


class TestCadLayer:
    def test_defaults(self) -> None:
        layer = CadLayer(name=LayerName(value="TestLayer"))
        assert str(layer.name) == "TestLayer"
        assert layer.is_on is True
        assert layer.is_frozen is False

    def test_custom(self) -> None:
        layer = CadLayer(
            name=LayerName(value="Hidden"),
            is_on=False,
            is_frozen=True,
            is_locked=True,
        )
        assert layer.is_on is False
        assert layer.is_frozen is True
        assert layer.is_locked is True


class TestLayerName:
    def test_valid(self) -> None:
        ln = LayerName(value="0")
        assert str(ln) == "0"

    def test_empty(self) -> None:
        with pytest.raises(ValidationError):
            LayerName(value="")

    def test_long(self) -> None:
        with pytest.raises(ValidationError):
            LayerName(value="a" * 257)


class TestEntityHandle:
    def test_str(self) -> None:
        h = EntityHandle(value="ABC-123")
        assert str(h) == "ABC-123"
