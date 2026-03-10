"""
Repository pattern for database operations
"""

import json
import uuid

from src.database import close_session, get_session
from src.database.models import PackingItem as DBPackingItem
from src.database.models import Traveler as DBTraveler
from src.database.models import Trip as DBTrip
from src.database.models import User as DBUser
from src.models.packing_item import PackingItem
from src.models.trip import Trip


class UserRepository:
    """Repository for User operations"""

    @staticmethod
    def create(username: str, email: str, password: str) -> DBUser:
        """Create a new user"""
        session = get_session()
        try:
            user = DBUser(id=f"user_{uuid.uuid4().hex[:8]}", username=username, email=email)
            user.set_password(password)

            session.add(user)
            session.commit()
            session.refresh(user)

            return user
        finally:
            close_session()

    @staticmethod
    def get(user_id: str) -> DBUser | None:
        """Get user by ID"""
        session = get_session()
        try:
            return session.query(DBUser).filter(DBUser.id == user_id).first()
        finally:
            close_session()

    @staticmethod
    def get_by_username(username: str) -> DBUser | None:
        """Get user by username"""
        session = get_session()
        try:
            return session.query(DBUser).filter(DBUser.username == username).first()
        finally:
            close_session()

    @staticmethod
    def get_by_email(email: str) -> DBUser | None:
        """Get user by email"""
        session = get_session()
        try:
            return session.query(DBUser).filter(DBUser.email == email).first()
        finally:
            close_session()

    @staticmethod
    def update_last_login(user_id: str) -> None:
        """Update user's last login timestamp"""
        from datetime import datetime

        session = get_session()
        try:
            user = session.query(DBUser).filter(DBUser.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        finally:
            close_session()


class TripRepository:
    """Repository for Trip operations"""

    @staticmethod
    def create(trip: Trip, user_id: str) -> Trip:
        """Create a new trip in database"""
        session = get_session()
        try:
            # Generate ID if not exists
            if not trip.id:
                trip.id = f"trip_{uuid.uuid4().hex[:8]}"

            # Create DB model
            db_trip = DBTrip(
                id=trip.id,
                user_id=user_id,
                destination=trip.destination,
                start_date=trip.start_date,
                end_date=trip.end_date,
                duration=trip.duration,
                travel_style=trip.travel_style,
                transportation=trip.transportation,
                activities=json.dumps(trip.activities),
                special_notes=trip.special_notes,
                weather_conditions=trip.weather_conditions,
            )

            # Add travelers
            for _i, traveler_name in enumerate(trip.travelers):
                db_traveler = DBTraveler(
                    id=f"traveler_{uuid.uuid4().hex[:8]}",
                    trip_id=trip.id,
                    name=traveler_name,
                    traveler_type="adult",  # Default
                    special_needs=json.dumps([]),
                    preferences=json.dumps([]),
                )
                db_trip.travelers.append(db_traveler)

            session.add(db_trip)
            session.commit()
            session.refresh(db_trip)

            return TripRepository._to_domain(db_trip)
        finally:
            close_session()

    @staticmethod
    def get(trip_id: str, user_id: str | None = None) -> Trip | None:
        """Get a trip by ID, optionally verify ownership"""
        session = get_session()
        try:
            query = session.query(DBTrip).filter(DBTrip.id == trip_id)
            if user_id:
                query = query.filter(DBTrip.user_id == user_id)
            db_trip = query.first()
            if db_trip:
                return TripRepository._to_domain(db_trip)
            return None
        finally:
            close_session()

    @staticmethod
    def list_all(user_id: str | None = None) -> list[Trip]:
        """List all trips, optionally filtered by user"""
        session = get_session()
        try:
            query = session.query(DBTrip)
            if user_id:
                query = query.filter(DBTrip.user_id == user_id)
            db_trips = query.order_by(DBTrip.created_at.desc()).all()
            return [TripRepository._to_domain(db_trip) for db_trip in db_trips]
        finally:
            close_session()

    @staticmethod
    def update(trip_id: str, **kwargs) -> Trip | None:
        """Update a trip"""
        session = get_session()
        try:
            db_trip = session.query(DBTrip).filter(DBTrip.id == trip_id).first()
            if not db_trip:
                return None

            # Update fields
            for key, value in kwargs.items():
                if hasattr(db_trip, key) and value is not None:
                    if key == "activities":
                        setattr(db_trip, key, json.dumps(value))
                    else:
                        setattr(db_trip, key, value)

            session.commit()
            session.refresh(db_trip)

            return TripRepository._to_domain(db_trip)
        finally:
            close_session()

    @staticmethod
    def delete(trip_id: str) -> bool:
        """Delete a trip"""
        session = get_session()
        try:
            db_trip = session.query(DBTrip).filter(DBTrip.id == trip_id).first()
            if db_trip:
                session.delete(db_trip)
                session.commit()
                return True
            return False
        finally:
            close_session()

    @staticmethod
    def _to_domain(db_trip: DBTrip) -> Trip:
        """Convert database model to domain model"""
        return Trip(
            id=db_trip.id,
            destination=db_trip.destination,
            start_date=db_trip.start_date,
            end_date=db_trip.end_date,
            duration=db_trip.duration,
            travelers=[t.name for t in db_trip.travelers],
            travel_style=db_trip.travel_style,
            transportation=db_trip.transportation,
            activities=json.loads(db_trip.activities) if db_trip.activities else [],
            special_notes=db_trip.special_notes,
            weather_conditions=db_trip.weather_conditions,
            is_template=db_trip.is_template if hasattr(db_trip, "is_template") else False,
            template_name=db_trip.template_name if hasattr(db_trip, "template_name") else None,
        )


class PackingItemRepository:
    """Repository for PackingItem operations"""

    @staticmethod
    def create(item: PackingItem) -> PackingItem:
        """Create a new packing item"""
        session = get_session()
        try:
            if not item.id:
                item.id = f"item_{uuid.uuid4().hex[:8]}"

            db_item = DBPackingItem(
                id=item.id,
                trip_id=item.trip_id,
                name=item.name,
                category=item.category,
                quantity=item.quantity,
                is_packed=item.is_packed,
                is_essential=item.is_essential,
                notes=item.notes,
                ai_suggested=item.ai_suggested,
            )

            session.add(db_item)
            session.commit()
            session.refresh(db_item)

            return PackingItemRepository._to_domain(db_item)
        finally:
            close_session()

    @staticmethod
    def get(item_id: str) -> PackingItem | None:
        """Get a packing item by ID"""
        session = get_session()
        try:
            db_item = session.query(DBPackingItem).filter(DBPackingItem.id == item_id).first()
            if db_item:
                return PackingItemRepository._to_domain(db_item)
            return None
        finally:
            close_session()

    @staticmethod
    def get_by_trip(trip_id: str) -> list[PackingItem]:
        """Get all items for a trip"""
        session = get_session()
        try:
            db_items = (
                session.query(DBPackingItem)
                .filter(DBPackingItem.trip_id == trip_id)
                .order_by(DBPackingItem.display_order.asc(), DBPackingItem.created_at.asc())
                .all()
            )

            return [PackingItemRepository._to_domain(db_item) for db_item in db_items]
        finally:
            close_session()

    @staticmethod
    def update(item_id: str, **kwargs) -> PackingItem | None:
        """Update a packing item"""
        session = get_session()
        try:
            db_item = session.query(DBPackingItem).filter(DBPackingItem.id == item_id).first()
            if not db_item:
                return None

            for key, value in kwargs.items():
                if hasattr(db_item, key) and value is not None:
                    setattr(db_item, key, value)

            session.commit()
            session.refresh(db_item)

            return PackingItemRepository._to_domain(db_item)
        finally:
            close_session()

    @staticmethod
    def delete(item_id: str) -> bool:
        """Delete a packing item"""
        session = get_session()
        try:
            db_item = session.query(DBPackingItem).filter(DBPackingItem.id == item_id).first()
            if db_item:
                session.delete(db_item)
                session.commit()
                return True
            return False
        finally:
            close_session()

    @staticmethod
    def get_history(user_id: str) -> list[dict]:
        """Get packing history for a user: items that were reviewed (actually_used is not None)"""
        session = get_session()
        try:
            db_items = (
                session.query(DBPackingItem)
                .join(DBTrip, DBPackingItem.trip_id == DBTrip.id)
                .filter(DBTrip.user_id == user_id, DBPackingItem.actually_used.isnot(None))
                .all()
            )
            results = []
            for item in db_items:
                results.append(
                    {
                        "name": item.name,
                        "category": item.category.value if item.category else "other",
                        "actually_used": item.actually_used,
                        "ai_suggested": item.ai_suggested,
                        "trip_id": item.trip_id,
                    }
                )
            return results
        finally:
            close_session()

    @staticmethod
    def _to_domain(db_item: DBPackingItem) -> PackingItem:
        """Convert database model to domain model"""
        return PackingItem(
            id=db_item.id,
            trip_id=db_item.trip_id,
            name=db_item.name,
            category=db_item.category,
            quantity=db_item.quantity,
            is_packed=db_item.is_packed,
            is_essential=db_item.is_essential,
            notes=db_item.notes,
            ai_suggested=db_item.ai_suggested,
            actually_used=db_item.actually_used if hasattr(db_item, "actually_used") else None,
            display_order=db_item.display_order if hasattr(db_item, "display_order") else 0,
        )
