conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(prefix, get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('PYTHON', python3.find_python().path())
conf.set('pythondir', join_paths(prefix, pythondir))

configure_file(
  input: 'gnome-pipe.in',
  output: 'gnome-pipe',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

gnome-pipe = join_paths(meson.build_root(), 'bin', 'gnome-pipe')
run_target('run',
  command: [gnome-pipe]
)
