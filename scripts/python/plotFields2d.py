"""
Plots the 2D fields from the PETSc solutions generated with PetIBM.
"""

import os
import argparse

import numpy
from matplotlib import pyplot, cm

import ioPetIBM


def parse_command_line():
  """
  Parses the command-line.

  Returns
  -------
  args: namespace
    Database with arguments parsed from the command-line.
  """
  formatter_class = argparse.ArgumentDefaultsHelpFormatter
  parser = argparse.ArgumentParser(description='Plots the 2D vorticity, '
                                               'pressure and velocity fields',
                                   formatter_class=formatter_class)
  parser.add_argument('--directory',
                      dest='directory',
                      type=str,
                      default=os.getcwd(),
                      help='directory of the simulation')
  parser.add_argument('--vorticity-range', '-wr',
                      dest='vorticity_range',
                      type=float,
                      nargs='+',
                      default=None,
                      help='vorticity range (min, max, number of levels)')
  parser.add_argument('--u-range', '-ur',
                      dest='u_range',
                      type=float,
                      nargs='+',
                      default=None,
                      help='u-velocity range (min, max, number of levels)')
  parser.add_argument('--v-range', '-vr',
                      dest='v_range',
                      type=float,
                      nargs='+',
                      default=None,
                      help='v-velocity range (min, max, number of levels)')
  parser.add_argument('--pressure-range', '-pr',
                      dest='pressure_range',
                      type=float,
                      nargs='+',
                      default=None,
                      help='pressure range (min, max, number of levels)')
  parser.add_argument('--bottom-left', '-bl',
                      dest='bottom_left',
                      type=float,
                      nargs='+',
                      default=[float('-inf'), float('-inf')],
                      help='coordinates of the bottom-left corner of the view')
  parser.add_argument('--top-right', '-tr',
                      dest='top_right',
                      type=float,
                      nargs='+',
                      default=[float('inf'), float('inf')],
                      help='coordinates of the top-right corner of the view')
  parser.add_argument('--time-steps', '-t',
                      dest='time_steps',
                      type=int,
                      nargs='+',
                      default=[],
                      help='time-steps to plot (initial, final, increment)')
  parser.add_argument('--periodic',
                      dest='periodic',
                      type=str,
                      nargs='+',
                      default=[],
                      help='direction(s) (x and/or y) with '
                            'periodic boundary conditions')
  parser.add_argument('--no-velocity',
                      dest='velocity',
                      action='store_false',
                      help='does not plot the velocity fields')
  parser.add_argument('--no-pressure',
                      dest='pressure',
                      action='store_false',
                      help='does not plot the pressure field')
  parser.add_argument('--no-vorticity',
                      dest='vorticity',
                      action='store_false',
                      help='does not plot the vorticity field')
  parser.add_argument('--size',
                      dest='size',
                      type=float,
                      nargs='+',
                      default=[8.0, 8.0],
                      help='size (width and height) of the figure '
                           'to save (in inches)')
  parser.add_argument('--dpi',
                      dest='dpi',
                      type=int,
                      default=100,
                      help='dots per inch (resoltion of the figure)')
  parser.set_defaults(velocity=True, pressure=True, vorticity=True)
  return parser.parse_args()


def vorticity(u, v):
  """
  Computes the vorticity field for a two-dimensional simulation.

  Parameters
  ----------
  u, v: Field objects
    Velocity fields.

  Returns
  -------
  vorticity: Field object
    The vorticity field.
  """
  print('\tCompute the vorticity field ...')
  mask_x = numpy.where(numpy.logical_and(u.x > v.x[0], u.x < v.x[-1]))[0]
  mask_y = numpy.where(numpy.logical_and(v.y > u.y[0], v.y < u.y[-1]))[0]
  # vorticity nodes at cell vertices intersection
  xw, yw = 0.5 * (v.x[:-1] + v.x[1:]), 0.5 * (u.y[:-1] + u.y[1:])
  # compute vorticity
  w = ((v.values[mask_y, 1:] - v.values[mask_y, :-1])
       / numpy.outer(numpy.ones(yw.size), v.x[1:] - v.x[:-1])
       - (u.values[1:, mask_x] - u.values[:-1, mask_x])
       / numpy.outer(u.y[1:] - u.y[:-1], numpy.ones(xw.size)))
  return ioPetIBM.Field(x=xw, y=yw, values=w)


