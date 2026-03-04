"""
Logistics models: Transport, Library, Hostel, Lab
Multi-tenant, inheriting from BaseModel
"""

from app.models.base import BaseModel
from app.extensions import db
from datetime import datetime, date


# ==================== TRANSPORT ====================

class Vehicle(BaseModel):
    """Vehicle for transport - Multi-tenant"""
    __tablename__ = 'vehicles'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    vehicle_number = db.Column(db.String(50), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)  # bus, van, car, etc.
    capacity = db.Column(db.Integer, nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    registration_number = db.Column(db.String(50), nullable=False)
    insurance_expiry = db.Column(db.Date, nullable=True)
    pollution_certificate_expiry = db.Column(db.Date, nullable=True)
    fitness_certificate_expiry = db.Column(db.Date, nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    gps_device_id = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    driver = db.relationship('User', foreign_keys=[driver_id])
    helper = db.relationship('User', foreign_keys=[helper_id])
    routes = db.relationship('Route', back_populates='vehicle', cascade='all, delete-orphan')
    gps_logs = db.relationship('GPSLog', backref='vehicle', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'vehicle_number', name='uq_vehicle_number'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'vehicle_number': self.vehicle_number,
            'vehicle_type': self.vehicle_type,
            'capacity': self.capacity,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'registration_number': self.registration_number,
            'insurance_expiry': self.insurance_expiry.isoformat() if self.insurance_expiry else None,
            'pollution_certificate_expiry': self.pollution_certificate_expiry.isoformat() if self.pollution_certificate_expiry else None,
            'fitness_certificate_expiry': self.fitness_certificate_expiry.isoformat() if self.fitness_certificate_expiry else None,
            'driver_id': self.driver_id,
            'driver_name': self.driver.name if self.driver else None,
            'helper_id': self.helper_id,
            'helper_name': self.helper.name if self.helper else None,
            'is_active': self.is_active
        })
        return data


class Route(BaseModel):
    """Transport route - Multi-tenant"""
    __tablename__ = 'routes'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Route A - North"
    direction = db.Column(db.String(50), nullable=False)  # pickup, drop, both
    start_point = db.Column(db.String(255), nullable=False)
    end_point = db.Column(db.String(255), nullable=False)
    pickup_time = db.Column(db.Time, nullable=True)
    drop_time = db.Column(db.Time, nullable=True)
    total_stops = db.Column(db.Integer, nullable=True)
    route_distance = db.Column(db.Float, nullable=True)  # in km
    monthly_fare = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    vehicle = db.relationship('Vehicle', foreign_keys=[vehicle_id], back_populates='routes')
    stops = db.relationship('RouteStop', backref='route', cascade='all, delete-orphan')
    allocations = db.relationship('StudentTransportAllocation', back_populates='route', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'name', name='uq_route_name'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'vehicle_id': self.vehicle_id,
            'vehicle_number': self.vehicle.vehicle_number,
            'name': self.name,
            'direction': self.direction,
            'start_point': self.start_point,
            'end_point': self.end_point,
            'pickup_time': self.pickup_time.isoformat() if self.pickup_time else None,
            'drop_time': self.drop_time.isoformat() if self.drop_time else None,
            'total_stops': self.total_stops,
            'route_distance': self.route_distance,
            'monthly_fare': float(self.monthly_fare),
            'is_active': self.is_active
        })
        return data


class RouteStop(BaseModel):
    """Stop on a transport route - Multi-tenant"""
    __tablename__ = 'route_stops'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    stop_number = db.Column(db.Integer, nullable=False)
    stop_name = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    arrival_time = db.Column(db.Time, nullable=True)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'route_id': self.route_id,
            'stop_number': self.stop_number,
            'stop_name': self.stop_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None
        })
        return data


class StudentTransportAllocation(BaseModel):
    """Allocate student to transport route - Multi-tenant"""
    __tablename__ = 'student_transport_allocations'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='transport_allocations')
    route = db.relationship('Route', foreign_keys=[route_id], back_populates='allocations')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'student_id', 'route_id', 'from_date', 
                                          name='uq_student_route_allocation'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'route_id': self.route_id,
            'route_name': self.route.name,
            'from_date': self.from_date.isoformat(),
            'to_date': self.to_date.isoformat() if self.to_date else None,
            'is_active': self.is_active
        })
        return data


class GPSLog(BaseModel):
    """GPS tracking for vehicles - Multi-tenant"""
    __tablename__ = 'gps_logs'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=True)  # km/h
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'vehicle_id': self.vehicle_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'speed': self.speed,
            'logged_at': self.logged_at.isoformat()
        })
        return data


