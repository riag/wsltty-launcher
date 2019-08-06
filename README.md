# wsltty-launcher
 Windows Subsystem for Linux (WSL) 的终端模拟器，基于 [mintty](https://github.com/mintty/mintty) 和 [wslbridge](https://github.com/rprichard/wslbridge) ; 参考了 [wsltty](https://github.com/mintty/wsltty) 和 [wsl-terminal](https://github.com/goreliu/wsl-terminal) 这 2 个项目



## 特点

* 绿色版；解压后，修改配置文件就可以运行
* 采用 msys2 编译 mintty
* 代码更好维护；打包脚本使用 python3 开发，wsltty-launcher 使用 golang 开发
* 从 0.3.2 版本开始自动设置以下 3 个环境变量，方便与 [pywslpath](https://github.com/riag/pywslpath) 配合一起使用
  ```
    WSL_DISTRO_NAME 当前 WSL Linux 的 distro name
    WSL_DISTRO_GUID 当前 WSL Linux 的 distro guid
    WSL_DISTRO_ROOTFS_DIR 当前 WSL Linux 的 distro rootfs 路径
  ```


## 安装和配置

如果还没安装 WSL 下的 Linux，可以使用 [LxRunOffline](https://github.com/DDoSolitary/LxRunOffline) 来安装 WSL 下的 Linux

* 下载文件 

​     在[这里](https://github.com/riag/wsltty-launcher/releases)下载最新版本

* 修改配置 `wsltty-launcher.toml`

  ```
	# 默认启动的 shell
	shell = "/bin/bash"
	# mintty 默认的标题
	title = "wsltty"
	# mintty 默认的图标名字
	# 文件名必须是 resources/ico 下的文件名
	icon_name = ""

	# mintty 的可执行文件路径，
	# 默认是 wsltty-launcher 的 usr/bin/mintty.exe
	mintty_bing_path = ""
	# mintty 的配置文件所在目录路径
	# 默认是 wsltty-launcer 的 etc/ 目录
	mintty_config_dir = ""

	# WSL Linux distro 对于的配置
	# 支持多个, launcher 启动时会询问选择哪个distro
	# 如果不设置 shell, title, icon_name, 使用默认值

	#[[distro]]
	#shell="/usr/bin/zsh"
	#title="manjaro-linux"
	#icon_name="manjaro.ico"
	# 该 distro 显示的名字
	#name = "manjaro-linux"
	# WSL Linux distro 名字
	#distro = "manjaro-linux"

	#[[distro]]
	#name = "manjaro-linux-test"
	#distro = "manjaro-linux-test"
  ```

  ​

* 安装字体

  双击安装 `resources/fonts` 下的 consolas-font-for-powerline 字体文件，mintty 默认配置是使用 [consolas-font-for-powerline]( https://github.com/runsisi/consolas-font-for-powerline) 的字体的

  ​

* 运行参数 
 可以直接运行，如果配置文件里定义了多个 WSL Linux Distro，则会让你选择
 也可以使用以下参数运行
 ```
-h, --help      显示帮助信息
-v, --version   显示版本号
-s, --slient    静默模式
    --config    指定配置文件
-n, --name      指定 distro name
    --workdir   指定 WSL Linux 的工作目录
 ```

 --name 对应的是配置文件里的 `name` 字段的值

## 编译

安装以下依赖软件

* 在 windows 下安装 golang 和 git，可以使用 scoop 来安装
* msys2
* 在 msys2 下安装 python3, binutils, patch, make, gcc, zip
* 在 msys2 下把 windows 的 golang 的 `bin` 目录加入到 `PATH` 环境变量, 以及 git 的目录加入到 `PATH` 环境变量

执行下面命令编译

```
python3 pakcage.py
```


## 

mintty 与 WSL 相关的说明 https://github.com/mintty/mintty/wiki/Tips

wslbridge 的工作原理  https://github.com/rprichard/wslbridge/issues/3