def plot_contour(field, field_range, image_path,
                 view=[float('-inf'), float('-inf'),
                       float('inf'), float('inf')],
                 size=[8.0, 8.0], dpi=100):
  """
  Plots and saves the field.

  Parameters
  ----------
  field: Field object
    Nodes and values of the field.
  field_range: 3-tuple with 2 floats and 1 integer
    Min, max and number of contours to plot.
  image_path: string
    Path of the image to save.
  view: list of 4 floats, optional
    Bottom-left and top-right coordinates of the rectangular view to plot;
    default: the whole domain.
  size: list of 2 floats, optional
    Size (width and height) of the figure to save (in inches);
    default: [8, 8].
  dpi: integer, optional
    Dots per inch (resolution);
    default: 100
  """
  print('\tPlot the {} contour ...'.format(field.label))
  fig, ax = pyplot.subplots(figsize=(size[0], size[1]), dpi=dpi)
  pyplot.xlabel('$x$')
  pyplot.ylabel('$y$')
  if field_range:
    levels = numpy.linspace(field_range[0], field_range[1], field_range[2])
    colorbar_ticks = numpy.linspace(field_range[0], field_range[1], 5)
  else:
    levels = numpy.linspace(field.values.min(), field.values.max(), 101)
    colorbar_ticks = numpy.linspace(field.values.min(), field.values.max(), 5)
  X, Y = numpy.meshgrid(field.x, field.y)
  color_map = {'pressure': cm.jet, 'vorticity': cm.RdBu_r,
               'u-velocity': cm.RdBu_r, 'v-velocity': cm.RdBu_r}
  cont = ax.contourf(X, Y, field.values,
                     levels=levels, extend='both',
                     cmap=color_map[field.label])
  fig.colorbar(cont, label=field.label,
               orientation='horizontal', format='%.02f',
               ticks=colorbar_ticks)
  x_start, x_end = max(view[0], field.x.min()), min(view[2], field.x.max())
  y_start, y_end = max(view[1], field.y.min()), min(view[3], field.y.max())
  ax.axis([x_start, x_end, y_start, y_end])
  ax.set_aspect('equal')
  pyplot.savefig(image_path, dpi=dpi)
  pyplot.close()


def main(args):
  """
  Plots the the velocity, pressure and vorticity fields at saved time-steps
  for a two-dimensional simulation.

  Parameters
  ----------
  args: namespace
    Database with arguments parsed from the command-line.
  """
  print('[case directory] {}'.format(args.directory))

  time_steps = ioPetIBM.get_time_steps(args.time_steps,
                                       directory=args.directory)

  # create directory where images will be saved
  images_directory = os.path.join(args.directory, 'images')
  print('[images directory] {}'.format(images_directory))
  if not os.path.isdir(images_directory):
    os.makedirs(images_directory)

  # read the grid nodes
  coords = ioPetIBM.read_grid(directory=args.directory)

  # load default style of matplotlib figures
  pyplot.style.use(os.path.join(os.environ['PETIBM_DIR'],
                                'scripts',
                                'python',
                                'style',
                                'style_PetIBM.mplstyle'))

  for time_step in time_steps:
    if args.velocity or args.vorticity:
      # get velocity fields
      u, v = ioPetIBM.read_velocity(time_step, coords,
                                    directory=args.directory,
                                    periodic=args.periodic)
      if args.velocity:
        # plot u-velocity field
        u.label = 'u-velocity'
        image_path = os.path.join(images_directory,
                                  'uVelocity{:0>7}.png'.format(time_step))
        plot_contour(u, args.u_range, image_path,
                     view=args.bottom_left + args.top_right,
                     size=args.size, dpi=args.dpi)
        # plot v-velocity field
        v.label = 'v-velocity'
        image_path = os.path.join(images_directory,
                                  'vVelocity{:0>7}.png'.format(time_step))
        plot_contour(v, args.v_range, image_path,
                     view=args.bottom_left + args.top_right,
                     size=args.size, dpi=args.dpi)
      if args.vorticity:
        # compute vorticity field
        w = vorticity(u, v)
        # plot vorticity field
        w.label = 'vorticity'
        image_path = os.path.join(images_directory,
                                  'vorticity{:0>7}.png'.format(time_step))
        plot_contour(w, args.vorticity_range, image_path,
                     view=args.bottom_left + args.top_right,
                     size=args.size, dpi=args.dpi)
    if args.pressure:
      # get pressure field
      p = ioPetIBM.read_pressure(time_step, coords,
                                 directory=args.directory)
      # plot pressure field
      p.label = 'pressure'
      image_path = os.path.join(images_directory,
                                'pressure{:0>7}.png'.format(time_step))
      plot_contour(p, args.pressure_range, image_path,
                   view=args.bottom_left + args.top_right,
                   size=args.size, dpi=args.dpi)


if __name__ == '__main__':
  print('\n[{}] START\n'.format(os.path.basename(__file__)))
  args = parse_command_line()
  main(args)
  print('\n[{}] END\n'.format(os.path.basename(__file__)))
