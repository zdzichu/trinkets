
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
-- help grafana using extract epoch - and not getting index goodies
-- see also https://www.depesz.com/2014/04/04/how-to-deal-with-timestamps/
CREATE INDEX idx_temperatures_timestamp_brin ON temperatures((extract(epoch from datetime at time zone 'UTC')));

CREATE INDEX idx_sensors ON temperatures(sensor_id);
