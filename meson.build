project('gnome-pipe',
  version: '1.1',
  meson_version: '>= 0.40.0'
)

# i18n = import('i18n')
python3 = import('python3')
prefix = get_option('prefix')
pkgdatadir = join_paths(prefix, get_option('datadir'), meson.project_name())
pythondir = python3.sysconfig_path('purelib')

install_subdir('gnome-pipe', install_dir: pythondir)
subdir('data')
subdir('bin')

meson.add_install_script('scripts/meson_post_install.py')

if get_option('with-flatpak')
  # We keep a generic manifest in the repo you can use but
  # we want builds to use the local files so simply rewrite it
  make_local_manifest = find_program('scripts/make_local_manifest.py')
  local_manifest = custom_target('manifest',
    input: 'dist/flatpak/org.gabmus.gnome-pipe.json',
    output: 'org.gabmus.gnome-pipe.json',
    command: [make_local_manifest, '@INPUT@', '@OUTPUT@']
  )

  # Build a bundle for both testing and releases
  build_flatpak = find_program('scripts/build_flatpak.py')
  custom_target('flatpak',
    input: local_manifest,
    output: 'org.gabmus.gnome-pipe.flatpak',
    command: [build_flatpak, '@INPUT@', '@OUTPUT@'],
    build_always: true
    # TODO: This shouldn't build unless explicit
  )
endif