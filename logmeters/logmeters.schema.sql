
id
timestamp
	        id      bigserial PRIMARY KEY,
		        datetime        timestamp with time zone NOT NULL DEFAULT NOW(),
		        sensor_id       int NOT NULL,
kind (water, heat)
		        value   double precision
remaining_battery_life_y?
				);
