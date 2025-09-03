# IOTCONNECT Smart Asset Monitoring
# KPI and Sensor Implementation Guide (Consolidated)

This guide explains how to configure and interpret Key Performance Indicators (KPIs) in the Smart Asset Monitoring application and how to integrate common industrial sensors with the ED 549/BB 400 data acquisition system. It is written for engineers and operators who are connecting hardware to the platform and need to build meaningful dashboards. 

---

## Table of Contents
1. Audience and Scope
2. Platform Overview and Key Features
3. Quick Start: Hardware and Connectivity
4. Designing Device Templates for KPIs
5. KPI Builder: Concepts and Workflow
6. KPI Formula Modes (General vs. Duration-Only)
7. Worked Examples
8. Dashboards: Building KPI-First Views
9. Rules and Alerts
10. Maintenance and Asset Lifecycle
11. Sensor Integration and KPI Mapping
12. Industrial Use Cases and Reference KPIs
13. Troubleshooting and Best Practices
14. Appendix A: Duration-Only KPI Patterns
15. Appendix B: BB-400 Quick Reference

---

## 1) Audience and Scope
This guide is for admins, engineers, and operations users who configure device templates, create KPIs, and compose dashboards in the Smart Asset Monitoring application. It explains how to translate raw telemetry into business metrics, then operationalize those metrics with dashboards, rules, and maintenance.

---

## 2) Platform Overview and Key Features
Smart Asset Monitoring provides role-based access to the following modules: Locations and Zones, Templates, Assets, KPI management, Rules and Alerts, Maintenance, Roles and Users, and Dashboards.

Key capabilities for KPI solutions include:
- Centralized KPI Builder (counter or chart) with time aggregation for Day, Week, Month, and Year. Data is typically stored every 5 minutes and rolled up by the selected chart frequency.
- Custom dashboards with drag-and-drop KPI widgets, charts, alert panels, and location statistics, with color, size, and typography customization and drill-downs.
- Rules and alerts on attributes and states, including device-disconnect policies, audiences, and severity levels.

---

## 3) Quick Start: Hardware and Connectivity
**BB-400 gateway (Brainboxes, CM3+, armhf)**

Install the IOTCONNECT snap, then run a hello-telemetry example to verify end-to-end data flow:

```bash
sudo snap install iotconnect
iotconnect.setup
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```

If the IOTCONNECT socket path differs, set:
```bash
export IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock
```

Use this platform with the ED-549 analog input module for 4-20 mA and +/-5 V or +/-10 V sensors referenced later in this guide.

---

## 4) Designing Device Templates for KPIs
Before you build KPIs, ensure Device Templates contain the attributes your math needs (for example, pressure, vibration, temperature, heartbeat). In the template, define attribute data types, units, and optional color codes for visualization; use Shadow for configurables (setpoints) and Commands for remote actions (including OTA flags).

Template authoring checklist:
- Attribute names match planned KPI parameter names (case-sensitive).
- Include status or enum fields where your KPIs count events (for example, machine_status, alarm_status).
- Capture sampling frequency in template properties to align with KPI rollups.

---

## 5) KPI Builder: Concepts and Workflow
A KPI transforms raw telemetry into a metric such as uptime percent, average pressure, or time-in-compliance. KPIs are either Counters (single value) or Charts (trend).

Authoring flow:
1. Name your KPI clearly (for example, Compressor Vibration Max).
2. Formula. Enter a mathematical expression using your parameter names (details below).
3. Device Template. Select the source template; this determines available attributes.
4. Type and Widget. Choose Counter or Chart; for charts, select Line, Bar, or Column and a frequency (Day, Week, Month, Year). Data ingests every 5 minutes; frequency controls aggregation intervals in the chart.
5. Define Parameters for each variable referenced in your formula:
   - Parameter Name: must match the formula exactly.
   - Operation: SUM, AVERAGE, COUNT, MIN, MAX, LATEST (and DURATION where available).
   - Template Attribute: for example, pressure, heartbeat, vibration.
   - Comparison Operator or Value: optional filter such as >, <, ==, >=, <=, !=, or BETWEEN.
6. Save and add the KPI to dashboards.

Notes and tips:
- Align parameter names with telemetry fields; prefer descriptive names like pressure_avg or fail_count.
- Use LATEST for stateful flags or setpoints, MIN or MAX for safety bounds, AVERAGE or SUM for utilization or consumption.

---

## 6) KPI Formula Modes (General vs. Duration-Only)
Two authoring styles exist across deployments:

1. General Formula Mode: The formula field accepts arithmetic expressions (for example, (p1 * 100) / p2 or SUM(p1)). Use any mix of SUM, AVERAGE, COUNT, MIN, MAX, and LATEST in parameters and reference them in the formula.

