# wsltty-portable
 Windows Subsystem for Linux (WSL) 的终端模拟器，基于 [mintty](https://github.com/mintty/mintty) 和 [wslbridge](https://github.com/rprichard/wslbridge) ; 参考了 [wsltty](https://github.com/mintty/wsltty) 和 [wsl-terminal](https://github.com/goreliu/wsl-terminal) 这 2 个项目



## 特点

* 绿色版；解压后，修改配置文件就可以运行
* 采用 msys2 编译 mintty
* 代码更好维护；打包脚本使用 python 开发，wsltty 使用 rust 开发

## 安装和配置

如果还没安装 WSL 下的 Linux，可以使用 [LxRunOffline](https://github.com/DDoSolitary/LxRunOffline) 来安装 WSL 下的 Linux

* 下载文件 

* 修改配置 `wsltty.toml`

  ```
  # 默认启动的 shell
  shell = "/bin/bash"
  # linux 对应的 distro
  distro = "ubuntu"

  # mintty 的可执行文件路径，
  # 默认是当前路径下的 ${mintty-portable}/usr/bin/mintty.exe
  # mintty_bin_path=""

  # mintty 的标题栏的 ico 
  # 文件名必须是 ${mintty-portable}/resouces/ico 下的文件名
  # ico_name = "ubuntu"

  # mintty 的标题
  # title = "wsltty"

  # mintty 的配置文件所在目录路径
  # 默认是当前路径下的 ${mintty-portable}/etc/ 目录
  # mintty_config_dir = ""
  ```

  ​

* 安装字体

  双击安装 ${mintty-portable}/resources/fonts 下的 consolas-font-for-powerline 字体文件，mintty 默认配置是使用 [consolas-font-for-powerline]( https://github.com/runsisi/consolas-font-for-powerline) 的字体的

  ​

## 

mintty 与 WSL 相关的说明 https://github.com/mintty/mintty/wiki/Tips

wslbridge 的工作原理  https://github.com/rprichard/wslbridge/issues/3



