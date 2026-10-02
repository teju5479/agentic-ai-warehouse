import json
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
import os

from app.models.database import Base, engine
from app.models import Order, OrderLine, Inventory, Shipment, Picker, Policy

def load_json_data(filename: str):
    file_path = Path(__file__).parent / filename
    with open(file_path, "r") as f:
        return json.load(f)

def seed_database(session: Session):
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    now = datetime.now()
    
    # 1. Seed Policies
    policies_data = load_json_data("policies.json")
    for pol_data in policies_data:
        policy = Policy(**pol_data)
        session.add(policy)
        
    # 2. Seed Pickers
    pickers = [
        Picker(picker_id="PICK-001", name="Alice Johnson", availability="AVAILABLE", capacity=20, current_workload=5, location="ZONE-A", skills=json.dumps(["fragile", "heavy", "standard"])),
        Picker(picker_id="PICK-002", name="Bob Smith", availability="AVAILABLE", capacity=15, current_workload=3, location="ZONE-B", skills=json.dumps(["standard", "refrigerated"])),
        Picker(picker_id="PICK-003", name="Carol Davis", availability="AVAILABLE", capacity=18, current_workload=8, location="ZONE-A", skills=json.dumps(["fragile", "standard"])),
        Picker(picker_id="PICK-004", name="Dave Wilson", availability="UNAVAILABLE", capacity=20, current_workload=0, location="ZONE-C", skills=json.dumps(["heavy", "standard", "hazmat"])),
        Picker(picker_id="PICK-005", name="Eve Martinez", availability="AVAILABLE", capacity=12, current_workload=2, location="ZONE-B", skills=json.dumps(["standard", "refrigerated", "fragile"])),
    ]
    for p in pickers:
        session.add(p)

    # 3. Seed Inventory
    inventories = [
        Inventory(sku="SKU-001", location_id="LOC-A1", on_hand=50, reserved=10, available=40),
        Inventory(sku="SKU-002", location_id="LOC-A2", on_hand=30, reserved=5, available=25),
        Inventory(sku="SKU-003", location_id="LOC-B1", on_hand=20, reserved=3, available=17),
        Inventory(sku="SKU-004", location_id="LOC-B2", on_hand=15, reserved=2, available=13),
        Inventory(sku="SKU-005", location_id="LOC-C1", on_hand=8, reserved=2, available=6),
        Inventory(sku="SKU-006", location_id="LOC-C2", on_hand=25, reserved=4, available=21),
        Inventory(sku="SKU-007", location_id="LOC-D1", on_hand=18, reserved=0, available=18),
        Inventory(sku="SKU-008", location_id="LOC-D2", on_hand=12, reserved=1, available=11),
        Inventory(sku="SKU-009", location_id="LOC-E1", on_hand=22, reserved=5, available=17),
        Inventory(sku="SKU-010", location_id="LOC-E2", on_hand=10, reserved=2, available=8),
        Inventory(sku="SKU-012", location_id="LOC-F2", on_hand=35, reserved=0, available=35),
    ]
    for inv in inventories:
        session.add(inv)

    # 4. Seed Orders
    orders_data = [
        {"order_id": "ORD-1001", "status": "PENDING", "priority": "HIGH", "deadline": now + timedelta(hours=2), "destination": "DEST-NYC"},
        {"order_id": "ORD-1002", "status": "PENDING", "priority": "MEDIUM", "deadline": now + timedelta(hours=4), "destination": "DEST-LA"},
        {"order_id": "ORD-1003", "status": "PENDING", "priority": "LOW", "deadline": now + timedelta(hours=8), "destination": "DEST-CHICAGO"},
        {"order_id": "ORD-1004", "status": "PENDING", "priority": "HIGH", "deadline": now + timedelta(hours=3), "destination": "DEST-HOUSTON"},
        {"order_id": "ORD-1005", "status": "PENDING", "priority": "MEDIUM", "deadline": now + timedelta(hours=5), "destination": "DEST-PHOENIX"},
        {"order_id": "ORD-1006", "status": "PENDING", "priority": "MEDIUM", "deadline": now + timedelta(hours=5), "destination": "DEST-PHOENIX"},
        {"order_id": "ORD-1007", "status": "PROCESSING", "priority": "HIGH", "deadline": now + timedelta(hours=1), "destination": "DEST-PHILLY"},
        {"order_id": "ORD-1008", "status": "PENDING", "priority": "MEDIUM", "deadline": now + timedelta(hours=6), "destination": "DEST-DALLAS"},
        {"order_id": "ORD-1009", "status": "PROCESSING", "priority": "MEDIUM", "deadline": now - timedelta(days=7), "destination": "DEST-SEATTLE"},
        {"order_id": "ORD-1010", "status": "PENDING", "priority": "HIGH", "deadline": now + timedelta(hours=2), "destination": "DEST-CHICAGO"},
        {"order_id": "ORD-1011", "status": "PENDING", "priority": "MEDIUM", "deadline": now + timedelta(hours=4), "destination": "DEST-BOSTON"},
        {"order_id": "ORD-1012", "status": "PENDING", "priority": "HIGH", "deadline": now + timedelta(hours=1.5), "destination": "DEST-NYC"},
        {"order_id": "ORD-1013", "status": "PENDING", "priority": "LOW", "deadline": now + timedelta(hours=10), "destination": "DEST-LA"},
        {"order_id": "ORD-1014", "status": "PENDING", "priority": "MEDIUM", "deadline": now + timedelta(hours=6), "destination": "DEST-DENVER"},
        {"order_id": "ORD-1015", "status": "COMPLETED", "priority": "HIGH", "deadline": now - timedelta(hours=1), "destination": "DEST-MIAMI"},
        {"order_id": "ORD-1016", "status": "PENDING", "priority": "URGENT", "deadline": now + timedelta(hours=1), "destination": "DEST-ATLANTA"},
        {"order_id": "ORD-1017", "status": "PENDING", "priority": "LOW", "deadline": now + timedelta(hours=12), "destination": "DEST-PORTLAND"},
        {"order_id": "ORD-1018", "status": "CANCELLED", "priority": "LOW", "deadline": now + timedelta(hours=24), "destination": "DEST-DENVER"},
    ]
    
    order_objs = {}
    for o_data in orders_data:
        o = Order(**o_data)
        session.add(o)
        order_objs[o.order_id] = o
        
    session.flush() # get IDs if needed

    # 5. Seed Order Lines
    order_lines_data = [
        {"order_id": "ORD-1001", "sku": "SKU-001", "requested_qty": 5},
        {"order_id": "ORD-1001", "sku": "SKU-003", "requested_qty": 3},
        {"order_id": "ORD-1002", "sku": "SKU-002", "requested_qty": 8},
        {"order_id": "ORD-1002", "sku": "SKU-004", "requested_qty": 2},
        {"order_id": "ORD-1003", "sku": "SKU-001", "requested_qty": 2},
        {"order_id": "ORD-1003", "sku": "SKU-006", "requested_qty": 4},
        {"order_id": "ORD-1003", "sku": "SKU-008", "requested_qty": 1},
        {"order_id": "ORD-1004", "sku": "SKU-005", "requested_qty": 10},
        {"order_id": "ORD-1004", "sku": "SKU-003", "requested_qty": 2},
        {"order_id": "ORD-1005", "sku": "SKU-002", "requested_qty": 5},
        {"order_id": "ORD-1005", "sku": "SKU-007", "requested_qty": 3},
        {"order_id": "ORD-1006", "sku": "SKU-002", "requested_qty": 5},
        {"order_id": "ORD-1006", "sku": "SKU-007", "requested_qty": 3},
        {"order_id": "ORD-1007", "sku": "SKU-001", "requested_qty": 4},
        {"order_id": "ORD-1007", "sku": "SKU-009", "requested_qty": 2},
        {"order_id": "ORD-1008", "sku": "SKU-004", "requested_qty": -2},
        {"order_id": "ORD-1008", "sku": "SKU-006", "requested_qty": 3},
        {"order_id": "ORD-1009", "sku": "SKU-003", "requested_qty": 6},
        {"order_id": "ORD-1009", "sku": "SKU-010", "requested_qty": 2},
        {"order_id": "ORD-1010", "sku": "SKU-008", "requested_qty": 3},
        {"order_id": "ORD-1010", "sku": "SKU-001", "requested_qty": 2},
        {"order_id": "ORD-1011", "sku": "SKU-011", "requested_qty": 5},
        {"order_id": "ORD-1012", "sku": "SKU-002", "requested_qty": 4},
        {"order_id": "ORD-1012", "sku": "SKU-006", "requested_qty": 2},
        {"order_id": "ORD-1013", "sku": "SKU-004", "requested_qty": 3},
        {"order_id": "ORD-1013", "sku": "SKU-009", "requested_qty": 1},
        {"order_id": "ORD-1014", "sku": "SKU-001", "requested_qty": 3},
        {"order_id": "ORD-1014", "sku": "SKU-010", "requested_qty": 4},
        {"order_id": "ORD-1015", "sku": "SKU-005", "requested_qty": 2},
        {"order_id": "ORD-1015", "sku": "SKU-003", "requested_qty": 1},
        {"order_id": "ORD-1016", "sku": "SKU-002", "requested_qty": 6},
        {"order_id": "ORD-1016", "sku": "SKU-008", "requested_qty": 2},
        {"order_id": "ORD-1017", "sku": "SKU-006", "requested_qty": 2},
        {"order_id": "ORD-1017", "sku": "SKU-009", "requested_qty": 3},
        {"order_id": "ORD-1018", "sku": "SKU-001", "requested_qty": 1},
    ]
    for ol_data in order_lines_data:
        ol = OrderLine(**ol_data)
        session.add(ol)

    # 6. Seed Shipments
    shipments_data = [
        {"shipment_id": "SHP-101", "order_id": "ORD-1001", "status": "PENDING", "carrier": "FedEx", "destination": "DEST-NYC", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-102", "order_id": "ORD-1002", "status": "PENDING", "carrier": "UPS", "destination": "DEST-LA", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-103", "order_id": "ORD-1003", "status": "PENDING", "carrier": "USPS", "destination": "DEST-CHICAGO", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-104", "order_id": "ORD-1004", "status": "PENDING", "carrier": "FedEx", "destination": "DEST-HOUSTON", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-105", "order_id": "ORD-1005", "status": "PENDING", "carrier": "UPS", "destination": "DEST-PHOENIX", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-106", "order_id": "ORD-1006", "status": "PENDING", "carrier": "UPS", "destination": "DEST-PHOENIX", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-107", "order_id": "ORD-1007", "status": "DELIVERED", "carrier": "FedEx", "destination": "DEST-PHILLY", "created_at": now - timedelta(hours=5)},
        {"shipment_id": "SHP-108", "order_id": "ORD-1008", "status": "PENDING", "carrier": "DHL", "destination": "DEST-DALLAS", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-109", "order_id": "ORD-1009", "status": "IN_TRANSIT", "carrier": "FedEx", "destination": "DEST-SEATTLE", "created_at": now - timedelta(days=14)},
        {"shipment_id": "SHP-110", "order_id": "ORD-1010", "status": "PENDING", "carrier": "UPS", "destination": "DEST-DALLAS", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-111", "order_id": "ORD-1012", "status": "PENDING", "carrier": "FedEx", "destination": "DEST-NYC", "created_at": now - timedelta(hours=1)},
        {"shipment_id": "SHP-115", "order_id": "ORD-1015", "status": "DELIVERED", "carrier": "UPS", "destination": "DEST-MIAMI", "created_at": now - timedelta(hours=24)},
    ]
    for s_data in shipments_data:
        s = Shipment(**s_data)
        session.add(s)

    session.commit()
    print("Database seeded successfully.")
    
    print(f"Summary:")
    print(f"- Policies: {len(policies_data)}")
    print(f"- Pickers: {len(pickers)}")
    print(f"- Inventories: {len(inventories)}")
    print(f"- Orders: {len(orders_data)}")
    print(f"- Order Lines: {len(order_lines_data)}")
    print(f"- Shipments: {len(shipments_data)}")

def reset_database(session: Session):
    print("Resetting database...")
    seed_database(session)

if __name__ == "__main__":
    from app.models.database import get_db
    db_gen = get_db()
    session = next(db_gen)
    try:
        reset_database(session)
    finally:
        session.close()