2. Duration-Only Mode: The formula field only permits DURATION(condition), which measures time-in-state. All other aggregation (for example, COUNT, SUM) is expressed as parameter filters, and time normalization (for example, / 60, / 3600) is done in the formula after DURATION(...). Operators are ignored inside DURATION(); treat it as seconds in state.

If you are unsure which mode your environment uses, try creating a simple non-duration expression. If validation fails, follow the Duration-Only patterns in Appendix A.

---

## 7) Worked Examples

### Example 1: Uptime Percent
Concept: Devices emit a heartbeat every N seconds. A scheduled job computes 5-minute availability.

Formula (general mode):
```
((Heartbeat * HeartbeatInterval) / HeartbeatDuration) * 100
```

Parameters:
- Heartbeat -> COUNT on attribute heartbeat
- HeartbeatInterval -> LATEST on heartbeat_interval (seconds)
- HeartbeatDuration -> CONSTANT = 300 (5 minutes)

Interpretation: If a device misses 3 heartbeats in a 5-minute window with a 30-second interval, Heartbeat = 7 and uptime is 70 percent.

Duration-only variant: Use a boolean or flag attribute to represent online, then compute:
```
DURATION(online_flag == 1) / 300 * 100
```

### Example 2: Temperature Compliance (Cold Chain)
General:
```
DURATION(temp BETWEEN -1 AND 5) / 60
```
Result: Minutes in range per aggregation window.

### Example 3: Vibration Health
- vibration_max parameter using MAX over vibration; display as Counter or Line chart.
- Add COUNT(vibration > limit) to track event frequency.
- For 4-20 mA vibration loops, set channel mode to 4-20 mA and ensure adequate loop supply (for example, 12-30 V).

### Example 4: Pressure Overshoot Time
```
DURATION(pressure > threshold)
```
Accumulates seconds above limit; chart by Day for QA audits.

### Example 5: Utilization Hours
```
DURATION(machine_status == "Running") / 3600
```

---

## 8) Dashboards: Building KPI-First Views
Use "Try New Dashboard" to compose a KPI-first view: drag KPIs, alerts, and charts; customize colors, type, and fonts; and enable drill-downs. Keep layouts responsive, focus on the few metrics that drive action, and add filters for time ranges and asset groups.

Widget guidance:
- Counters for headline numbers (uptime percent, hours run, events).
- Lines for trends vs. time; Bars or Columns for category comparisons.
- Integrate alerts panes and upcoming maintenance lists to close the loop from insight to action.

---

## 9) Rules and Alerts
Create Standard or Smart rules (and device-disconnect policies) on template attributes and states. Set severity, audiences (roles and users), and alert channels. Use rules to notify when KPIs breach limits (for example, high vibration, temperature out-of-range, extended disconnect).

---

## 10) Maintenance and Asset Lifecycle
Schedule and track maintenance per asset; surface upcoming maintenance on dashboards. Combine condition-based rules (for example, DURATION(vibration > limit)) with run-time counters to move from time-based to condition-based maintenance.

---

## 11) Sensor Integration and KPI Mapping

### Supported signal types
- 4-20 mA loops (2-wire). Typical wiring: +24 V -> sensor +; sensor - -> AInX+; AInX- -> 0 V; channel mode: 4-20 mA.
- Ratiometric voltage (0.5-4.5 V), 0-10 V. Typical wiring: OUT -> AInX+; GND -> AInX-; channel mode: +/-5 V or +/-10 V.
- Digital sensors (I2C or SPI): route via a microcontroller or DAC if your input module is analog-only.

### Representative sensor to KPI map
| Brand | Model | Measure | Output | Typical KPIs |
|---|---|---|---|---|
| Amphenol SSI | P51-500-S-A-P-20MA-000-000 | Pressure | 4-20 mA | MAX(pressure), AVERAGE(pressure), DURATION(pressure > limit) |
| Amphenol SSI | P51-75-A-B-P-4.5V-000-000 | Pressure | 0.5-4.5 V | Same KPIs; configure +/-5 V channel. |
| Wilcoxon | PC420VR-10 / PC420VP-20 | Vibration | 4-20 mA | MAX(vibration), COUNT(vibration > limit). Ensure 12-30 V loop supply. |
| Telaire | HUMI-DP-XR-D / EHRH-2-I-F | RH and Temperature | 0-10 V or 4-20 mA | DURATION(temp in band), MIN and MAX for RH. |
| Piher | PST360 G2 or G21 | Rotary position | 0.5-4.5 V | AVERAGE(position), COUNT(position > angle). |
| TE | AST4000 | Pressure | 4-20 mA or voltage | Same pressure KPIs; select matching channel mode. |
| TE | M3200 | Pressure | 4-20 mA or 0-10 V or 0.5-4.5 V | Pressure KPIs; wire per output type. |
| TE | AST4520 | Level (submersible) | 4-20 mA | MIN and MAX(level), DURATION(level < lowLimit). |
| TE (Celesco) | IT9420 | Tilt | 4-20 mA | MAX(abs(tilt)), DURATION(abs(tilt) > warn). |
| TE (Celesco) | SG series string pot | Linear position | 4-20 mA or 0-10 V | Utilization or position-in-zone durations. |

