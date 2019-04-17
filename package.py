# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil
import platform
import re
import io

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
}

mintty_version = '2.9.5'
mintty_msys2_url = "https://raw.githubusercontent.com/Alexpux/MSYS2-packages/%s/mintty/" % (mintty_version_map[mintty_version])
mintty_url = 'https://github.com/mintty/mintty/archive/%s.tar.gz' % (mintty_version)
mintty_name = 'mintty-%s' % (mintty_version)

wslbridge_version = '0.2.4'
wslbridge_url = 'https://github.com/rprichard/wslbridge/releases/download/%s/%%s' % (wslbridge_version)


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


def build_wsltty(context):

    cmd = '%s clean' % context.cargo_bin
    call_shell_command(cmd, work_dir=context.wsltty_dir, shell=True)

    cmd = '%s build --release' % context.cargo_bin
    call_shell_command(cmd, work_dir=context.wsltty_dir, shell=True)


def build_launcher(context):

    cmd = 'powershell -File build.ps1'
    call_shell_command(cmd, work_dir=context.launcher_dir, shell=True)

    laucher_bin = os.path.join(context.launcher_dir, 'wsltty-launcher.exe')
    if not os.path.exists(laucher_bin):
        print("build launcher failed")
        sys.exit(-1)


def make_wslbrigde_name(context):
    return 'wslbridge-%s-%s' % (wslbridge_version, context.platform_machine)


def make_wslbrigde_archive(context):
    return '%s.tar.gz' % (make_wslbrigde_name(context))


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


def download(context):
    download_wslbridge(context)


def build(context):

    build_mintty(context)

    # build_wsltty(context)
    build_launcher(context)


def after_build(context):
    pass


def generate_version_file(context, dest_dir):
    p = os.path.join(dest_dir, 'version.txt')
    with open(p, 'w') as f:
        f.write('mintty = %s\n' % mintty_version)
        f.write('wslbridge = %s\n' % wslbridge_version)
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

    # copy wslbrigde to dist/wsltty

    mintty_bin_dir = os.path.join(wsltty_dist_dir, 'usr', 'bin')

    wslbridge_name = make_wslbrigde_name(context)
    wslbridge_name_archive = make_wslbrigde_archive(context)
    wslbrigde_dir = os.path.join(
            context.download_dir,
            wslbridge_name
            )
    if not os.path.exists(wslbrigde_dir) or not os.path.isdir(wslbrigde_dir):
            call_shell_command([
                    'tar', 'xfz', wslbridge_name_archive
                    ], work_dir=context.download_dir
            )
    shutil.copy(
            os.path.join(wslbrigde_dir, 'wslbridge.exe'),
            mintty_bin_dir)
    shutil.copy(
            os.path.join(wslbrigde_dir, 'wslbridge-backend'),
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
