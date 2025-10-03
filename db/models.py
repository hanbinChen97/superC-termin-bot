from sqlalchemy import Column, Integer, BigInteger, Text, DateTime, Boolean, Index, String, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func, text

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)  # serial in PostgreSQL
    name = Column(String(100))
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, default='member')
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', role='{self.role}')>"

class AppointmentProfile(Base):
    __tablename__ = 'appointment_profiles'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 基本信息
    vorname = Column(Text)
    nachname = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    geburtsdatum_day = Column(Integer)
    geburtsdatum_month = Column(Integer)
    geburtsdatum_year = Column(Integer)
    preferred_locations = Column(Text, default='superc')
    
    # 预约状态和进度
    appointment_status = Column(Text, default='waiting')  # waiting, booked
    
    # 预约详情
    appointment_date = Column(DateTime)
    location_type = Column(Text)
    
    # 完成时间
    completed_at = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AppointmentProfile(id={self.id}, vorname='{self.vorname}', nachname='{self.nachname}', status='{self.appointment_status}')>"

# 定义索引
# 部分索引：只对等待状态的记录建立索引，按创建时间升序排列，方便查找排队最久的人
waiting_queue_idx = Index(
    'waiting_queue_idx',
    AppointmentProfile.created_at,
    postgresql_where=text("appointment_status = 'waiting'")
)

class AppLogsMin(Base):
    __tablename__ = 'app_logs_min'
    
    id = Column(BigInteger, primary_key=True)  # bigserial in PostgreSQL
    log_timestamp = Column(DateTime(timezone=True), nullable=False)
    level = Column(Text, nullable=False)
    schritt = Column(Text, nullable=False, default='-')
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Check constraint for level
    __table_args__ = (
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name='app_logs_min_level_check'
        ),
    )
    
    def __repr__(self):
        return f"<AppLogsMin(id={self.id}, level='{self.level}', log_timestamp='{self.log_timestamp}')>"

# 定义 app_logs_min 的索引
app_logs_min_timestamp_idx = Index(
    'idx_app_logs_min_timestamp',
    AppLogsMin.log_timestamp.desc()
)

app_logs_min_level_idx = Index(
    'idx_app_logs_min_level',
    AppLogsMin.level
)
