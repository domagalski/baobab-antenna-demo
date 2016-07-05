#!/usr/bin/env python
'''
This script demonstrates grabbing data from a wideband Pocket correlator and
plotting it using numpy/pylab. Designed for use with CASPER workshop Tutorial 4.
\n\n
Author: Jason Manley, August 2009.
Modified: Aug 2012, Nie Jun; April 2016, Rachel Simone Domagalski
'''

#TODO: add support for coarse delay change
#TODO: add support for ADC histogram plotting.
#TODO: add support for determining ADC input level

import corr,time,numpy,struct,sys,logging,pylab,matplotlib
from matplotlib.colors import LogNorm

katcp_port=7147

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def get_data(baseline):

    acc_n = fpga.read_uint('acc_num')
    #print 'Grabbing integration number %i'%acc_n

    #get the data...
    a_0r=struct.unpack('>512l',fpga.read('dir_x0_%s_real'%baseline,2048,0))
    a_1r=struct.unpack('>512l',fpga.read('dir_x1_%s_real'%baseline,2048,0))
    b_0r=struct.unpack('>512l',fpga.read('dir_x0_%s_real'%baseline,2048,0))
    b_1r=struct.unpack('>512l',fpga.read('dir_x1_%s_real'%baseline,2048,0))
    a_0i=struct.unpack('>512l',fpga.read('dir_x0_%s_imag'%baseline,2048,0))
    a_1i=struct.unpack('>512l',fpga.read('dir_x1_%s_imag'%baseline,2048,0))
    b_0i=struct.unpack('>512l',fpga.read('dir_x0_%s_imag'%baseline,2048,0))
    b_1i=struct.unpack('>512l',fpga.read('dir_x1_%s_imag'%baseline,2048,0))

    interleave_a=[]
    interleave_b=[]

    for i in range(512):
        interleave_a.append(complex(a_0r[i], a_0i[i]))
        interleave_a.append(complex(a_1r[i], a_1i[i]))
        interleave_b.append(complex(b_0r[i], b_0i[i]))
        interleave_b.append(complex(b_1r[i], b_1i[i]))

    return acc_n,interleave_a,interleave_b


def drawDataCallback(baseline):
    matplotlib.pyplot.clf()
    acc_n,interleave_a,interleave_b = get_data(baseline)

    matplotlib.pyplot.subplot(121)
    if ifch == True:
        #matplotlib.pyplot.semilogy(numpy.abs(interleave_a))
        matplotlib.pyplot.plot(numpy.abs(interleave_a))
        matplotlib.pyplot.xlim(0,1024)
    else:
        #matplotlib.pyplot.semilogy(xaxis,numpy.abs(interleave_a))
        matplotlib.pyplot.plot(xaxis,numpy.abs(interleave_a))
    matplotlib.pyplot.grid()
    #matplotlib.pyplot.title('Integration number %i \n%s'%(acc_n,baseline))
    matplotlib.pyplot.ylabel('Power (arbitrary units)')
    matplotlib.pyplot.yscale('log')

    matplotlib.pyplot.subplot(122)
    if ifch == True:
        matplotlib.pyplot.plot(numpy.unwrap(numpy.angle(interleave_b)))
        matplotlib.pyplot.xlim(0,1024)
        matplotlib.pyplot.xlabel('FFT Channel')
    else:
        matplotlib.pyplot.plot(xaxis,(numpy.angle(interleave_b)))
        matplotlib.pyplot.xlabel('FFT Frequency')
    matplotlib.pyplot.ylabel('Phase')
    matplotlib.pyplot.ylim(-numpy.pi,numpy.pi)
    matplotlib.pyplot.grid()

    matplotlib.pyplot.tight_layout()
    fig.canvas.draw()
    fig.canvas.manager.window.after(100, drawDataCallback,baseline)

