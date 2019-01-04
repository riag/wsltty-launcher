package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/BurntSushi/toml"
	"github.com/mkideal/cli"
)

const version string = "0.3.0"

var (
	slient      bool
	config_file string
	distro_name string
)

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
	//work_dir string
	Distro []DistroConfig
}

func init_flag(default_config_file string) {
	//flag.BoolVar(&slient, "")
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

func launch_wsltty(config *LauncherConfig, ico_file string, idx int, work_dir string) {
	distro_config := config.Distro[idx]
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
	cmd_list = append(cmd_list, "--")
	cmd_list = append(cmd_list, "-e")
	cmd_list = append(cmd_list, "SHELL="+distro_config.Shell)
	cmd_list = append(cmd_list, distro_config.Shell)

	cmd := exec.Command(cmd_list[0], cmd_list[1:]...)
	if config.Debug {
		fmt.Println(cmd.Args)
	}
	err := cmd.Start()
	if err != nil {
		log.Println("run wsltty failed")
		log.Fatal(err)
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
				continue
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
		log.Fatal(err)
	}

	default_config_file := filepath.Join(exe_dir, "wsltty-launcher.toml")
	if len(argv.ConfigFile) == 0 {
		argv.ConfigFile = default_config_file
	}

	ico_dir := filepath.Join(exe_dir, "resources", "ico")

	var config LauncherConfig
	_, err = toml.DecodeFile(argv.ConfigFile, &config)
	if err != nil {
		log.Fatal("parse toml file failed")
	}
	init_default(exe_dir, &config)

	if len(config.Distro) == 0 {
		log.Fatal("not found any distro config")
	}

	idx := choose_distro(argv, &config)
	if config.Debug {
		fmt.Printf("your choice is %d\n", idx)
	}
	if idx < 0 {
		log.Fatal("not choose andy distro")
	}

	distro_config := config.Distro[idx]
	icon_name := distro_config.Icon_name
	if len(icon_name) == 0 {
		icon_name = choose_ico_name(distro_config.Distro)
	}

	ico_file := filepath.Join(ico_dir, icon_name)

	launch_wsltty(&config, ico_file, idx, argv.WorkDir)
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
