# 📊 Smart Asset Monitoring – KPI & Sensor Integration Guide

## Overview
This document explains how to design, configure, and interpret KPIs (Key Performance Indicators) in the **Smart Asset Monitoring Solution**, and how to connect compatible industrial sensors (e.g., Amphenol, TE Connectivity) into the ED-549/BB-400 data acquisition system.  

It is intended for engineers, developers, and operations managers deploying IoTConnect-enabled monitoring across industrial equipment.

---

## 1. KPI Builder

The KPI Builder allows users to **transform raw telemetry data into actionable insights**.  
- Data is aggregated or transformed across configurable windows (Day, Week, Month, Custom).  
- KPIs can be visualized as gauges, line/bar charts, utilization tiles, or numeric readouts.  
- KPIs support **aggregations** (Sum, Count, Min, Max, Average, Latest) and **time-in-state functions** (Duration).  

### Supported Functions

| Function       | Description                                                                 | Example Use Case                          |
|----------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **SUM()**      | Adds up numeric values.                                                     | Total energy consumed (kWh) per shift.    |
| **COUNT()**    | Counts how many telemetry points met a condition.                          | Number of fails per hour.                 |
| **MIN()**      | Finds the lowest recorded value.                                            | Minimum temperature in a cold store.      |
| **MAX()**      | Finds the highest recorded value.                                           | Maximum pump discharge pressure.          |
| **AVERAGE()**  | Calculates the mean of all values.                                          | Average cycle time of a mixer.            |
| **LATEST()**   | Returns the most recent value received.                                     | Latest utilization status of a motor.     |
| **DURATION()** | Returns total time (in seconds) a condition remains true within the window. | Pump run-time per day; Fail time in QA.   |

⚠️ **Note:**  
Operators (Sum, Count, etc.) are **ignored** when used inside `DURATION()`.  
Duration should be interpreted as **time-in-state**, not span (first-to-last).  
If implemented correctly, `DURATION(Pass) + DURATION(Fail) ≈ total runtime`.

---

## 2. KPI Examples by Industry

### 🏭 Manufacturing
- **Machine Utilization Hours**  
  ``` 
  DURATION(machine_status == "Running") / 3600
  ```
- **Downtime Events**  
  ```
  COUNT(machine_status == "Stopped")
  ```
- **Overall Equipment Effectiveness (Availability%)**  
  ``` 
  (DURATION(utilization_status == 1) / Total_Time) * 100
  ```

### ⚡ Energy & Utilities
- **Total Energy Consumption**  
  ``` 
  SUM(energy_kWh)
  ```  
- **Generator Runtime**  
  ``` 
  DURATION(generator_status == "On")
  ```

### 🚚 Logistics & Cold Chain
- **Temperature Compliance**  
  ``` 
  DURATION(temp BETWEEN -1 AND 5)
  ```  
- **Overheat Events**  
  ``` 
  COUNT(temp > 10)
  ```

### 🏥 Healthcare
- **Time in Alarm State**  
  ``` 
  DURATION(alarm_status == "Active")
  ```  
- **Average Room Temperature**  
  ``` 
  AVERAGE(room_temp)
  ```

### 🏗️ Construction / Rental Equipment
- **Engine Runtime**  
  ``` 
  DURATION(engine_status == "On") / 3600
  ```  
- **Idle Fuel Burn**  
  ``` 
  SUM(fuel_rate WHEN engine_status == "Idle")
  ```

---

## 3. Sensor Integration

Industrial sensors provide the **raw telemetry** used to calculate KPIs.  
The ED-549 analog input module accepts:
- **4–20 mA loops** (2-wire current sensors).  
- **±5 V / ±10 V ratiometric voltage sensors**.  
- **Digital I²C/SPI/UART sensors** (with conditioning).  

### Sensor Reference Table (Partial)

