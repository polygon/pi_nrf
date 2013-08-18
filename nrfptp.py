# Implements a point to point communications link
# Using two nrf24l01+ and Enhanced Shock Burst

import spidev
import RPi.GPIO as gpio
import time

class NrfConfig:
  channel = 2 # 2400 + channel MHz
  rt_delay = 250  # us
  rt_count = 3
  datarate = 2000000 # bps
  tx_pwr = 0  # dBm
  rx_addr = [0x10, 0x10, 0x10, 0x10, 0x10]
  data_len = 12

class PiConfig:
  bus = 0
  chipsel = 0
  cepin = 15

class NrfPtp:
  def __init__(self, nrfconf, piconf):
    self.nrfconf = nrfconf
    self.piconf = piconf

    # Setup raspberry pi and nrf
    self.setup_rpi()
    self.setup_nrf()

  def standby(self):
    gpio.output(self.piconf.cepin, gpio.LOW)
    
  def receive(self):
    gpio.output(self.piconf.cepin, gpio.HIGH)

  def status(self):
    return self.spi.xfer2([0xff])

  # Polls the RX FIFOs and returns the number of data available
  def hasdata(self):
    status = self.spi.xfer2([0x17, 0xff])[1]
    if status & 0x1:
      return False
    return True

  def getdata(self):
    # Save state of CE pin
    cestate = gpio.input(self.piconf.cepin)
    gpio.output(self.piconf.cepin, gpio.LOW)

    data = self.spi.xfer2([0b01100001] + [0xFF]*self.nrfconf.data_len)

    gpio.output(self.piconf.cepin, cestate)
    return data[1:]

  def setup_rpi(self):
    gpio.setmode(gpio.BOARD)
    gpio.setup(self.piconf.cepin, gpio.OUT)
    gpio.output(self.piconf.cepin, gpio.LOW)

    self.spi = spidev.SpiDev(self.piconf.bus, self.piconf.chipsel)

  def setup_nrf(self):
    self.spi.xfer2([0x20, 0b00001011]) # Power on, primary receiver, CRC enabled

    if not (0 <= self.nrfconf.rt_count <= 15):
      raise ValueError('Retransmit count must be between 0 and 15');
    delayval = int(self.nrfconf.rt_delay / 250) - 1
    if not (0 <= delayval <= 15):
      raise ValueError('Retransmit delay must be between 250us and 4000us')
    self.spi.xfer2([0x24, delayval << 4 + self.nrfconf.rt_count])

    if not(0 <= self.nrfconf.channel <= 127):
      raise ValueError('Channel must be between 0 and 127')
    self.spi.xfer2([0x25, self.nrfconf.channel])
    print 'Channel %i' % self.nrfconf.channel

    if self.nrfconf.datarate == 250000:
      dr = 4
    elif self.nrfconf.datarate == 1000000:
      dr = 0
    elif self.nrfconf.datarate == 2000000:
      dr = 1
    else:
      raise ValueError('Datarate must be 250000, 1000000 or 2000000')
    if self.nrfconf.tx_pwr == -18:
      pwr = 0
    elif self.nrfconf.tx_pwr == -12:
      pwr = 1
    elif self.nrfconf.tx_pwr == -6:
      pwr = 2
    elif self.nrfconf.tx_pwr == 0:
      pwr = 3
    else:
      raise ValueError('TX power must be -18, -12, -6 or -0dBm')
    self.spi.xfer2([0x26, (dr << 3) + pwr])
    print 'Pwrsetting %i' % ((dr << 3) + pwr)

    self.spi.xfer2([0x2B] + self.nrfconf.rx_addr)
    print self.nrfconf.rx_addr

    if not(0 <= self.nrfconf.data_len <= 32):
      raise ValueError('Data length must be between 0 and 32')
    self.spi.xfer2([0x32, self.nrfconf.data_len])
    print 'datalen %i' % self.nrfconf.data_len
