# pylint: disable=missing-docstring,fixme

import os

from conans import ConanFile, tools
from conans.errors import ConanException

def get_version():
    # pylint: disable=bare-except
    try:
        return os.getenv('MINMEA_VERSION').strip()
    except:
        pass

    try:
        return tools.load('VERSION').strip()
    except:
        pass

    return None

class Minmea(ConanFile):
    name = 'minmea'
    version = get_version()
    url = 'https://github.com/StarryInternet/minmea.git'
    description = 'Minimal NMEA sentence parsing library'
    generators = 'pkg_config'
    settings = 'os', 'compiler', 'build_type', 'arch'
    license = 'WTFPL'

    # Conan assumes in-source build unless we specify out of source.
    no_copy_source = True

    def source(self):
        git = tools.Git()
        git.clone('git@github.com:StarryInternet/minmea.git')

        if self.version is not None:
            try:
                git.checkout(self.version)
            except:  # pylint: disable=bare-except
                self.output.warn(
                    'Failed to checkout version: {}'.format(self.version))

    # pylint:disable=no-member

    def build(self):
        optional_prefix = ''
        if getattr(self, 'package_folder', None) is not None:
            optional_prefix = '--prefix {} '.format(self.package_folder)

        self.run(
            'meson {} '
            '{}'
            '-Dtests=false '
            '-Dexample=false '
            '-Dinstall_headers=true '
            .format(self.build_folder, optional_prefix),
            cwd=self.source_folder
        )
        self.run('ninja', cwd=self.build_folder)

    def package(self):
        # pylint: disable=attribute-defined-outside-init

        # When no_copy_source is True, package() gets called twice...
        self._package_called = getattr(self, '_package_called', False)
        if self._package_called:
            return

        self.run('ninja install', cwd=self.build_folder)

        self._package_called = True

    def package_info(self):
        self.cpp_info.libs = ['minmea']

    def test(self):
        # FIXME What is wrong with Conan/Meson?
        success = False
        attempt = 1
        for attempt in range(1, 11):
            self.run(
                'meson configure -Dexample=true',
                cwd=self.build_folder,
            )

            self.run('ninja', cwd=self.build_folder)
            example = os.path.join(self.build_folder, 'example')

            if os.path.exists(example) and os.path.isfile(example):
                success = True
                break

            self.output.warn('Failed to reconfigure meson. Retrying...')

        if not success:
            raise ConanException(
                'Failed to reconfigure meson after {} attempts. '
                .format(attempt))
