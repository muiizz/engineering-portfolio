SELECT attendance_id, student_id, attended_on, present
FROM attendance
WHERE tenant_id = 37
  AND attended_on >= DATE '2025-03-01'
  AND attended_on < DATE '2025-03-08'
ORDER BY attended_on, attendance_id;
