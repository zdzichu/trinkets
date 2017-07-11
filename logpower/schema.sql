
CREATE TABLE measurements (
	m_id	serial PRIMARY KEY,
	m_datetime	timestamp with time zone NOT NULL DEFAULT NOW()
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
	pmi_group_e_tariff	varchar(2) DEFAULT NULL,
	pmi_group_f_historical	varchar(2) DEFAULT NULL,
	-- 32 value + * + 16 unit, although I've seen additional fields adding aup to 63
	-- in mode C up to 128bytes, but we ignore it now
	pmi_data	varchar(64)
);


CREATE INDEX idx_m_datetime ON measurements USING BRIN(m_datetime);
CREATE INDEX idx_pmi_mid ON power_measurements_items(pmi_measurement_id);

-- create delta (in Watts) view for 1.8.0*00  (01,02 are historical values)
-- m2 - current measurement, m1 - previous measurement
CREATE VIEW v_power_delta AS SELECT m2.m_datetime, '1.8.0*00' AS field,
	( (pmi2.pmi_data::float - pmi1.pmi_data::float) / (EXTRACT(EPOCH FROM m2.m_datetime) - EXTRACT(EPOCH FROM m1.m_datetime)) ) * 1000 AS delta
	FROM power_measurements_items AS pmi1, power_measurements_items AS pmi2, measurements AS m1, measurements AS m2
	-- find previous measuremnts and its items
	WHERE m1.m_id = (SELECT m_id FROM measurements WHERE m_id < m2.m_id ORDER BY m_datetime DESC LIMIT 1)
	AND pmi2.pmi_measurement_id = m2.m_id AND pmi1.pmi_measurement_id = (SELECT m_id FROM measurements WHERE m_id < m2.m_id ORDER BY m_datetime DESC LIMIT 1)
	-- match groups in first and second measurement
	AND pmi1.pmi_group_c_type = '1'      AND pmi2.pmi_group_c_type = '1'
	AND pmi1.pmi_group_d_variable = '8'  AND pmi2.pmi_group_d_variable = '8'
	AND pmi1.pmi_group_e_tariff = '0'    AND pmi2.pmi_group_e_tariff='0'
	AND pmi1.pmi_group_f_historical='00' AND pmi2.pmi_group_f_historical='00';

/*
CREATE INDEX idx_timestamp ON temperatures(datetime);
CREATE INDEX idx_sensors ON temperatures(sensor_id); */
