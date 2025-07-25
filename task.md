
export const appointmentProfiles = pgTable('appointment_profiles', {
  id: bigserial('id', { mode: 'number' }).primaryKey(),
  userId: integer('user_id')
    .notNull()
    .references(() => users.id),
  
  // 基本信息
  vorname: text('vorname'),
  nachname: text('nachname'),
  email: text('email'),
  phone: text('phone'),
  geburtsdatumDay: integer('geburtsdatum_day'),
  geburtsdatumMonth: integer('geburtsdatum_month'),
  geburtsdatumYear: integer('geburtsdatum_year'),
  preferredLocations: text('preferred_locations').default('superc'),
  
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
    // 部分索引：只对等待状态的记录建立索引，按创建时间升序排列，方便查找排队最久的人
    waitingQueueIdx: index('waiting_queue_idx').on(table.createdAt).where(sql`appointment_status = 'waiting'`),
  }
});

更新了 email 属性，请你更新 db/models.py 中的 AppointmentProfile 类。

增加文件 profile.py 用来定义 dataclaas Profile 类，用于填最后的表单。和 db/models.py 中的 AppointmentProfile 类对接。

