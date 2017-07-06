
CREATE TABLE measurements (
	m_id	serial PRIMARY KEY,
	m_datetime	timestamp with time zone NOT NULL DEFAULT NOW(),
);

CREATE TABLE power_measurements_items (
	pmi_id	bigserial PRIMARY KEY,
	pmi_measurement_id	integer REFERENCES measurements(m_id),
	-- http://manuals.lian98.biz/doc.en/html/u_iec62056_struct.htm
	-- a-b:c.d.e*f
	pmi_group_a_medium	varchar(1) DEFAULT NULL,
	pmi_group_b_channel	varchar(1) DEFAULT NULL,
	pmi_group_c_type	varchar(2) NOT NULL,
	pmi_group_d_variable	varchar(2) NOT NULL,
	pmi_group_e_tariff	varchar(1) DEFAULT NULL,
	pmi_group_f_historical	varchar(2) DEFAULT NULL,
	-- 32 value + * + 16 unit
	-- in mode C up to 128bytes, but we ignore it now
	pmi_data	varchar(49)
);


CREATE INDEX idx_m_datetime ON measurements USING BRIN(m_datetime);
CREATE INDEX idx_pmi_mid ON power_measurements_items(pmi_measurement_id);

/* view kwh consumed z 1.8.0 ? 8?


CREATE INDEX idx_timestamp ON temperatures(datetime);
CREATE INDEX idx_sensors ON temperatures(sensor_id); /*
