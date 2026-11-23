CREATE INDEX attendance_tenant_date_idx
    ON attendance (tenant_id, attended_on);
