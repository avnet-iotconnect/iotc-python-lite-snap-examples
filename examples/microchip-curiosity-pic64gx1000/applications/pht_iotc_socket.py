#!/usr/bin/env python3
# pht_iotc_socket.py — Read MS8607 (PHT Click) and send telemetry to IOTCONNECT Snap
#
# Environment overrides (used by the systemd unit in ../systemd):
#   IOTC_SOCK     telemetry socket path (default /var/snap/iotconnect/common/iotc.sock)
#   PHT_I2C_BUS   I2C bus number for the mikroBUS socket in use (default 0)
#   PHT_INTERVAL  seconds between samples (default 10)
import json, os, select, socket, threading, time
from smbus2 import SMBus, i2c_msg

BUS = int(os.environ.get("PHT_I2C_BUS", "0"))
SOCK_TX = os.environ.get("IOTC_SOCK", "/var/snap/iotconnect/common/iotc.sock")
SOCK_RX = os.environ.get("IOTC_CMD_SOCK", "/var/snap/iotconnect/common/iotc_cmd.sock")
PERIOD = float(os.environ.get("PHT_INTERVAL", "10"))
ADDR_RH, ADDR_PT = 0x40, 0x76
CMD_RH_HOLD, CMD_SOFT_RST = 0xE5, 0xFE
ADC_READ, RESET_PT = 0x00, 0x1E

# MS8607 pressure-die oversampling. Higher OSR averages more ADC samples: about
# sqrt(2) less noise and twice the conversion time per step. The wait must clear
# the datasheet maximum conversion time or the previous result is read back.
OSR_TABLE = {                 # osr: (D1 cmd, D2 cmd, conversion wait)
     256: (0x40, 0x50, 0.002),
     512: (0x42, 0x52, 0.003),
    1024: (0x44, 0x54, 0.004),
    2048: (0x46, 0x56, 0.006),
    4096: (0x48, 0x58, 0.012),
}
DEFAULT_OSR = int(os.environ.get("PHT_OSR", "4096"))

_state = {"osr": DEFAULT_OSR if DEFAULT_OSR in OSR_TABLE else 4096}
_state_lock = threading.Lock()

def rh_soft_reset():
    try:
        with SMBus(BUS) as i2c:
            i2c.write_byte(ADDR_RH, CMD_SOFT_RST)
    except OSError:
        pass
    time.sleep(0.02)

def read_hold(addr, cmd, n=3):
    with SMBus(BUS) as bus:
        msgs = [i2c_msg.write(addr, [cmd]), i2c_msg.read(addr, n)]
        bus.i2c_rdwr(*msgs)
        return list(msgs[1])

def rh_from_raw(raw): return -6.0 + 125.0 * (raw / 65536.0)

def pt_reset_and_prom():
    with SMBus(BUS) as i2c: i2c.write_byte(ADDR_PT, RESET_PT)
    time.sleep(0.003)
    C = [0]*7
    with SMBus(BUS) as i2c:
        for i, cmd in enumerate([0xA2,0xA4,0xA6,0xA8,0xAA,0xAC], start=1):
            d = i2c.read_i2c_block_data(ADDR_PT, cmd, 2)
            C[i] = (d[0]<<8)|d[1]
    return C

def convert_and_read(cmd, wait):
    with SMBus(BUS) as i2c: i2c.write_byte(ADDR_PT, cmd)
    time.sleep(wait)
    with SMBus(BUS) as i2c:
        d = i2c.read_i2c_block_data(ADDR_PT, ADC_READ, 3)
    return (d[0]<<16)|(d[1]<<8)|d[2]

