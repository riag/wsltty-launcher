# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil
import platform
import re
import io
import py7zr

require_platform = 'msys'

# 从 laucher/wsltty-laucher.go 里读取版本号
launcher_version = ''

version_pattern = r'const\s+version\s+string\s+=\s*\"(.*?)\"'

curr_dir = os.path.dirname(os.path.realpath(__file__))

# mintty 2.8.3 -> f5b7aa6ab9cfa79bebad5cb3c2a03949a1d24423
# mintty 2.8.4 -> ed9f0a14b679ca31daccfafa6dad2b13744ad2a6
mintty_version_map = {
    '2.8.3': 'f5b7aa6ab9cfa79bebad5cb3c2a03949a1d24423',
    '2.8.4': 'ed9f0a14b679ca31daccfafa6dad2b13744ad2a6',
    '2.8.5': 'b6a482792f0f2239f4839a23189ccc5777175b95',
    '2.9.4': '37c52820c9e6e2e125585aa743d09ac59d8e57d2',
    '2.9.5': 'f969bc9f861b95b47a81b0c9452d75d69ccf5b75',
    '3.0.0': 'ecaf326b9769caaf398b658eef5c24af64bb6d38',
    '3.0.2': 'fe045cbe3c47d274e99f477d90589354fcd4458c',
    '3.1.0': '368a8b5e7db3370d4e9f2b9d7164087b76decb92',
}

mintty_patch_files_map = {
        '3.0.2':[
                'PKGBUILD',
                '0002-add-msys2-launcher.patch',
                '8be3ff0d918058b56ba0d1bc26eea25b875ab929.patch'
                ],
        '3.1.0':[
                'PKGBUILD',
                '0002-add-msys2-launcher.patch',
                ],
}

mintty_version = '3.1.0'
mintty_msys2_url = "https://raw.githubusercontent.com/riag/MSYS2-packages/%s/mintty/" % (mintty_version_map[mintty_version])
mintty_url = 'https://github.com/mintty/mintty/archive/%s.tar.gz' % (mintty_version)
mintty_name = 'mintty-%s' % (mintty_version)

wslbridge_version = '0.2.4'
wslbridge_url = 'https://github.com/rprichard/wslbridge/releases/download/%s/%%s' % (wslbridge_version)

wslbridge2_version = 'v0.5'
wslbridge2_url = 'https://github.com/Biswa96/wslbridge2/releases/download/%s/%%s' % (wslbridge2_version)


class BuildContext(object):
    def __init__(self, sys_platform, machine, curr_dir):
        self.sys_platform = sys_platform
        self.machine = machine
        self.architecture = '32'
        if machine == 'x86_64':
            self.architecture = '64'

        self.platform_machine = '%s%s' % (self.sys_platform, self.architecture)

        self.build_dir = os.path.join(curr_dir, 'build')
        self.download_dir = os.path.join(curr_dir, 'download')
        self.mintty_dir = os.path.join(self.build_dir, 'mintty')
        self.dist_dir = os.path.join(curr_dir, 'dist')
        self.launcher_dir = os.path.join(curr_dir, 'launcher')
        self.config_dir = os.path.join(curr_dir, 'config')
        self.resources_dir = os.path.join(curr_dir, 'resources')
        self.ico_dir = os.path.join(self.resources_dir, 'ico')
        self.fonts_dir = os.path.join(self.resources_dir, 'fonts')

        launcher_src_file = os.path.join(self.launcher_dir, 'wsltty-launcher.go')

        global launcher_version
        with io.open(launcher_src_file, 'rt', encoding='utf-8') as f:
            launcher_version = re.search(version_pattern, f.read()).group(1)



def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except Exception as e:
                print(e)
                os.unlink(d)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def execute_shell_command(cmd_list, work_dir=None):
    print("exec: ", ' '.join(cmd_list))
    output = subprocess.check_output(cmd_list, cwd=work_dir)
    print(output)
    return output


def call_shell_command(cmd_list, work_dir=None, check=True, shell=False):
    print("exec: ", ' '.join(cmd_list))
    return subprocess.run(
        cmd_list, check=check, shell=shell,
        cwd=work_dir).returncode


def prepare_build(context):
    print("platform: %s" % context.sys_platform)
    if not context.sys_platform.startswith(require_platform):
        print("please run script in %s" % require_platform,  file=sys.stderr)
        sys.exit(-1)

    if not os.path.exists(context.build_dir) or not os.path.isdir(context.build_dir):
        os.makedirs(context.build_dir)

    if os.path.exists(context.mintty_dir) or os.path.isdir(context.mintty_dir):
        shutil.rmtree(context.mintty_dir)

    os.makedirs(context.mintty_dir)

    if not os.path.exists(context.download_dir) or not os.path.isdir(context.download_dir):
        os.makedirs(context.download_dir)

    if not os.path.exists(context.dist_dir) or not os.path.isdir(context.dist_dir):
        os.makedirs(context.dist_dir)


