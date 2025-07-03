#
# Copyright (c) 2019 - Frederic Mes, RTLOC
# Copyright (c) 2015 - Decawave Ltd, Dublin, Ireland.
# 
# This file is part of Zephyr-DWM1001.
#
#   Zephyr-DWM1001 is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Zephyr-DWM1001 is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Zephyr-DWM1001.  If not, see <https://www.gnu.org/licenses/>.
#
#   ========================================================
#
#   UWB Tag Configuration
#   Double-Sided Two-Way Ranging (DS-TWR) Implementation
#
#   Copyright (c) 2025 SOCCOS
#
#   Author:  Michael Marinovich   marinovich.ml@phystech.edu
#
from Board.components import Transmitter, Receiver, System_info, FrameFiltering, Antena
from Board.config import network_attributes as Net, run_startup_config
from Board.utils import flags as F, data_formaters as df
from Board.utils.types import MAC_message as Message
from Board.utils.const import BROADCAST_ADR, Filter_message_type
from Board.utils.masks import SYS_TIME

from time import sleep_ms

APP_NAME = "DS-TWR Tag"

UUS_TO_DWT_TIME = 65536 # [dwt] ~ 1uus (1 dwt ~ 15.65ps)
FINAL_MSG_TS_LEN = 4 # number of bytes required to encode timestamps

DSTWR_TXRX1 = 1
DSTWR_TXRX3 = 3

# TIMEOUTS
RNG_DELAY_MS = 1000 # [ms] between new message sequence 
POLL_TX_TO_RESP_RX_DLY_UUS = 100 # [uus] between send and start receiving
RESP_RX_TO_FINAL_TX_DLY_UUS = 20000 # [uus] between receive and send in future
RESP_RX_TIMEOUT_UUS = 20000 # [uus] await for response

def main():
    frame_seq_nb = 0
    status_reg = 0

    poll_tx_ts = 0
    resp_rx_ts = 0
    final_tx_ts = 0    
    
    print(APP_NAME)

    # Startup configuration
    run_startup_config()
    # Network
    Net.pan_address = bytes([0x11,0x11])
    Net.source_address = bytes([0x01,0x01])
    FrameFiltering.enable(Filter_message_type.ANY, False)
    # Tx & Rx
    Receiver.set_reception_timeout(RESP_RX_TIMEOUT_UUS)
    Transmitter.set_rx_after_tx_delay(POLL_TX_TO_RESP_RX_DLY_UUS)
    
    tx_msg = Message.build_dummy()

    # Main loop
    while True:
        frame_seq_nb = (frame_seq_nb + 1) & 0xFF # mod 256 = 2 bytes
        
        # TX1 - Send POLL
        tx_msg.seque_num = frame_seq_nb
        tx_msg.set_source(Net.pan_address, Net.source_address)
        tx_msg.set_destination(Net.pan_address, df.int_to_bytes(BROADCAST_ADR))
        tx_msg.payload = bytes([DSTWR_TXRX1])

        Transmitter.set_message_data(tx_msg.assemble())
        
        System_info.clear_status(F.sys_status.RXFCG)
        Transmitter.launch_with_options(F.txrx.START_TX_IMMEDIATE | F.txrx.RESPONSE_EXPECTED)
        status_reg = 0

        # TX1 - await for transmission
        while not (status_reg & F.sys_status.TXFRS):
            status_reg = System_info.get_status()
            continue   
        
        print("[%u]TX1 send - " % frame_seq_nb, end='')
        
        # RX2 - await for response
        while not (status_reg & ( F.sys_status.RXFCG | F.sys_status.ALL_RX_ERR | F.sys_status.ALL_RX_TO)):
            status_reg = System_info.get_status()
            continue
        
        # RX2 - RESP processing
        if status_reg & F.sys_status.RXFCG:
            rx_msg = Message.build_from_rx_buff(Receiver.get_message_data())

            print("[" + str(rx_msg.seque_num) + "]RX2 get - ", end="")
            if rx_msg.seque_num != frame_seq_nb:
                print("Wrong SeqNum.")
                continue

            poll_tx_ts = Transmitter.get_message_sendtime() # TX1 send time
            resp_rx_ts = Receiver.get_message_arrivetime() # RX2 receive time

            final_tx_time = resp_rx_ts + (RESP_RX_TO_FINAL_TX_DLY_UUS * UUS_TO_DWT_TIME)
            final_tx_time &= SYS_TIME
            Transmitter.set_launch_time(final_tx_time) # set TX3 send time

            # TX3 - RESP message
            final_tx_ts = Antena.tx_delay + final_tx_time

            tx_msg.seque_num = frame_seq_nb
            tx_msg.set_destination(Net.pan_address, rx_msg.source_address)
            tx_msg.payload = (
                bytes([DSTWR_TXRX3]) +
                df.int_to_bytes(poll_tx_ts, n=FINAL_MSG_TS_LEN) + 
                df.int_to_bytes(resp_rx_ts, n=FINAL_MSG_TS_LEN) +
                df.int_to_bytes(final_tx_ts, n=FINAL_MSG_TS_LEN))
            
            Transmitter.set_message_data(tx_msg.assemble())
            System_info.clear_status(F.sys_status.TXFRS)
            Transmitter.launch_with_options(F.txrx.START_TX_DELAYED)
            status_reg = 0

            # wait for TX3 to finish
            while not (status_reg & F.sys_status.TXFRS):
                status_reg = System_info.get_status()
                continue
            print("[%u]TX3 send - End." % frame_seq_nb)
        else:
            if status_reg & F.sys_status.RX_AFFREJ: 
                print("RX2 FF Rejection")
            else: 
                print("RX2 timeout")
                
            System_info.clear_status(F.sys_status.ALL_RX_TO | F.sys_status.ALL_RX_ERR)
            Receiver.soft_reset()

        sleep_ms(RNG_DELAY_MS)
        
if __name__ == "__main__":
    main()