# ==================== LIBRARY ====================

class Book(BaseModel):
    """Library book - Multi-tenant"""
    __tablename__ = 'books'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    isbn = db.Column(db.String(50), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    publisher = db.Column(db.String(255), nullable=True)
    publication_year = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    acquisition_date = db.Column(db.Date, nullable=True)
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    location = db.Column(db.String(100), nullable=True)  # Rack/Shelf number
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    issues = db.relationship('BookIssue', back_populates='book', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'isbn', name='uq_school_isbn'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'publication_year': self.publication_year,
            'category': self.category,
            'total_copies': self.total_copies,
            'available_copies': self.available_copies,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'cost': float(self.cost) if self.cost else None,
            'location': self.location,
            'is_active': self.is_active
        })
        return data


class BookIssue(BaseModel):
    """Book issue record - Multi-tenant"""
    __tablename__ = 'book_issues'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    fine_charged = db.Column(db.Numeric(10, 2), default=0)
    fine_paid = db.Column(db.Boolean, default=False)
    is_returned = db.Column(db.Boolean, default=False)
    remarks = db.Column(db.Text)
    
    # Relationships
    book = db.relationship('Book', foreign_keys=[book_id], back_populates='issues')
    user = db.relationship('User', foreign_keys=[user_id], backref='book_issues')
    
    def is_overdue(self):
        """Check if book is overdue"""
        return not self.is_returned and date.today() > self.due_date
    
    def calculate_fine(self, daily_rate=10):
        """Calculate fine for overdue books"""
        if self.is_returned and self.return_date:
            if self.return_date > self.due_date:
                days_overdue = (self.return_date - self.due_date).days
                return days_overdue * daily_rate
        elif not self.is_returned:
            days_overdue = (date.today() - self.due_date).days
            if days_overdue > 0:
                return days_overdue * daily_rate
        return 0
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'book_id': self.book_id,
            'book_title': self.book.title,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'issue_date': self.issue_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'fine_charged': float(self.fine_charged),
            'fine_paid': self.fine_paid,
            'is_returned': self.is_returned,
            'is_overdue': self.is_overdue(),
            'remarks': self.remarks
        })
        return data


# ==================== HOSTEL ====================

class HostelRoom(BaseModel):
    """Hostel room - Multi-tenant"""
    __tablename__ = 'hostel_rooms'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.Integer, nullable=True)
    building = db.Column(db.String(50), nullable=True)
    room_type = db.Column(db.String(50), nullable=False)  # single, double, triple, etc.
    capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0)
    monthly_rent = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    allocations = db.relationship('HostelAllocation', back_populates='room', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'room_number', name='uq_room_number'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'room_number': self.room_number,
            'floor': self.floor,
            'building': self.building,
            'room_type': self.room_type,
            'capacity': self.capacity,
            'current_occupancy': self.current_occupancy,
            'available_seats': self.capacity - self.current_occupancy,
            'monthly_rent': float(self.monthly_rent),
            'is_active': self.is_active
        })
        return data


class HostelAllocation(BaseModel):
    """Allocate student to hostel room - Multi-tenant"""
    __tablename__ = 'hostel_allocations'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('hostel_rooms.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='hostel_allocations')
    room = db.relationship('HostelRoom', foreign_keys=[room_id], back_populates='allocations')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'student_id', 'from_date', name='uq_hostel_allocation'),)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'room_id': self.room_id,
            'room_number': self.room.room_number,
            'from_date': self.from_date.isoformat(),
            'to_date': self.to_date.isoformat() if self.to_date else None,
            'is_active': self.is_active
        })
        return data


# ==================== LAB ====================

class LabInventory(BaseModel):
    """Lab equipment/material inventory - Multi-tenant"""
    __tablename__ = 'lab_inventory'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Chemistry, Physics, Biology, etc.
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(50), nullable=True)  # pieces, liters, grams, etc.
    acquisition_date = db.Column(db.Date, nullable=True)
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    location = db.Column(db.String(100), nullable=True)  # Lab name/section
    reorder_level = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'school_id': self.school_id,
            'item_name': self.item_name,
            'category': self.category,
            'quantity': self.quantity,
            'unit': self.unit,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'cost': float(self.cost) if self.cost else None,
            'location': self.location,
            'reorder_level': self.reorder_level,
            'needs_reorder': self.quantity <= self.reorder_level,
            'is_active': self.is_active
        })
        return data
