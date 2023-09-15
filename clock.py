# dirty, but it actually works pretty well
# this variable is shared between cpu (producer), speaker and paddle (consumers)
# to provide a way to measure a duration between two events
# the delta between two value is the number of clock cycles that were elapsed.

ticks = 0



# added for fun : change at your will
# the original cpu frequency of the APPLE II is 1023000 Hz

CPU_FREQUENCY = 1023000