def download_mintty(work_dir):
    download_file(mintty_url, mintty_name + '.tar.gz', work_dir)


def build_mintty(context):
    build_scripts = mintty_patch_files_map.get(mintty_version, None)
    if build_scripts is None:
        build_scripts = [
                '0002-add-msys2-launcher.patch',
                '0003-fix-current-dir-inheritance-for-alt-f2-on-msys2.patch' ,
                'PKGBUILD'
                ]
    for s in build_scripts:
        u = mintty_msys2_url + s
        # call_shell_command([
        #    'wget', '-O',
        #    os.path.join(context.mintty_dir, s), u]
        #    )
        download_file(u, s, context.mintty_dir)

    mintty_src_archive = os.path.join(context.download_dir, mintty_name + '.tar.gz')
    if not os.path.exists(mintty_src_archive) or not os.path.isfile(mintty_src_archive):
            download_mintty(context.download_dir)

    shutil.copy(mintty_src_archive, context.mintty_dir)
    call_shell_command(['makepkg'], work_dir=context.mintty_dir)

    src_dir = os.path.join(context.mintty_dir, 'pkg', 'mintty')
    dest_dir = os.path.join(context.dist_dir, 'mintty')

    if os.path.exists(dest_dir) and os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)

    shutil.copytree(src_dir, dest_dir)
    mintty_bin_dir = os.path.join(dest_dir, 'usr', 'bin')
    shutil.copy('/usr/bin/msys-2.0.dll', mintty_bin_dir)
    shutil.copy('/usr/bin/cygwin-console-helper.exe', mintty_bin_dir)


def build_launcher(context):

    laucher_bin = os.path.join(context.launcher_dir, 'wsltty-launcher.exe')
    if os.path.isfile(laucher_bin):
            os.remove(laucher_bin)

    cmd = 'powershell -File build.ps1'
    call_shell_command(cmd, work_dir=context.launcher_dir, shell=True)

    if not os.path.exists(laucher_bin):
        print("build launcher failed")
        sys.exit(-1)


def make_wslbrigde_name(context):
    return 'wslbridge-%s-%s' % (wslbridge_version, context.platform_machine)


def make_wslbrigde_archive(context):
    return '%s.tar.gz' % (make_wslbrigde_name(context))


def make_wslbrigde2_name(context, with_version=False):
    if with_version:
        return 'wslbridge2-%s_x86_64' % (context.platform_machine)
    else:
        return 'wslbridge2-%s-%s_x86_64' % (wslbridge2_version, context.platform_machine)


def make_wslbrigde2_archive(context, with_version=False):
    return '%s.7z' % (make_wslbrigde2_name(context), with_version)


def download_file(url, path, work_dir):
    tmp_path = path + '.tmp'

    if os.path.isfile(tmp_path):
        os.remove(tmp_path)

    call_shell_command([
            'wget', '-O', tmp_path,
            url],
            work_dir=work_dir)

    if work_dir:
        os.rename(
                os.path.join(work_dir, tmp_path),
                os.path.join(work_dir, path)
        )
    else:
        os.rename(tmp_path, path)


def download_wslbridge(context):
        wslbridge_archive = make_wslbrigde_archive(context)
        wslbridge_archive_path = os.path.join(
                context.download_dir,
                wslbridge_archive)
        url = wslbridge_url % wslbridge_archive
        if not os.path.exists(wslbridge_archive_path) or not os.path.isfile(wslbridge_archive_path):
                download_file(url, wslbridge_archive, context.download_dir)

def download_wslbridge2(context):
        wslbridge2_archive = make_wslbrigde2_archive(context, False)
        url = wslbridge2_url % wslbridge2_archive

        wslbridge2_archive_version = make_wslbrigde2_archive(context, True)
        wslbridge2_archive_path = os.path.join(
                context.download_dir,
                wslbridge2_archive_version)
        if not os.path.exists(wslbridge_archive_path) or not os.path.isfile(wslbridge_archive_path):
                download_file(url, wslbridge2_archive_version, context.download_dir)

def download(context):
    download_wslbridge2(context)


def build(context):

    build_mintty(context)

    build_launcher(context)


def after_build(context):
    pass


