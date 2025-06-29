from balor.sender import Sender
import time

pew_time_in_tens_of_µs = 1000

sender = Sender()
sender.open()
sender.set_xy(0x8000, 0x8000)
sender.raw_fiber_open_mo(1,0)

job = sender.job()
#job.raw_fiber_ylpmp_pulse_width(14)
job.set_power(20)
job.raw_q_switch_period(10000)
job.raw_laser_on_point(pew_time_in_tens_of_µs)
job.raw_end_of_list()





try:
    job.execute(1)
    
except KeyboardInterrupt:
    print ("Interrupted.")
sender.raw_fiber_open_mo(0,0)



sender.light_off()
sender.close()