Wiring tips:
- Match input mode to sensor type.
- Use shielded cable for low-level voltages.
- Ensure loop supply headroom through input resistance.
- Avoid ground loops.
- Translate I2C or SPI to analog if needed.

---

## 12) Industrial Use Cases and Reference KPIs
A sample plant with eight asset types illustrates telemetry to KPI to dashboard flow. For each asset, define parameters and a simple formula, then add to a trend dashboard.

| Asset Type | Example KPI | Formula | Parameter -> (Operation, Attribute) |
|---|---|---|---|
| Process Pump | Avg Discharge Pressure | pressure_avg | pressure_avg -> (AVERAGE, pressure) |
| Air Compressor | Max Vibration | vibration_max | vibration_max -> (MAX, vibration) |
| Mixing Vessel | Min Level | level_min | level_min -> (MIN, level) |
| Storage Tank | Max Tilt | tilt_max | tilt_max -> (MAX, tilt) |
| Cooling or Chiller | Condenser Pressure Avg | condenser_pressure_avg | (AVERAGE, pressure) |
| Boiler or Heat Exchanger | Steam Pressure Avg | steam_pressure_avg | (AVERAGE, pressure) |
| Conveyor System | Gearbox Vibration Max | conveyor_vibration_max | (MAX, vibration) |
| Crane or AGV | Hoist Position Avg | hoist_position_avg | (AVERAGE, position) |

Add counters for headline KPIs and lines for time trends; configure rules for breach notifications (for example, vibration over limit).

---

## 13) Troubleshooting and Best Practices

Authoring
- Use descriptive names; keep parameter names consistent across related KPIs.
- Validate that formulas match defined parameters exactly (case-sensitive).
- In duration-only environments, remember: DURATION() measures time-in-state; operators inside are ignored. Normalize to minutes or hours in the formula.

Sensors
- Confirm channel mode (4-20 mA vs. voltage) per sensor.
- Check supply headroom for current loops.
- Use twisted and shielded pairs for low-level voltages.
- Avoid ground loops.

Dashboards
- Keep layouts focused; avoid too many widgets.
- Use filters and drill-downs for detail.
- Test across devices.

---

## 14) Appendix A: Duration-Only KPI Patterns
Use these patterns when your tenant restricts the formula field to DURATION(condition) and prohibits arbitrary arithmetic across parameters. Build semantics via conditions and then normalize time units in the formula (for example, divide by 60 or 3600).

| KPI | Formula (Duration Mode) | Parameter (Operation, Attribute, Condition) |
|---|---|---|
| Machine Utilization (hours) | DURATION(machine_on) / 3600 | machine_on -> (COUNT, machine_status, == "Running") |
| Downtime Events | DURATION(downtime_trigger) | downtime_trigger -> (COUNT, machine_status, == "Stopped") |
| Availability (percent) | DURATION(available) | available -> (COUNT, utilization_status, == 1) |
| Energy Use (kWh) | DURATION(energy_detected) | energy_detected -> (SUM, energy_kWh, > 0) |
| Generator Runtime (minutes) | DURATION(generator_on) / 60 | generator_on -> (COUNT, generator_status, == "On") |
| Temperature Compliance (minutes) | DURATION(in_range) / 60 | in_range -> (COUNT, temp, BETWEEN -1 AND 5) |
| Overheat Events | DURATION(overheat) | overheat -> (COUNT, temp, > 10) |
| Alarm Active Time (minutes) | DURATION(alarm_active) / 60 | alarm_active -> (COUNT, alarm_status, == "Active") |
| Tilt Within Safe Range | DURATION(safe_tilt) | safe_tilt -> (COUNT, tilt, BETWEEN -10 AND 10) |
| Max Pressure Breach Time | DURATION(high_pressure) | high_pressure -> (COUNT, pressure, > 75) |
| Vibration Alert Duration | DURATION(vibration_alert) | vibration_alert -> (COUNT, vibration, > 1.0) |

Tip: For availability percentage, divide DURATION(running) by the window length (Total_Time) and multiply by 100 in your charting or reporting layer if the formula field does not allow additional arithmetic.

---

## 15) Appendix B: BB-400 Quick Reference
- Install: `sudo snap install iotconnect` then `iotconnect.setup`
- Socket path override: `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`
- Smoke test: `python3 ../../examples/00-hello-telemetry/hello_telemetry.py`
- Pair with ED-549 for analog inputs feeding KPI telemetry (pressure, vibration, RH and temperature, level, position).

---
