station.awg.stop()
station.awg.ch1_state(0)
station.awg.ch2_state(0)
station.awg.ch3_state(0)
station.awg.ch4_state(0)
station.psg.off()

print('Pulse stopped and Chs 1, 2, 3 OFF')
