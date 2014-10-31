
CREATE TABLE sensors (
	id	serial PRIMARY KEY,
	SN	varchar(15) NOT NULL, -- serial number
	description	varchar
);

CREATE TABLE temperatures (
	id	bigserial PRIMARY KEY,
	datetime	timestamp NOT NULL,
	sensor_id	int NOT NULL,
	value	double precision
);