def read_ms8607_once(C, osr):
    d1_cmd, d2_cmd, wait = OSR_TABLE[osr]
    rrh = read_hold(ADDR_RH, CMD_RH_HOLD)
    rh_raw = ((rrh[0]<<8)|rrh[1]) & 0xFFFC
    rh = round(rh_from_raw(rh_raw), 2)
    D1 = convert_and_read(d1_cmd, wait)
    D2 = convert_and_read(d2_cmd, wait)
    dT = D2 - C[5]*256
    TEMP = 2000 + (dT*C[6]) / 8388608.0
    OFF = C[2]*131072.0 + (C[4]*dT)/64.0
    SENS = C[1]*65536.0 + (C[3]*dT)/128.0
    if TEMP < 2000:
        T2=(dT*dT)/2147483648.0; OFF2=5*((TEMP-2000)**2)/2; SENS2=5*((TEMP-2000)**2)/4
        if TEMP < -1500:
            OFF2+=7*((TEMP+1500)**2); SENS2+=11*((TEMP+1500)**2)/2
        TEMP-=T2; OFF-=OFF2; SENS-=SENS2
    else: TEMP-=(dT*dT)/137438953472.0
    P=(((D1*SENS)/2097152.0)-OFF)/32768.0
    # TEMP is in 0.01 C and P is in 0.01 mbar, so both are scaled to C and hPa.
    # The MS8607 humidity die has no temperature command (0xE3 returns zeros on
    # this part, unlike the HTU21 it resembles), so the pressure die is the only
    # temperature source and PHT_die_temp mirrors PHT_temp.
    t = round(TEMP/100.0, 2)
    return t, round(P/100.0, 2), rh, t

def send_iotc(payload):
    # The bridge may not be up yet at boot, and it recreates its sockets on
    # restart. Treat both as transient so the service keeps sampling.
    wire=json.dumps(payload).encode()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(SOCK_TX); s.sendall(wire); s.shutdown(socket.SHUT_WR)
        return True
    except OSError as e:
        print(f"[TX] {SOCK_TX}: {e}")
        return False

def init_sensor():
    # Retry rather than exit, so the service survives a Click board that is
    # seated late or an I2C bus that appears after this unit starts.
    while True:
        try:
            rh_soft_reset()
            return pt_reset_and_prom()
        except OSError as e:
            print(f"[I2C] bus {BUS}: {e}; retrying in 5s")
            time.sleep(5.0)

def apply_osr(value):
    try:
        osr = int(float(value))
    except (TypeError, ValueError):
        return False, f"osr must be one of {sorted(OSR_TABLE)}"
    if osr not in OSR_TABLE:
        return False, f"osr must be one of {sorted(OSR_TABLE)}"
    with _state_lock:
        _state["osr"] = osr
    print(f"[CMD] osr -> {osr} (applied)")
    return True, ""

def command_loop():
    # Read-only listener. Every connected client sees every command, so anything
    # that is not ours is ignored quietly.
    decoder = json.JSONDecoder()
    while True:
        s = None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(SOCK_RX)
            buf = ""
            while True:
                if not select.select([s], [], [], 60.0)[0]:
                    continue
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="ignore")
                while buf.strip():
                    try:
                        msg, end = decoder.raw_decode(buf.strip())
                    except ValueError:
                        break
                    buf = buf.strip()[end:]
                    if not isinstance(msg, dict):
                        continue
                    name = str(msg.get("name", "")).strip().lower()
                    args = msg.get("args")
                    if isinstance(args, (list, tuple)):
                        args = args[0] if args else None
                    if name == "osr":
                        ok, err = apply_osr(args)
                        if msg.get("ack_id"):
                            send_iotc({"ack": msg["ack_id"], "status": "success" if ok else "error",
                                       "message": err, "ts": int(time.time())})
        except OSError as e:
            print(f"[CMD] {SOCK_RX}: {e}; retrying in 2s")
            time.sleep(2.0)
        finally:
            if s:
                try: s.close()
                except OSError: pass

def main():
    C=init_sensor()
    threading.Thread(target=command_loop, daemon=True).start()
    print(f"[PHT] bus={BUS} interval={PERIOD}s osr={_state['osr']} tx={SOCK_TX}")
    while True:
        with _state_lock:
            osr = _state["osr"]
        try:
            t,p,rh,trh=read_ms8607_once(C, osr)
        except OSError as e:
            print(f"[I2C] read failed: {e}; re-initialising")
            C=init_sensor(); continue
        payload={"timestamp":int(time.time()),"PHT_temp":t,"PHT_pressure":p,"PHT_humidity":rh,"PHT_die_temp":trh,"osr":osr}
        print("TX:",payload); send_iotc(payload); time.sleep(PERIOD)

if __name__=="__main__": main()