| Brand / Division                     | Model / Series               | Measurement Type         | Output      | Supply   | Typical Wiring to ED-549                              | Notes                                   |
|--------------------------------------|------------------------------|--------------------------|-------------|---------|------------------------------------------------------|-----------------------------------------|
| **Amphenol SSI Technologies**        | P51-500-S-A-P-20MA-000-000   | Pressure (500 psi)       | 4–20 mA     | 8–30 VDC | Loop: +24 V → sensor +; sensor – → AInX+; AInX– → 0V | Current loop, Packard connector.        |
| **Amphenol SSI Technologies**        | P51-75-A-B-P-4.5V-000-000    | Pressure (75 psi)        | 0.5–4.5 V   | 5 VDC    | OUT → AInX+; GND → AInX– (±5 V channel)              | Ratiometric voltage output.             |
| **Amphenol Wilcoxon**                | PC420VR-10                   | Vibration (velocity RMS) | 4–20 mA     | 24 VDC   | Loop: +24 V → sensor +; sensor – → AInX+; AInX– → 0V | 1 ips full scale.                       |
| **Amphenol Advanced Sensors (Telaire)** | HUMI-DP-XR-D                 | RH/Temp (duct)           | 0–10 V / 4–20 mA | 12–30 VDC | Voltage OUT → AInX+; GND → AInX–; or loop 4–20 mA | Humidity & temperature in HVAC ducts.   |
| **Amphenol Piher Sensing**           | PST360G2 / PST360G21         | Rotary position          | 0.5–4.5 V   | 5–15 VDC | OUT → AInX+; GND → AInX– (±5 V or ±10 V channel)     | Non-contact hall rotary sensors.        |
| **TE Connectivity (Measurement Spec.)** | AST4520                    | Level (submersible)      | 4–20 mA     | 10–28 V  | Loop + → AInX+; return → AInX–; channel 4–20 mA     | Tank/well liquid level monitoring.      |
| **TE Connectivity (Celesco)**        | IT9420                       | Inclinometer (tilt)      | 4–20 mA     | 12–30 V  | Loop + → AInX+; return → AInX–; channel 4–20 mA     | Rugged inclinometer, damped pendulum.   |
| **TE Connectivity (Celesco)**        | SG Series String Pot         | Linear position          | 4–20 mA or 0–10 V | 12–30 V | Current: loop → AInX; Voltage: OUT → AInX+; GND → AInX– | Motion tracking, cranes, hoists.        |

*(Full table available in reference spreadsheet.)*

---

## 4. Mapping Sensors to KPIs

| Sensor Type       | Example Sensor                  | Typical KPI                                |
|-------------------|---------------------------------|--------------------------------------------|
| Pressure          | Amphenol P51 / TE AST4000       | MAX(pressure) for safety alarms; DURATION(pressure > threshold) |
| Vibration         | Amphenol Wilcoxon PC420 series  | AVERAGE(vibration) for machine health; COUNT(vibration > limit) |
| Temperature/RH    | Telaire HUMI-DP-XR-D            | DURATION(temp in compliance band); MIN(RH) |
| Position (linear/rotary) | Piher PST360 / SG String Pot | AVERAGE(position); DURATION(position == "operating zone") |
| Level / Submersible | TE AST4520                    | SUM(level_change) for usage; MAX(level)    |
| Tilt/Rotation     | Celesco IT9420                  | DURATION(tilt within safe band)            |

---

## 5. Best Practices
- Always align **sensor output type** (current loop vs voltage) with the **ED-549 channel mode**.  
- For **I²C digital sensors** (e.g., NovaSensor NPA-730), add DAC/conditioner if analog input is required.  
- Configure KPIs close to operational metrics:
  - **Operators want hours, %, or compliance time**, not raw counts.  
  - Use DURATION() for utilization, SUM() for consumption, MAX/MIN for safety limits.  

---

## Summary
- The KPI Builder enables turning raw telemetry into actionable insights.  
- Aggregation functions (Sum, Count, Avg, etc.) summarize numeric signals.  
- `DURATION()` measures **time-in-state**, critical for utilization and compliance metrics.  
- A wide range of industrial sensors (Amphenol, TE, Wilcoxon, etc.) connect to ED-549 to feed telemetry.  
- Proper mapping from **sensor → telemetry → KPI** delivers meaningful dashboards for manufacturing, energy, logistics, healthcare, and construction.

