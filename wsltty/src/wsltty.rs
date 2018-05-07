#[macro_use]
extern crate serde_derive;
extern crate serde;
extern crate toml;

use std::env;
use std::path::Path;
use std::process::Command;
use std::io::Read;
use std::fs::File;

const WSLTTY_VERSION:&'static str = "0.1.1";

#[derive(Deserialize)]
struct TomlConfig{
	shell: String,
	ico_name: Option<String>,
	title: Option<String>,	
	distro: String,
	mintty_bin_path: Option<String>,
	mintty_config_dir: Option<String>
}

struct WslttyConfig{
	shell: String,
	ico_name: String,
	title: String,	
	distro: String,
	mintty_bin_path: String,
	mintty_config_dir: String
}

impl WslttyConfig{
	fn new(exe_dir: &Path) -> WslttyConfig{
		WslttyConfig{
			shell: String::from("/bin/bash"),
			ico_name:String::from(""),
			title: String::from("wsltty"),
			distro: String::from("ubuntu"),
			mintty_bin_path: String::from(exe_dir.join("usr/bin/mintty.exe")
					.to_str().unwrap()),
			mintty_config_dir: String::from(exe_dir.join("etc")
						.to_str().unwrap())
		}
	}
}

fn load_config(config: &mut WslttyConfig, exe_dir:&Path){

	let wsltty_config_path = exe_dir.join("wsltty.toml");
	if !wsltty_config_path.exists() {
		println!("{} is not exists", wsltty_config_path.display());
		return;
	}
	if !wsltty_config_path.is_file(){
		println!("{} is not file", wsltty_config_path.display());
		return;
	}

	let mut file = File::open(wsltty_config_path).unwrap();
	let mut content = String::new();
	file.read_to_string(&mut content)
		.expect(
		"read file wsltty config failed"
		);
	let toml_config:TomlConfig = toml::from_str(&content).unwrap();
	
	config.shell = toml_config.shell;
	config.distro = toml_config.distro;
	if toml_config.ico_name != None{
		config.ico_name = toml_config.ico_name.unwrap();
	}
	if toml_config.title != None{
		config.title = toml_config.title.unwrap();
	}
	if toml_config.mintty_bin_path != None {
		config.mintty_bin_path = toml_config.mintty_bin_path.unwrap();
	}
	if toml_config.mintty_config_dir != None {
		config.mintty_config_dir = toml_config.mintty_config_dir.unwrap();
	}
}


fn main() {

	//let current_dir = env::current_dir().unwrap();
	let current_exe = env::current_exe().unwrap();
	let exe_dir = current_exe.parent().unwrap();
	let ico_dir = exe_dir.join("resources").join("ico");

	//println!("Path of this executable is: {}", current_exe.display());
	//println!("Dir of this executable is: {}", exe_dir.display());
	//println!("Path of current dir is: {}", current_dir.display());
	println!("wsltty version {}", WSLTTY_VERSION);
	
	let mut config = WslttyConfig::new(&exe_dir);

	load_config(&mut config, exe_dir);

	let mut ico_name = config.ico_name;
	let distro = config.distro.to_lowercase();
	if ico_name.is_empty(){
		ico_name = String::from("ubuntu.ico");
		if distro.contains("opensuse"){
			ico_name = String::from("opensuse.ico")
		}
	}
	
	let ico_path = ico_dir.join(ico_name);
	let shell = config.shell;

	let run_cmd_args = vec![
		String::from("-i"), 
		ico_path.into_os_string().into_string().unwrap(),
		String::from("-t"), config.title,
		String::from("--WSL=") + &config.distro,
		String::from("--configdir"), config.mintty_config_dir,
		String::from("-~"), String::from("--"),
		String::from("-e"), String::from("SHELL=") + &shell,
		shell
	];

	Command::new(config.mintty_bin_path)
		.args(&run_cmd_args)
		.spawn()
		.expect("failed to start wsltty") ;
}
