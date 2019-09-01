package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"golang.org/x/sys/windows/registry"

	"github.com/BurntSushi/toml"
	"github.com/mkideal/cli"
)

const version string = "0.3.5"

type DistroConfig struct {
	Shell     string
	Title     string
	Icon_name string
	Distro    string
	Name      string
	// work_dir string
}

type LauncherConfig struct {
	// 运行的 shell
	Shell             string
	Title             string
	Icon_name         string
	Debug             bool
	Mintty_bin_path   string
	Mintty_config_dir string
	LogFile			  string
	//work_dir string
	Distro []DistroConfig
}

type LxssInfo struct {
		Name 			string
		Guid			string
		BasePath  string
}

func error_and_exit(slient bool, msg interface{}){
	 	if msg != nil {
			log.Println(msg)
		}
		if !slient{
				fmt.Println("")
				fmt.Println("press any key to exit")

				var input string
				fmt.Scanln(&input)
		}
		os.Exit(-1)
}

func init_default(exe_dir string, config *LauncherConfig) {
	if len(config.Shell) == 0 {
		config.Shell = "/bin/bash"
	}
	if len(config.Title) == 0 {
		config.Title = "wsltty"
	}
	if len(config.Mintty_bin_path) == 0 {
		config.Mintty_bin_path = filepath.Join(exe_dir, "usr", "bin", "mintty.exe")
	}
	if len(config.Mintty_config_dir) == 0 {
		config.Mintty_config_dir = filepath.Join(exe_dir, "etc")
	}
	if len(config.LogFile) == 0 {
		config.LogFile = filepath.Join(exe_dir, "logs", "wsltty.log")
	}
	//init Distro
	for _, d := range config.Distro {
		if len(d.Title) == 0 {
			d.Title = config.Title
		}
		if len(d.Shell) == 0 {
			d.Shell = config.Shell
		}
		if len(d.Icon_name) == 0 {
			d.Icon_name = config.Icon_name
		}
	}
}

//Software\\Microsoft\\Windows\\CurrentVersion\\Lxss\\
func get_all_lxss_info() map[string]LxssInfo{

		var lxss_info_map = make(map[string]LxssInfo)

		key, err := registry.OpenKey(
			registry.CURRENT_USER,
			"Software\\Microsoft\\Windows\\CurrentVersion\\Lxss\\", registry.READ)
		if err != nil{
			fmt.Println("open lxss key failed")
			return lxss_info_map
		}

		defer key.Close()

		sub_keys, _  := key.ReadSubKeyNames(0)

		for _, k := range sub_keys {
				lxss_info := LxssInfo{}
				lxss_info.Guid = k

				sub_key, _ := registry.OpenKey(key, k, registry.READ)
				value, _, _ := sub_key.GetStringValue("DistributionName")

				lxss_info.Name = value

				value, _, _ = sub_key.GetStringValue("BasePath")

				lxss_info.BasePath = value

				lxss_info_map[lxss_info.Name] = lxss_info

				sub_key.Close()
		}


		return lxss_info_map
}

func launch_wsltty(argv * argT, config *LauncherConfig, ico_file string, idx int, work_dir string) {
	distro_config := config.Distro[idx]

	var lxss_info_map = get_all_lxss_info()
	lxss_info, ok := lxss_info_map[distro_config.Distro]
	if ok != true {
		fmt.Println("not found any lxss info")
		error_and_exit(argv.Slient, nil)
	}

	var wsl_rootfs_path = filepath.Join(lxss_info.BasePath, "rootfs")
	wsl_rootfs_path = strings.Replace(wsl_rootfs_path, ":\\", "/", 1)
	wsl_rootfs_path = strings.Replace(wsl_rootfs_path, "\\", "/", -1)
	wsl_rootfs_path = strings.ToLower(wsl_rootfs_path[0:1]) + wsl_rootfs_path[1:]
	wsl_rootfs_path = "/mnt/" + wsl_rootfs_path

	var cmd_list []string = make([]string, 0, 100)
	cmd_list = append(cmd_list, config.Mintty_bin_path)
	cmd_list = append(cmd_list, "-i")
	cmd_list = append(cmd_list, ico_file)
	cmd_list = append(cmd_list, "-t")
	cmd_list = append(cmd_list, distro_config.Title)
	cmd_list = append(cmd_list, "--configdir")
	cmd_list = append(cmd_list, config.Mintty_config_dir)
	cmd_list = append(cmd_list, "--WSL="+distro_config.Distro)
	if len(work_dir) == 0 {
		cmd_list = append(cmd_list, "-~")
	} else {
		cmd_list = append(cmd_list, "--dir")
		cmd_list = append(cmd_list, work_dir)
	}
	cmd_list = append(cmd_list, "--log")
	cmd_list = append(cmd_list, config.LogFile)
	if(config.Debug){
		cmd_list = append(cmd_list, "-h always")
	}
	cmd_list = append(cmd_list, "--")
	cmd_list = append(cmd_list, "-e")
	cmd_list = append(cmd_list, "SHELL="+distro_config.Shell)
	cmd_list = append(cmd_list, "-e")
	cmd_list = append(cmd_list, "WSL_DISTRO_NAME="+distro_config.Name)
	cmd_list = append(cmd_list, "-e")
	cmd_list = append(cmd_list, "WSL_DISTRO_GUID="+lxss_info.Guid)
	cmd_list = append(cmd_list, "-e")
	cmd_list = append(cmd_list, "WSL_DISTRO_ROOTFS_DIR="+wsl_rootfs_path)
	cmd_list = append(cmd_list, distro_config.Shell)

	cmd := exec.Command(cmd_list[0], cmd_list[1:]...)
	if config.Debug {
		fmt.Println(cmd.Args)
	}
	err := cmd.Start()
	if err != nil {
		log.Println("run wsltty failed")
		error_and_exit(argv.Slient, err)
	}
}

