# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil

require_platform = 'msys'

wsltty_version = '0.1.0'

curr_dir = os.path.dirname(os.path.realpath(__file__))

# mintty 2.8.3 -> f5b7aa6ab9cfa79bebad5cb3c2a03949a1d24423
# mintty 2.8.4 -> ed9f0a14b679ca31daccfafa6dad2b13744ad2a6
mintty_msys2_url="https://raw.githubusercontent.com/Alexpux/MSYS2-packages/%s/mintty/" % ("ed9f0a14b679ca31daccfafa6dad2b13744ad2a6")
mintty_version='2.8.4'
mintty_url = 'https://github.com/mintty/mintty/archive/%s.tar.gz' %( mintty_version )
mintty_name = 'mintty-%s.tar.gz' %( mintty_version )

wslbridge_version = '0.2.4'
wslbridge_url = 'https://github.com/rprichard/wslbridge/releases/download/0.2.4/wslbridge-%s-msys64.tar.gz' % ( wslbridge_version )

wslbridge_name = 'wslbridge-%s-msys64.tar.gz' % ( wslbridge_version )

class BuildContext(object):
    def __init__(self, curr_dir, cargo_bin='cargo'):
	    self.build_dir =os.path.join(curr_dir, 'build')
	    self.download_dir = os.path.join(curr_dir, 'download')
	    self.mintty_dir = os.path.join(self.build_dir, 'mintty')
	    self.dist_dir = os.path.join(curr_dir, 'dist')
	    self.wsltty_dir = os.path.join(curr_dir, 'wsltty')
	    self.cargo_bin = os.getenv('CARGO_BIN', 'cargo.exe')
	    self.config_dir = os.path.join(curr_dir, 'config')
	    self.ico_dir = os.path.join(curr_dir, 'ico')

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
	print("platform: %s" % sys.platform)
	if not sys.platform.startswith(require_platform):
		print("please run script in %s"% require_platform,  file=sys.stderr)
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
	call_shell_command(['wget', '-O', mintty_name, mintty_url], work_dir)

def build_mintty(context):
    build_scripts = [
            '0002-add-msys2-launcher.patch', 
            '0003-fix-current-dir-inheritance-for-alt-f2-on-msys2.patch' ,
            'PKGBUILD'
            ]
    for s in build_scripts:
        u = mintty_msys2_url + s
        call_shell_command([
            'wget', '-O', 
            os.path.join(context.mintty_dir, s), u]
            )

    mintty_src_archive = os.path.join(context.download_dir, mintty_name)
    if not os.path.exists(mintty_src_archive) or not os.path.isfile(mintty_src_archive):
	    download_mintty(context.download_dir)

    shutil.copy(mintty_src_archive, context.mintty_dir)
    call_shell_command(['makepkg'], work_dir=context.mintty_dir) 

    src_dir = os.path.join(context.mintty_dir, 'pkg', 'mintty')
    dest_dir = os.path.join(context.dist_dir, 'mintty')

    if os.path.exists(dest_dir) and os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)

    shutil.copytree(src_dir, dest_dir)
    mintty_bin_dir=os.path.join(dest_dir, 'usr', 'bin')
    shutil.copy('/usr/bin/msys-2.0.dll', mintty_bin_dir)
    shutil.copy('/usr/bin/cygwin-console-helper.exe', mintty_bin_dir)


def build_wsltty(context):
	call_shell_command([
			context.cargo_bin, 'build', '--release'
	], work_dir=context.wsltty_dir)
	

def download_wslbridge(context):
	wslbridge_archive = os.path.join(
		context.download_dir, 
		wslbridge_name)
	if not os.path.exists(wslbridge_archive) or not os.path.isfile(wslbridge_archive):
		call_shell_command([
			'wget', '-O', wslbridge_name,
			wslbridge_url], 
			work_dir=context.download_dir)


def build(context):
    download_wslbridge(context)

    build_mintty(context)
    build_wsltty(context)

def after_build(context):
    pass

def package(context):

	# copy wsltty.exe
	wsltty_bin=os.path.join(context.wsltty_dir, 'target', 'release', 'wsltty.exe')
	wsltty_dist_dir = os.path.join(context.dist_dir, 'wsltty')

	if os.path.exists(wsltty_dist_dir) and os.path.isdir(wsltty_dist_dir):
		shutil.rmtree(wsltty_dist_dir)	

	os.makedirs(wsltty_dist_dir)

	shutil.copy(wsltty_bin, wsltty_dist_dir)

	# copy mintty to dist/mintty dir
	src_dir = os.path.join(context.dist_dir, 'mintty')

	src_dir = os.path.join(context.mintty_dir, 'pkg', 'mintty')
	mintty_dist_dir = os.path.join(context.dist_dir, 'mintty')

	if os.path.exists(mintty_dist_dir) and os.path.isdir(mintty_dist_dir):
		shutil.rmtree(mintty_dist_dir)

	shutil.copytree(src_dir, mintty_dist_dir)

	# copy msys2 dll or exe to dist/mintty dir
	mintty_bin_dir=os.path.join(mintty_dist_dir, 'usr', 'bin')
	shutil.copy('/usr/bin/msys-2.0.dll', mintty_bin_dir)
	shutil.copy('/usr/bin/cygwin-console-helper.exe', mintty_bin_dir)

	# copy dist/mintty to dist/wsltty
	copytree(mintty_dist_dir, wsltty_dist_dir)

	# copy wslbrigde to dist/wsltty

	mintty_bin_dir=os.path.join(wsltty_dist_dir, 'usr', 'bin')
	wslbrigde_dir = os.path.join(
		context.download_dir, 
		'wslbridge-%s-msys64' % wslbridge_version)
	if not os.path.exists(wslbrigde_dir) or not os.path.isdir(wslbrigde_dir):
		call_shell_command([
			'tar', 'xfz', wslbridge_name
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
		os.path.join(context.config_dir, 'wsltty.toml'),
		wsltty_dist_dir)
	
	etc_dir = os.path.join(wsltty_dist_dir, 'etc')
	os.makedirs(etc_dir)
	shutil.copy(
		os.path.join(context.config_dir, 'minttyrc'),
		etc_dir
		)

	# copy ico
	shutil.copytree(
		context.ico_dir,
		os.path.join(wsltty_dist_dir, 'ico')
	)
		

if __name__ == '__main__':

    context = BuildContext(curr_dir)

    #prepare_build(context)

    #build(context)

    after_build(context)

    package(context)
