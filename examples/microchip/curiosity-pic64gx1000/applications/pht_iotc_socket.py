#!/usr/bin/env python3
# pht_iotc_socket.py — Read MS8607 (PHT Click) and send telemetry to IOTCONNECT Snap
import json, socket, time
from smbus2 import SMBus, i2c_msg

BUS = 0
SOCK_TX = "/var/snap/iotconnect/common/iotc.sock"
ADDR_RH, ADDR_PT = 0x40, 0x76
CMD_RH_HOLD, CMD_TEMP_HOLD, CMD_SOFT_RST = 0xE5, 0xE3, 0xFE
ADC_READ, RESET_PT, D1_OSR4096, D2_OSR4096 = 0x00, 0x1E, 0x48, 0x58

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
def t_rh_from_raw(raw): return -46.85 + 175.72 * (raw / 65536.0)

def pt_reset_and_prom():
    with SMBus(BUS) as i2c: i2c.write_byte(ADDR_PT, RESET_PT)
    time.sleep(0.003)
    C = [0]*7
    with SMBus(BUS) as i2c:
        for i, cmd in enumerate([0xA2,0xA4,0xA6,0xA8,0xAA,0xAC], start=1):
            d = i2c.read_i2c_block_data(ADDR_PT, cmd, 2)
            C[i] = (d[0]<<8)|d[1]
    return C

def convert_and_read(cmd):
    with SMBus(BUS) as i2c: i2c.write_byte(ADDR_PT, cmd)
    time.sleep(0.012)
    with SMBus(BUS) as i2c:
        d = i2c.read_i2c_block_data(ADDR_PT, ADC_READ, 3)
    return (d[0]<<16)|(d[1]<<8)|d[2]

def read_ms8607_once(C):
    rrh = read_hold(ADDR_RH, CMD_RH_HOLD)
    rtrh = read_hold(ADDR_RH, CMD_TEMP_HOLD)
    rh_raw = ((rrh[0]<<8)|rrh[1]) & 0xFFFC
    trh_raw = ((rtrh[0]<<8)|rtrh[1]) & 0xFFFC
    rh = round(rh_from_raw(rh_raw), 2)
    t_rh = round(t_rh_from_raw(trh_raw), 2)
    D1 = convert_and_read(D1_OSR4096)
    D2 = convert_and_read(D2_OSR4096)
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
    return round(TEMP/100.0,2), round(P,2), rh, t_rh

def send_iotc(payload):
    wire=json.dumps(payload).encode()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(SOCK_TX); s.sendall(wire); s.shutdown(socket.SHUT_WR)

def main():
    rh_soft_reset(); C=pt_reset_and_prom()
    while True:
        t,p,rh,trh=read_ms8607_once(C)
        payload={"timestamp":int(time.time()),"PHT_temp":t,"PHT_pressure":p,"PHT_humidity":rh,"PHT_die_temp":trh}
        print("TX:",payload); send_iotc(payload); time.sleep(10)

if __name__=="__main__": main()
