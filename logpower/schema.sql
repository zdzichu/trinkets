
CREATE TABLE measurements (
	id	serial PRIMARY KEY,
	datetime	timestamp NOT NULL,
);

CREATE TABLE measurements_items (
	id	bigserial PRIMARY KEY,
	measurement_id	XXX
	field_id XXX
	field_value XXX
	sensor_id	int NOT NULL,
	value	double precision
);

CREATE INDEX idx_timestamp ON temperatures(datetime);
CREATE INDEX idx_sensors ON temperatures(sensor_id);
