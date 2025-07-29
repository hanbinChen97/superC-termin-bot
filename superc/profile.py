from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from db.models import AppointmentProfile

@dataclass
class Profile:
    """Profile dataclass for form filling, interfaces with AppointmentProfile database model"""
    
    vorname: str
    nachname: str
    email: str
    phone: str
    geburtsdatum_day: int
    geburtsdatum_month: int
    geburtsdatum_year: int
    preferred_locations: str = 'superc'
    
    @classmethod
    def from_appointment_profile(cls, appointment_profile: AppointmentProfile) -> 'Profile':
        """Create Profile instance from AppointmentProfile database model"""
        return cls(
            vorname=appointment_profile.vorname or "",
            nachname=appointment_profile.nachname or "",
            email=appointment_profile.email or "",
            phone=appointment_profile.phone or "",
            geburtsdatum_day=appointment_profile.geburtsdatum_day or 1,
            geburtsdatum_month=appointment_profile.geburtsdatum_month or 1,
            geburtsdatum_year=appointment_profile.geburtsdatum_year or 1990,
            preferred_locations=appointment_profile.preferred_locations or 'superc'
        )
    
    def to_form_data(self) -> dict:
        """Convert Profile to form data dictionary for appointment booking"""
        return {
            'vorname': self.vorname,
            'nachname': self.nachname,
            'email': self.email,
            'phone': self.phone,
            'geburtsdatum_day': str(self.geburtsdatum_day),
            'geburtsdatum_month': str(self.geburtsdatum_month),
            'geburtsdatum_year': str(self.geburtsdatum_year)
        }
    
    @property
    def full_name(self) -> str:
        """Get full name for display purposes"""
        return f"{self.vorname} {self.nachname}".strip()
    
    @property
    def birth_date(self) -> datetime:
        """Get birth date as datetime object"""
        return datetime(
            year=self.geburtsdatum_year,
            month=self.geburtsdatum_month, 
            day=self.geburtsdatum_day
        )
    
    def print_info(self) -> None:
        """打印所有Profile信息"""
        print("=== Profile 信息 ===")
        print(f"姓名: {self.full_name}")
        print(f"邮箱: {self.email}")
        print(f"电话: {self.phone}")
        print(f"生日: {self.geburtsdatum_day}/{self.geburtsdatum_month}/{self.geburtsdatum_year}")
        print(f"偏好地点: {self.preferred_locations}")
        print("-" * 30)