# Smart Asset Monitoring – KPI and Sensor Guide

This guide defines the telemetry keys, their descriptions, units, and how they are used to calculate KPIs (Key Performance Indicators). It also provides instructions and examples for creating KPIs using the supported `DURATION(condition)` formula structure.

---

## ✅ KPI Authoring Guidelines

- **Formula Field**: Only `DURATION(condition)` is allowed.
- **All aggregation logic (Count, Sum, Average, etc.) must be defined in the parameters.**
- **No arithmetic expressions (e.g., COUNT(...) / TOTAL)** are allowed in the formula field.
- Use consistent parameter naming and value comparisons to ensure compatibility.

---

## 🧮 Example KPI Definitions

| KPI Name                      | Formula                      | Param1 Name     | Operation | Attribute        | Comparison   | Value           |
|------------------------------|------------------------------|------------------|-----------|------------------|--------------|-----------------|
| Machine Utilization (hrs)    | DURATION(machine_on) / 3600  | machine_on       | Count     | machine_status   | ==           | "Running"       |
| Downtime Events              | DURATION(downtime_trigger)   | downtime_trigger | Count     | machine_status   | ==           | "Stopped"       |
| Availability (%)             | DURATION(active)             | active           | Count     | utilization_status| ==          | 1               |
| Energy Use (kWh)             | DURATION(energy_detected)    | energy_detected  | Sum       | energy_kWh       | >            | 0               |
| Generator Runtime (mins)     | DURATION(generator_on) / 60  | generator_on     | Count     | generator_status | ==           | "On"            |
| Temperature Compliance (mins)| DURATION(in_range) / 60      | in_range         | Count     | temp             | BETWEEN      | -1 AND 5        |
| Overheat Events              | DURATION(overheat)           | overheat         | Count     | temp             | >            | 10              |
| Alarm Active Time (mins)     | DURATION(alarm_active) / 60  | alarm_active     | Count     | alarm_status     | ==           | "Active"        |
| OEE Availability (%)         | DURATION(available)          | available        | Count     | machine_status   | ==           | "Running"       |
| Tilt Within Safe Range       | DURATION(safe_tilt)          | safe_tilt        | Count     | tilt             | BETWEEN      | -10 AND 10      |
| Max Pressure Breach Time     | DURATION(high_pressure)      | high_pressure    | Count     | pressure         | >            | 75              |
| Vibration Alert Duration     | DURATION(vibration_alert)    | vibration_alert  | Count     | vibration         | >           | 1.0             |
| Humidity In Range (min)      | DURATION(humidity_ok)        | humidity_ok      | Count     | RH                | BETWEEN     | 40 AND 60       |
| Liquid Level Drop Alert      | DURATION(level_drop)         | level_drop       | Count     | level             | <           | 20              |
| Rotary Angle In Range        | DURATION(angle_ok)           | angle_ok         | Count     | position          | BETWEEN     | 30 AND 120      |
| Positioning Time at Limit    | DURATION(pos_limit)          | pos_limit        | Count     | position          | >           | 90              |

---

## 🛠 Notes

- Use consistent units and attribute naming aligned with telemetry keys.
- Normalize time-based KPIs into seconds, minutes, or hours in the formula field.
- Values must be literal (e.g., 1, "On", BETWEEN x AND y).

