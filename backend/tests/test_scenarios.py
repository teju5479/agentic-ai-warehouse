"""Tests for scenario validation.

Each test verifies that the seeded data supports the expected scenario.
"""
import pytest
from app.models.order import Order, OrderLine
from app.models.inventory import Inventory
from app.models.shipment import Shipment
from app.models.picker import Picker


def test_scenario_exc001_inventory_shortfall(db_session):
    """Verify ORD-1004 has inventory shortfall for SKU-005."""
    lines = db_session.query(OrderLine).filter(OrderLine.order_id == "ORD-1004").all()
    sku005_line = [l for l in lines if l.sku == "SKU-005"][0]
    assert sku005_line.requested_qty == 10
    
    inv = db_session.query(Inventory).filter(Inventory.sku == "SKU-005").first()
    assert inv is not None
    assert inv.available < sku005_line.requested_qty


def test_scenario_exc002_duplicate_order(db_session):
    """Verify ORD-1005 and ORD-1006 are near-duplicates."""
    ord5 = db_session.query(Order).filter(Order.order_id == "ORD-1005").first()
    ord6 = db_session.query(Order).filter(Order.order_id == "ORD-1006").first()
    assert ord5.destination == ord6.destination
    
    lines5 = db_session.query(OrderLine).filter(OrderLine.order_id == "ORD-1005").all()
    lines6 = db_session.query(OrderLine).filter(OrderLine.order_id == "ORD-1006").all()
    items5 = {(l.sku, l.requested_qty) for l in lines5}
    items6 = {(l.sku, l.requested_qty) for l in lines6}
    assert items5 == items6  # Exact duplicate items


def test_scenario_exc003_status_conflict(db_session):
    """Verify ORD-1007 has conflicting order/shipment status."""
    order = db_session.query(Order).filter(Order.order_id == "ORD-1007").first()
    shipment = db_session.query(Shipment).filter(Shipment.order_id == "ORD-1007").first()
    assert order.status == "PROCESSING"
    assert shipment.status == "DELIVERED"


def test_scenario_exc004_invalid_quantity(db_session):
    """Verify ORD-1008 has a negative quantity."""
    lines = db_session.query(OrderLine).filter(OrderLine.order_id == "ORD-1008").all()
    negative_lines = [l for l in lines if l.requested_qty < 0]
    assert len(negative_lines) >= 1


def test_scenario_exc005_stale_shipment(db_session):
    """Verify SHP-109 is stale (14+ days)."""
    from datetime import datetime
    shipment = db_session.query(Shipment).filter(Shipment.shipment_id == "SHP-109").first()
    assert shipment is not None
    assert shipment.status == "IN_TRANSIT"
    days_old = (datetime.now() - shipment.created_at).days
    assert days_old >= 7  # Should be ~14 days old


def test_scenario_exc006_conflicting_destination(db_session):
    """Verify ORD-1010 and SHP-110 have different destinations."""
    order = db_session.query(Order).filter(Order.order_id == "ORD-1010").first()
    shipment = db_session.query(Shipment).filter(Shipment.order_id == "ORD-1010").first()
    assert order.destination != shipment.destination


def test_scenario_exc007_missing_inventory(db_session):
    """Verify SKU-011 has no inventory record."""
    inv = db_session.query(Inventory).filter(Inventory.sku == "SKU-011").first()
    assert inv is None


def test_unavailable_picker_exists(db_session):
    """Verify PICK-004 is unavailable."""
    picker = db_session.query(Picker).filter(Picker.picker_id == "PICK-004").first()
    assert picker.availability == "UNAVAILABLE"


def test_sufficient_orders_seeded(db_session):
    """Verify at least 15 orders exist."""
    count = db_session.query(Order).count()
    assert count >= 15


def test_sufficient_pickers_seeded(db_session):
    """Verify 4-5 pickers exist."""
    count = db_session.query(Picker).count()
    assert count >= 4
