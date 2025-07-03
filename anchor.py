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
#   UWB Anchor Configuration
#   Double-Sided Two-Way Ranging (DS-TWR) Implementation
#
#   Copyright (c) 2025 SOCCOS
#
#   Author:  Michael Marinovich   marinovich.ml@phystech.edu
#
from Board.components import Transmitter, Receiver, System_info, FrameFiltering
from Board.utils import flags as F, data_formaters as df
from Board.config import run_startup_config, network_attributes as Net
from Board.utils.types import MAC_message as Message
from Board.utils.const import Filter_message_type

APP_NAME = "DS-TWR Anchor"
SPEED_OF_LIGHT = 299702547  # m/s
UUS_TO_DWT_TIME = 65536  # [dwt] ~ 1uus (1 dwt ~ 15.65ps)

DSTWR_TXRX1 = 1
DSTWR_TXRX3 = 3

FINAL_MSG_POLL_TX_TS_IDX = 1
FINAL_MSG_RESP_RX_TS_IDX = 5
FINAL_MSG_FINAL_TX_TS_IDX = 9
FINAL_MSG_TS_LEN = 4  # number of bytes required to encode timestamps

# TIMEOUTS
RESP_TX_TO_FINAL_RX_DLY_UUS = 300  # [uus] between send and start receiving
FINAL_RX_TIMEOUT_UUS = 20000  # [uus] await for response


def main():
    frame_seq_nb = 0
    status_reg = 0

    poll_rx_ts = 0
    resp_tx_ts = 0
    final_rx_ts = 0

    print(APP_NAME)

    # Startup configuration
    run_startup_config()
    # Network
    Net.pan_address = bytes([0x11, 0x11])
    Net.source_address = bytes([0x02, 0x02])
    FrameFiltering.enable(Filter_message_type.ANY, True)
    # Tx & Rx
    Transmitter.set_rx_after_tx_delay(RESP_TX_TO_FINAL_RX_DLY_UUS)

    while True:
        # RX1 - Lissten for POLL
        Receiver.set_reception_timeout(0)
        Receiver.launch()
        status_reg = 0

        # RX1 - POLL processing
        while not (status_reg & (F.sys_status.RXFCG | F.sys_status.ALL_RX_TO | F.sys_status.ALL_RX_ERR)):
            status_reg = System_info.get_status()
            continue

        if status_reg & F.sys_status.RXFCG:
            rx_msg = Message.build_from_rx_buff(Receiver.get_message_data())

            print("[" + str(rx_msg.seque_num) + "]RX1 get - ", end="")
            if rx_msg.payload[0] != DSTWR_TXRX1:
                print("Code Error.")
                continue
            frame_seq_nb = rx_msg.seque_num

            # RX3 timeout
            Receiver.set_reception_timeout(FINAL_RX_TIMEOUT_UUS)

            # TX2 - POLL response
            tx_msg = Message.build_dummy()
            tx_msg.seque_num = frame_seq_nb
            tx_msg.set_destination(Net.pan_address, rx_msg.source_address)
            tx_msg.set_source(Net.pan_address, Net.source_address)

            Transmitter.set_message_data(tx_msg.assemble())
            System_info.clear_status(F.sys_status.RXFCG)
            Transmitter.launch_with_options(F.txrx.START_TX_IMMEDIATE | F.txrx.RESPONSE_EXPECTED)
            status_reg = 0

            poll_rx_ts = Receiver.get_message_arrivetime()

            # wait for TX2 to finish
            while not (status_reg & F.sys_status.TXFRS):
                status_reg = System_info.get_status()
                continue
            print("[%u]TX2 send - " % frame_seq_nb, end='')

            # RX3 - FINAL
            while not (status_reg & (F.sys_status.RXFCG | F.sys_status.ALL_RX_TO | F.sys_status.ALL_RX_ERR)):
                status_reg = System_info.get_status()
                continue

            if status_reg & F.sys_status.RXFCG:
                rx_msg = Message.build_from_rx_buff(Receiver.get_message_data())

                print("[" + str(rx_msg.seque_num) + "]RX3 get - ", end="")
                if rx_msg.payload[0] != DSTWR_TXRX3:
                    print("Code Error.")
                    continue
                if rx_msg.seque_num != frame_seq_nb:
                    print("Wrong SeqNum.")
                    continue

                # getting TX2 and RX3 time
                resp_tx_ts = Transmitter.get_message_sendtime()
                final_rx_ts = Receiver.get_message_arrivetime()

                # getting TX1, RX2 and TX3 time, sended from the Tag
                poll_tx_ts = df.bytes_to_int(
                    rx_msg.payload[FINAL_MSG_POLL_TX_TS_IDX:FINAL_MSG_POLL_TX_TS_IDX + FINAL_MSG_TS_LEN])
                resp_rx_ts = df.bytes_to_int(
                    rx_msg.payload[FINAL_MSG_RESP_RX_TS_IDX:FINAL_MSG_RESP_RX_TS_IDX + FINAL_MSG_TS_LEN])
                final_tx_ts = df.bytes_to_int(
                    rx_msg.payload[FINAL_MSG_FINAL_TX_TS_IDX:FINAL_MSG_FINAL_TX_TS_IDX + FINAL_MSG_TS_LEN])

                # Calculate the time of flight
                Ra = resp_rx_ts - poll_tx_ts
                Rb = final_rx_ts - resp_tx_ts
                Da = final_tx_ts - resp_rx_ts
                Db = resp_tx_ts - poll_rx_ts

                # Parse to uint32
                Ra &= 0xFFFFFFFF
                Rb &= 0xFFFFFFFF
                Da &= 0xFFFFFFFF
                Db &= 0xFFFFFFFF

                tof_dtu = (Ra * Rb - Da * Db) / (Ra + Rb + Da + Db)

                tof = tof_dtu / 1e3 / UUS_TO_DWT_TIME
                distance = tof * SPEED_OF_LIGHT

                print("Distance:%d mm\n" % int(distance))
            else:
                if status_reg & F.sys_status.RX_AFFREJ:
                    print("RX3 FF Rejection")
                else:
                    print("RX3 timeout")
                System_info.clear_status(F.sys_status.ALL_RX_TO | F.sys_status.ALL_RX_ERR)
                Receiver.soft_reset()
        else:
            if status_reg & F.sys_status.RX_AFFREJ:
                print("RX1 FF Rejection")
            else:
                print("RX1 timeout")
            System_info.clear_status(F.sys_status.ALL_RX_TO | F.sys_status.ALL_RX_ERR)
            Receiver.soft_reset()


if __name__ == "__main__":
    main()