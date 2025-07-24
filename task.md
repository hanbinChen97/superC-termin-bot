使用 SQLAlchemy ， 链接 supabase。

查找 appointment_profiles 表格。
export const appointmentProfiles = pgTable('appointment_profiles', {
  id: bigserial('id', { mode: 'number' }).primaryKey(),
  userId: integer('user_id')
    .notNull()
    .references(() => users.id),
  
  // 基本信息
  vorname: text('vorname'),
  nachname: text('nachname'),
  phone: text('phone'),
  geburtsdatumDay: integer('geburtsdatum_day'),
  geburtsdatumMonth: integer('geburtsdatum_month'),
  geburtsdatumYear: integer('geburtsdatum_year'),
  preferredLocations: jsonb('preferred_locations'),
  
  // 预约状态和进度
  appointmentStatus: text('appointment_status').default('waiting'), // waiting, booked
  
  // 预约详情
  appointmentDate: timestamp('appointment_date'),
  locationType: text('location_type'),
  
  // 完成时间
  completedAt: timestamp('completed_at'),
  
  // 时间戳
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
}, (table) => {
  return {
    statusCreatedAtIdx: index('status_created_at_idx').on(table.appointmentStatus, table.createdAt),
  }
});

读取nidex 里的第一个记录, 作为填表的记录。
