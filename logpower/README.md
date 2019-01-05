
INSTALL
-------

Get https://github.com/cbergmiller/iec62056

CURATING THE DATA FROM DATABASE
-------------------------------

See views declared in SQL schema file.


In Grafana, you can use following snippet:
```
SELECT
  $__time(m_datetime),
  '1.8.'||pmi_group_e_tariff AS metric,
  split_part(pmi_data, '*', 1)::float
FROM
  v_powerconsumption
WHERE
  pmi_group_f_historical = '00' AND
  $__timeFilter(m_datetime)

```

`split_part()` is needed to strip '*kWh' added by some meters.

Graphing current utilization can be dne with:

```
SELECT
  $__time(m_datetime),
  field AS metric,
  delta * 1000
FROM
  v_power_delta
WHERE
  $__timeFilter(m_datetime)
ORDER BY
  m_datetime ASC
```
