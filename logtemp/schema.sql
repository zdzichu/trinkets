
CREATE TABLE sensors (
	id	serial PRIMARY KEY,
	SN	varchar(16) NOT NULL, -- serial number; 15 for onewire, but Raspi got 16 chars
	description	varchar
);

CREATE TABLE temperatures (
	id	bigserial PRIMARY KEY,
	datetime	timestamp with time zone NOT NULL DEFAULT NOW(),
	sensor_id	int NOT NULL,
	value	double precision
);

CREATE INDEX idx_temperatures_timestamp ON temperatures USING BRIN(datetime);
CREATE INDEX idx_sensors ON temperatures(sensor_id);
