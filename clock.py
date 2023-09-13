# dirty, but it actually works pretty well

# this variable is shared between cpu (producer), speaker and paddle (consumers)
# to provide a way to measure a duration between two events
# the delta between two value is the number of clock cycles that were elapsed.

global ticks
ticks = 0