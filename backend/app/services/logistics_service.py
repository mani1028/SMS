"""
Logistics Service - CRUD and business logic for transport, library, hostel, lab
"""

from app.models.logistics import (Vehicle, Route, RouteStop, StudentTransportAllocation, GPSLog,
                                  Book, BookIssue, HostelRoom, HostelAllocation, LabInventory)
from app.extensions import db
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


# ==================== TRANSPORT SERVICE ====================

class TransportService:
    """Service for transport management"""
    
    @staticmethod
    def create_vehicle(school_id, vehicle_number, vehicle_type, capacity, registration_number,
                      manufacturer=None, model=None, driver_id=None, helper_id=None):
        """Create a vehicle"""
        try:
            existing = Vehicle.query.filter_by(school_id=school_id, vehicle_number=vehicle_number).first()
            if existing:
                return {'success': False, 'error': 'Vehicle already exists'}
            
            vehicle = Vehicle(
                school_id=school_id,
                vehicle_number=vehicle_number,
                vehicle_type=vehicle_type,
                capacity=capacity,
                registration_number=registration_number,
                manufacturer=manufacturer,
                model=model,
                driver_id=driver_id,
                helper_id=helper_id
            )
            db.session.add(vehicle)
            db.session.commit()
            
            return {'success': True, 'vehicle': vehicle.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating vehicle: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_route(school_id, vehicle_id, name, direction, start_point, end_point,
                    pickup_time=None, drop_time=None, monthly_fare=0, total_stops=None, distance=None):
        """Create a transport route"""
        try:
            route = Route(
                school_id=school_id,
                vehicle_id=vehicle_id,
                name=name,
                direction=direction,
                start_point=start_point,
                end_point=end_point,
                pickup_time=pickup_time,
                drop_time=drop_time,
                total_stops=total_stops,
                route_distance=distance,
                monthly_fare=monthly_fare
            )
            db.session.add(route)
            db.session.commit()
            
            return {'success': True, 'route': route.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating route: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_route_stop(school_id, route_id, stop_number, stop_name, latitude=None, longitude=None, arrival_time=None):
        """Add a stop to a route"""
        try:
            stop = RouteStop(
                school_id=school_id,
                route_id=route_id,
                stop_number=stop_number,
                stop_name=stop_name,
                latitude=latitude,
                longitude=longitude,
                arrival_time=arrival_time
            )
            db.session.add(stop)
            db.session.commit()
            
            return {'success': True, 'stop': stop.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding route stop: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def allocate_student_to_route(school_id, student_id, route_id, from_date=None):
        """Allocate student to transport route"""
        try:
            if not from_date:
                from_date = date.today()
            
            allocation = StudentTransportAllocation(
                school_id=school_id,
                student_id=student_id,
                route_id=route_id,
                from_date=from_date
            )
            db.session.add(allocation)
            db.session.commit()
            
            return {'success': True, 'allocation': allocation.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error allocating student: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_routes(school_id, page=1, limit=50):
        """Get all routes"""
        try:
            query = Route.query.filter_by(school_id=school_id, is_active=True)
            total = query.count()
            pages = (total + limit - 1) // limit
            
            routes = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'routes': [r.to_dict() for r in routes],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting routes: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def log_gps(school_id, vehicle_id, latitude, longitude, speed=None):
        """Log GPS location"""
        try:
            log = GPSLog(
                school_id=school_id,
                vehicle_id=vehicle_id,
                latitude=latitude,
                longitude=longitude,
                speed=speed,
                logged_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
            
            return {'success': True, 'log': log.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error logging GPS: {str(e)}")
            return {'success': False, 'error': str(e)}


# ==================== LIBRARY SERVICE ====================

class LibraryService:
    """Service for library management"""
    
    @staticmethod
    def add_book(school_id, title, author, isbn, total_copies=1,
                publisher=None, publication_year=None, category=None, cost=None, location=None):
        """Add a book to library"""
        try:
            existing = Book.query.filter_by(school_id=school_id, isbn=isbn).first()
            if existing:
                return {'success': False, 'error': 'Book already exists'}
            
            book = Book(
                school_id=school_id,
                title=title,
                author=author,
                isbn=isbn,
                total_copies=total_copies,
                available_copies=total_copies,
                publisher=publisher,
                publication_year=publication_year,
                category=category,
                cost=cost,
                location=location
            )
            db.session.add(book)
            db.session.commit()
            
            return {'success': True, 'book': book.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding book: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def issue_book(school_id, book_id, user_id, due_date=None):
        """Issue a book to user"""
        try:
            book = Book.query.filter_by(id=book_id, school_id=school_id).first()
            if not book:
                return {'success': False, 'error': 'Book not found'}
            
            if book.available_copies <= 0:
                return {'success': False, 'error': 'No copies available'}
            
            if not due_date:
                due_date = date.today() + timedelta(days=14)  # 2 weeks by default
            
            issue = BookIssue(
                school_id=school_id,
                book_id=book_id,
                user_id=user_id,
                issue_date=date.today(),
                due_date=due_date
            )
            
            # Decrease available copies
            book.available_copies -= 1
            
            db.session.add(issue)
            db.session.commit()
            
            return {'success': True, 'issue': issue.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error issuing book: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def return_book(school_id, issue_id, return_date=None):
        """Return a book"""
        try:
            issue = BookIssue.query.filter_by(id=issue_id, school_id=school_id).first()
            if not issue:
                return {'success': False, 'error': 'Issue record not found'}
            
            if issue.is_returned:
                return {'success': False, 'error': 'Book already returned'}
            
            if not return_date:
                return_date = date.today()
            
            issue.return_date = return_date
            issue.is_returned = True
            
            # Calculate fine if overdue
            if return_date > issue.due_date:
                days_overdue = (return_date - issue.due_date).days
                fine = days_overdue * 10  # ₹10 per day
                issue.fine_charged = fine
                if fine > 0:
                    logger.info(f"Fine calculated for book {issue.book_id}: ₹{fine}")
            
            # Increase available copies
            issue.book.available_copies += 1
            
            db.session.commit()
            
            return {'success': True, 'issue': issue.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error returning book: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_books(school_id, category=None, page=1, limit=50):
        """Get library books"""
        try:
            query = Book.query.filter_by(school_id=school_id, is_active=True)
            
            if category:
                query = query.filter_by(category=category)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            books = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'books': [b.to_dict() for b in books],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting books: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_user_issued_books(school_id, user_id):
        """Get books issued to a user"""
        try:
            issues = BookIssue.query.filter_by(
                school_id=school_id,
                user_id=user_id,
                is_returned=False
            ).all()
            
            return {'success': True, 'issues': [i.to_dict() for i in issues]}
        except Exception as e:
            logger.error(f"Error getting issued books: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_overdue_books(school_id):
        """Get overdue books"""
        try:
            overdue = BookIssue.query.filter(
                BookIssue.school_id == school_id,
                BookIssue.is_returned == False,
                BookIssue.due_date < date.today()
            ).all()
            
            return {'success': True, 'overdue': [o.to_dict() for o in overdue]}
        except Exception as e:
            logger.error(f"Error getting overdue books: {str(e)}")
            return {'success': False, 'error': str(e)}


# ==================== HOSTEL SERVICE ====================

class HostelService:
    """Service for hostel management"""
    
    @staticmethod
    def create_room(school_id, room_number, room_type, capacity, monthly_rent, floor=None, building=None):
        """Create hostel room"""
        try:
            existing = HostelRoom.query.filter_by(school_id=school_id, room_number=room_number).first()
            if existing:
                return {'success': False, 'error': 'Room already exists'}
            
            room = HostelRoom(
                school_id=school_id,
                room_number=room_number,
                room_type=room_type,
                capacity=capacity,
                monthly_rent=monthly_rent,
                floor=floor,
                building=building
            )
            db.session.add(room)
            db.session.commit()
            
            return {'success': True, 'room': room.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating room: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def allocate_student_to_room(school_id, student_id, room_id, from_date=None):
        """Allocate student to room"""
        try:
            room = HostelRoom.query.filter_by(id=room_id, school_id=school_id).first()
            if not room:
                return {'success': False, 'error': 'Room not found'}
            
            if room.current_occupancy >= room.capacity:
                return {'success': False, 'error': 'Room is full'}
            
            if not from_date:
                from_date = date.today()
            
            allocation = HostelAllocation(
                school_id=school_id,
                student_id=student_id,
                room_id=room_id,
                from_date=from_date
            )
            
            room.current_occupancy += 1
            
            db.session.add(allocation)
            db.session.commit()
            
            return {'success': True, 'allocation': allocation.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error allocating room: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def deallocate_student(school_id, allocation_id, to_date=None):
        """Remove student from room"""
        try:
            allocation = HostelAllocation.query.filter_by(id=allocation_id, school_id=school_id).first()
            if not allocation:
                return {'success': False, 'error': 'Allocation not found'}
            
            if not to_date:
                to_date = date.today()
            
            allocation.to_date = to_date
            allocation.is_active = False
            
            # Decrease occupancy
            allocation.room.current_occupancy = max(0, allocation.room.current_occupancy - 1)
            
            db.session.commit()
            
            return {'success': True, 'allocation': allocation.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deallocating room: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_rooms(school_id, page=1, limit=50):
        """Get hostel rooms"""
        try:
            query = HostelRoom.query.filter_by(school_id=school_id, is_active=True)
            total = query.count()
            pages = (total + limit - 1) // limit
            
            rooms = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'rooms': [r.to_dict() for r in rooms],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting rooms: {str(e)}")
            return {'success': False, 'error': str(e)}


# ==================== LAB SERVICE ====================

class LabService:
    """Service for lab inventory management"""
    
    @staticmethod
    def add_item(school_id, item_name, category, quantity, unit, cost=None, location=None, reorder_level=5):
        """Add item to lab inventory"""
        try:
            item = LabInventory(
                school_id=school_id,
                item_name=item_name,
                category=category,
                quantity=quantity,
                unit=unit,
                acquisition_date=date.today(),
                cost=cost,
                location=location,
                reorder_level=reorder_level
            )
            db.session.add(item)
            db.session.commit()
            
            return {'success': True, 'item': item.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding lab item: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_quantity(school_id, item_id, quantity_change, remarks=None):
        """Update item quantity"""
        try:
            item = LabInventory.query.filter_by(id=item_id, school_id=school_id).first()
            if not item:
                return {'success': False, 'error': 'Item not found'}
            
            item.quantity += quantity_change
            db.session.commit()
            
            return {'success': True, 'item': item.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating quantity: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_inventory(school_id, category=None, page=1, limit=50):
        """Get lab inventory"""
        try:
            query = LabInventory.query.filter_by(school_id=school_id, is_active=True)
            
            if category:
                query = query.filter_by(category=category)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            items = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'inventory': [i.to_dict() for i in items],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting inventory: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_reorder_items(school_id):
        """Get items that need reordering"""
        try:
            items = LabInventory.query.filter(
                LabInventory.school_id == school_id,
                LabInventory.quantity <= LabInventory.reorder_level
            ).all()
            
            return {'success': True, 'items': [i.to_dict() for i in items]}
        except Exception as e:
            logger.error(f"Error getting reorder items: {str(e)}")
            return {'success': False, 'error': str(e)}
