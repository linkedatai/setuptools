"""Tests for distutils.cygwinccompiler."""
import unittest
import sys
import os

from distutils.cygwinccompiler import (
    check_config_h,
    CONFIG_H_OK,
    CONFIG_H_NOTOK,
    CONFIG_H_UNCERTAIN,
    get_msvcr,
)
from distutils.tests import support
import pytest


class CygwinCCompilerTestCase(support.TempdirManager, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.version = sys.version
        self.python_h = os.path.join(self.mkdtemp(), 'python.h')
        from distutils import sysconfig

        self.old_get_config_h_filename = sysconfig.get_config_h_filename
        sysconfig.get_config_h_filename = self._get_config_h_filename

    def tearDown(self):
        sys.version = self.version
        from distutils import sysconfig

        sysconfig.get_config_h_filename = self.old_get_config_h_filename
        super().tearDown()

    def _get_config_h_filename(self):
        return self.python_h

    @unittest.skipIf(sys.platform != "cygwin", "Not running on Cygwin")
    @unittest.skipIf(
        not os.path.exists("/usr/lib/libbash.dll.a"), "Don't know a linkable library"
    )
    def test_find_library_file(self):
        from distutils.cygwinccompiler import CygwinCCompiler

        compiler = CygwinCCompiler()
        link_name = "bash"
        linkable_file = compiler.find_library_file(["/usr/lib"], link_name)
        assert linkable_file is not None
        assert os.path.exists(linkable_file)
        assert linkable_file == f"/usr/lib/lib{link_name:s}.dll.a"

    @unittest.skipIf(sys.platform != "cygwin", "Not running on Cygwin")
    def test_runtime_library_dir_option(self):
        from distutils.cygwinccompiler import CygwinCCompiler

        compiler = CygwinCCompiler()
        assert compiler.runtime_library_dir_option('/foo') == []

    def test_check_config_h(self):

        # check_config_h looks for "GCC" in sys.version first
        # returns CONFIG_H_OK if found
        sys.version = (
            '2.6.1 (r261:67515, Dec  6 2008, 16:42:21) \n[GCC '
            '4.0.1 (Apple Computer, Inc. build 5370)]'
        )

        assert check_config_h()[0] == CONFIG_H_OK

        # then it tries to see if it can find "__GNUC__" in pyconfig.h
        sys.version = 'something without the *CC word'

        # if the file doesn't exist it returns  CONFIG_H_UNCERTAIN
        assert check_config_h()[0] == CONFIG_H_UNCERTAIN

        # if it exists but does not contain __GNUC__, it returns CONFIG_H_NOTOK
        self.write_file(self.python_h, 'xxx')
        assert check_config_h()[0] == CONFIG_H_NOTOK

        # and CONFIG_H_OK if __GNUC__ is found
        self.write_file(self.python_h, 'xxx __GNUC__ xxx')
        assert check_config_h()[0] == CONFIG_H_OK

    def test_get_msvcr(self):

        # none
        sys.version = (
            '2.6.1 (r261:67515, Dec  6 2008, 16:42:21) '
            '\n[GCC 4.0.1 (Apple Computer, Inc. build 5370)]'
        )
        assert get_msvcr() is None

        # MSVC 7.0
        sys.version = (
            '2.5.1 (r251:54863, Apr 18 2007, 08:51:08) ' '[MSC v.1300 32 bits (Intel)]'
        )
        assert get_msvcr() == ['msvcr70']

        # MSVC 7.1
        sys.version = (
            '2.5.1 (r251:54863, Apr 18 2007, 08:51:08) ' '[MSC v.1310 32 bits (Intel)]'
        )
        assert get_msvcr() == ['msvcr71']

        # VS2005 / MSVC 8.0
        sys.version = (
            '2.5.1 (r251:54863, Apr 18 2007, 08:51:08) ' '[MSC v.1400 32 bits (Intel)]'
        )
        assert get_msvcr() == ['msvcr80']

        # VS2008 / MSVC 9.0
        sys.version = (
            '2.5.1 (r251:54863, Apr 18 2007, 08:51:08) ' '[MSC v.1500 32 bits (Intel)]'
        )
        assert get_msvcr() == ['msvcr90']

        sys.version = (
            '3.10.0 (tags/v3.10.0:b494f59, Oct  4 2021, 18:46:30) '
            '[MSC v.1929 32 bit (Intel)]'
        )
        assert get_msvcr() == ['ucrt', 'vcruntime140']

        # unknown
        sys.version = (
            '2.5.1 (r251:54863, Apr 18 2007, 08:51:08) ' '[MSC v.2000 32 bits (Intel)]'
        )
        with pytest.raises(ValueError):
            get_msvcr()