def generate_version_file(context, dest_dir):
    p = os.path.join(dest_dir, 'version.txt')
    with open(p, 'w') as f:
        f.write('mintty = %s\n' % mintty_version)
        f.write('wslbridge2 = %s\n' % wslbridge2_version)
        f.write('wsltty-launcher = %s\n' % launcher_version)


def package(context):

    wsltty_dist_name = 'wsltty-launcher-%s-%s' % ( launcher_version, context.platform_machine )
    wsltty_dist_dir = os.path.join(context.dist_dir,
             wsltty_dist_name
    )

    # copy launcher
    launcher_bin = os.path.join(context.launcher_dir, 'wsltty-launcher.exe')

    if os.path.exists(wsltty_dist_dir) and os.path.isdir(wsltty_dist_dir):
            shutil.rmtree(wsltty_dist_dir)

    os.makedirs(wsltty_dist_dir)

    shutil.copy(launcher_bin, wsltty_dist_dir)

    # copy mintty to dist/mintty dir
    src_dir = os.path.join(context.dist_dir, 'mintty')

    src_dir = os.path.join(context.mintty_dir, 'pkg', 'mintty')
    mintty_dist_dir = os.path.join(context.dist_dir, 'mintty')

    if os.path.exists(mintty_dist_dir) and os.path.isdir(mintty_dist_dir):
            shutil.rmtree(mintty_dist_dir)

    shutil.copytree(src_dir, mintty_dist_dir)

    # copy msys2 dll or exe to dist/mintty dir
    mintty_bin_dir = os.path.join(mintty_dist_dir, 'usr', 'bin')
    shutil.copy('/usr/bin/msys-2.0.dll', mintty_bin_dir)
    shutil.copy('/usr/bin/cygwin-console-helper.exe', mintty_bin_dir)

    # copy dist/mintty to dist/wsltty
    copytree(mintty_dist_dir, wsltty_dist_dir)

    # copy wslbrigde2 to dist/wsltty

    mintty_bin_dir = os.path.join(wsltty_dist_dir, 'usr', 'bin')

    wslbridge2_name = make_wslbrigde2_name(context, True)
    wslbridge2_name_archive = make_wslbrigde2_archive(context, True)
    wslbrigde2_dir = os.path.join(
            context.download_dir,
            wslbridge2_name
            )
    if not os.path.exists(wslbrigde2_dir) or not os.path.isdir(wslbrigde2_dir):
            archive = py7zr.SevenZipFile(wslbridge2_name_archive, mode='x')
            archive.extractall(path=wslbridge2_dir)
            archive.close()

    shutil.copy(
            os.path.join(wslbrigde2_dir, 'wslbridge2.exe'),
            mintty_bin_dir)
    shutil.copy(
            os.path.join(wslbrigde2_dir, 'wslbridge2-backend'),
            mintty_bin_dir)
    shutil.copy(
            os.path.join(wslbrigde2_dir, 'rawpty.exe'),
            mintty_bin_dir)

    # copy config file to dist/wsltty
    shutil.copy(
            os.path.join(context.launcher_dir, 'wsltty-launcher.toml.tpl'),
            os.path.join(wsltty_dist_dir, 'wsltty-launcher.toml'))

    etc_dir = os.path.join(wsltty_dist_dir, 'etc')
    os.makedirs(etc_dir)
    shutil.copy(
            os.path.join(context.config_dir, 'minttyrc'),
            etc_dir
            )

    # copy ico
    shutil.copytree(
            context.ico_dir,
            os.path.join(wsltty_dist_dir, 'resources', 'ico')
    )

    # copy fonts
    shutil.copytree(
            context.fonts_dir,
            os.path.join(wsltty_dist_dir, 'resources', 'fonts')
    )

    # copy license
    shutil.copy(
            os.path.join(curr_dir, 'LICENSE.mintty'),
            wsltty_dist_dir
            )
    shutil.copy(
            os.path.join(curr_dir, 'LICENSE.wslbridge'),
            wsltty_dist_dir
            )

    generate_version_file(context, wsltty_dist_dir)

    # rm file
    for m in ['.BUILDINFO', '.MTREE', '.PKGINFO']:
        p = os.path.join(wsltty_dist_dir, m)
        os.remove(p)

    log_dir = os.path.join(wsltty_dist_dir, 'logs')
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    # zip dir
    call_shell_command([
        'zip', '-r', wsltty_dist_name + '.zip',
        wsltty_dist_name
        ], work_dir=context.dist_dir)


def main():
    context = BuildContext(sys.platform, platform.machine(), curr_dir)

    prepare_build(context)

    download(context)

    build(context)

    after_build(context)

    package(context)


if __name__ == '__main__':
    main()
