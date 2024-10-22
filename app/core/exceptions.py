class VehicleUnavailableError(Exception):
    """Raised when a vehicle is unavailable for allocation."""
    pass

class DuplicateBookingError(Exception):
    """Raised when an employee tries to book a vehicle when one is already booked."""
    pass