func choose_distro(argv *argT, config *LauncherConfig) int {
	if len(config.Distro) == 1 {
		return 0
	}

	if argv.Slient {
		if len(argv.DistroName) == 0 {
			return 0
		}

		for idx, d := range config.Distro {
			if argv.DistroName == d.Name {
				return idx
			}
		}
		return -1
	}

	for {
		fmt.Println("")
		for idx, d := range config.Distro {
			fmt.Printf("\t%d) %s (distro:%s, %s)\n", idx, d.Name, d.Distro, d.Shell)
		}
		fmt.Println("")
		for i := 0; i < 10; i++ {
			fmt.Printf("please choose distro:")
			var input string
			fmt.Scanln(&input)
			if len(input) == 0 {
				return 0
			}

			choice, err := strconv.Atoi(input)
			if err != nil {
				fmt.Println("Invalid number")
				continue
			}
			if choice < 0 || choice > len(config.Distro) {
				fmt.Println("Invalid number")
				continue
			}
			return choice
		}
	}
}

func choose_ico_name(distro string) string {
	if strings.Contains(distro, "ubuntu") {
		return "ubuntu.ico"
	}
	if strings.Contains(distro, "opensuse") {
		return "opensuse.ico"
	}
	if strings.Contains(distro, "manjaro") {
		return "manjaro.ico"
	}
	if strings.Contains(distro, "archlinux") {
		return "archlinux.ico"
	}

	return "ubuntu.ico"
}

type argT struct {
	Help        bool   `cli:"h,help" usage:"显示帮助信息"`
	ShowVersion bool   `cli:"v,version" usage:"显示版本号"`
	Slient      bool   `cli:"s,slient" usage:"静默模式"`
	ConfigFile  string `cli:"config" usage:"指定配置文件"`
	DistroName  string `cli:"n,name" usage:"指定 distro name"`
	WorkDir     string `cli:"workdir" usage:"指定 WSL Linux 的工作目录"`
}

func do_main(argv *argT) {
	fmt.Printf("wsltty launcher version: %s\n", version)
	log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)

	exe_dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		log.Println("get dir of exe failed")
		error_and_exit(argv.Slient, err)
	}

	default_config_file := filepath.Join(exe_dir, "wsltty-launcher.toml")
	if len(argv.ConfigFile) == 0 {
		argv.ConfigFile = default_config_file
	}

	ico_dir := filepath.Join(exe_dir, "resources", "ico")

	var config LauncherConfig
	_, err = toml.DecodeFile(argv.ConfigFile, &config)
	if err != nil {
		error_and_exit(argv.Slient, "parse toml file failed")
	}
	init_default(exe_dir, &config)

	if len(config.Distro) == 0 {
		error_and_exit(argv.Slient, "not found any distro config")
	}

	idx := choose_distro(argv, &config)
	if config.Debug {
		fmt.Printf("your choice is %d\n", idx)
	}
	if idx < 0 {
		error_and_exit(argv.Slient, "not choose andy distro")
	}

	distro_config := config.Distro[idx]
	icon_name := distro_config.Icon_name
	if len(icon_name) == 0 {
		icon_name = choose_ico_name(distro_config.Distro)
	}

	ico_file := filepath.Join(ico_dir, icon_name)

	launch_wsltty(argv, &config, ico_file, idx, argv.WorkDir)
}

func main() {
	cli.Run(&argT{}, func(ctx *cli.Context) error {
		argv := ctx.Argv().(*argT)
		if argv.Help {
			ctx.WriteUsage()
			return nil
		}
		if argv.ShowVersion {
			fmt.Println(version)
			return nil
		}

		do_main(argv)
		return nil
	})
}
