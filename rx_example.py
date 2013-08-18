import nrfptp
import time

nrfcnf = nrfptp.NrfConfig()
nrfcnf.datarate = 250000
picnf = nrfptp.PiConfig()
nrf = nrfptp.NrfPtp(nrfcnf, picnf)

nrf.receive()

while True:
  time.sleep(0.1)
  if nrf.hasdata():
    print nrf.getdata()
  print '%0x' % nrf.status()[0]