def drawWaterfallCallback(baseline):
    global waterfall_amp
    global waterfall_phs
    matplotlib.pyplot.clf()
    acc_n,interleave_a,interleave_b = get_data(baseline)

    waterfall_amp = numpy.append(numpy.abs(interleave_a[::-1]),
                                waterfall_amp[:-1]).reshape(arr_size)
    waterfall_phs = numpy.append(numpy.angle(interleave_b[::-1]),
                                 waterfall_phs[:-1]).reshape(arr_size)

    ax1 = matplotlib.pyplot.subplot(121)
    im1 = ax1.imshow(waterfall_amp, norm=LogNorm(),
                     interpolation='nearest', origin='lower', aspect='auto')
    ax1.set_xticks([1024*i/5. for i in numpy.linspace(0,5,5)])
    ax1.set_xticklabels(map(str, 100*numpy.arange(4,9)))
    ax1.set_yticks([])
    cbar1 = matplotlib.pyplot.colorbar(im1)
    matplotlib.pyplot.grid()
    matplotlib.pyplot.xlabel('Frequency (MHz)')
    matplotlib.pyplot.title('Power (arbitrary units)')

    ax2 = matplotlib.pyplot.subplot(122)
    im2 = ax2.imshow(waterfall_phs, interpolation='nearest', origin='lower',
                     aspect='auto', vmin=-numpy.pi, vmax=numpy.pi)
    ax2.set_xticks([1024*i/5. for i in numpy.linspace(0,5,5)])
    ax2.set_xticklabels(map(str, 100*numpy.arange(4,9)))
    ax2.set_yticks([])
    cbar2 = matplotlib.pyplot.colorbar(im2)
    matplotlib.pyplot.grid()
    matplotlib.pyplot.xlabel('Frequency (MHz)')
    matplotlib.pyplot.title('Phase')

    #matplotlib.pyplot.tight_layout()
    fig.canvas.draw()
    fig.canvas.manager.window.after(100, drawWaterfallCallback,baseline)

#START OF MAIN:

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('poco_plot_cross.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-c', '--cross', dest='cross', type='str',default='ab',
        help='Plot this cross correlation magnitude and phase. default: ab')
    p.add_option('-C','--channel',dest='ch',action='store_true',
        help='Set plot with channel number or frequency.')
    p.add_option('-f','--frequency',dest='fr',type='float',default=400.0,
        help='Set plot max frequency.(If -c sets to False)')
    p.add_option('-w', '--waterfall', action='store_true',
        help='Create an updating waterfall plot.')
    p.add_option('-N', '--num-integ', type='int', default=100,
        help='Number of integrations for waterfall plots.')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. \nExiting.'
        exit()
    else:
        roach = args[0]

    if opts.ch !=None:
        ifch = opts.ch
    else:
        ifch = False

    if ifch == False:
        if opts.fr != '':
            maxfr = opts.fr
        else:
            maxfr = 400.0
        xaxis = numpy.arange(0.0, maxfr, maxfr*1./1024)

    baseline=opts.cross

try:
    loggers = []
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s on port %i... '%(roach,katcp_port)),
    #fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, timeout=10,logger=logger)
    fpga = corr.katcp_wrapper.FpgaClient(roach,logger=logger)
    time.sleep(1)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()


    # set up the figure with a subplot for each polarisation to be plotted
    fig = matplotlib.pyplot.figure(figsize=(19,10))
    ax = fig.add_subplot(1,2,1)

    # start the process
    if opts.waterfall:
        arr_size = (opts.num_integ, 1024)
        waterfall_amp = numpy.zeros(arr_size)
        waterfall_phs = numpy.zeros(arr_size)
        fig.canvas.manager.window.after(100, drawWaterfallCallback,baseline)
    else:
        fig.canvas.manager.window.after(100, drawDataCallback,baseline)
    matplotlib.pyplot.show()
    print 'Plotting complete. Exiting...'

except AttributeError:
    pass
except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

