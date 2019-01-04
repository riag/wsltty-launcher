#[macro_use]
extern crate serde_derive;
extern crate serde;
extern crate toml;

use std::env;
use std::path::Path;
use std::process::Command;
use std::io;
use std::io::Read;
use std::fs::File;

const WSLTTY_VERSION:&'static str = "0.3.0";

#[derive(Deserialize)]
struct TomlConfig{
	shell: String,
    title: Option<String>,
    ico_name: Option<String>,
	mintty_bin_path: Option<String>,
	mintty_config_dir: Option<String>,
    distro: Vec<DisTroConfig>
}

#[derive(Deserialize)]
struct DisTroConfig{
	shell: Option<String>,
	ico_name: Option<String>,
	title: Option<String>,	
    name: Option<String>,
	distro: String,
}


struct WslttyConfig{
	shell: String,
	ico_name: String,
	title: String,	
	mintty_bin_path: String,
	mintty_config_dir: String,
}

impl WslttyConfig{
	fn new(exe_dir: &Path) -> WslttyConfig{
		WslttyConfig{
			shell: String::from("/bin/bash"),
			ico_name:String::from(""),
			title: String::from("wsltty"),
			mintty_bin_path: String::from(exe_dir.join("usr/bin/mintty.exe")
					.to_str().unwrap()),
			mintty_config_dir: String::from(exe_dir.join("etc")
						.to_str().unwrap())
		}
	}
}

fn load_config(exe_dir:&Path) -> Option<TomlConfig>{

	let wsltty_config_path = exe_dir.join("wsltty.toml");
	if !wsltty_config_path.exists() {
		println!("{} is not exists", wsltty_config_path.display());
		return None;
	}
	if !wsltty_config_path.is_file(){
		println!("{} is not file", wsltty_config_path.display());
		return None;
	}

	let mut file = File::open(wsltty_config_path).unwrap();
	let mut content = String::new();
	file.read_to_string(&mut content)
		.expect(
		"read file wsltty config failed"
		);
	let toml_config:TomlConfig = toml::from_str(&content).unwrap();
	
    /*
	config.shell = toml_config.shell;
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
    */

    return Some(toml_config)
}

fn chooice_ico_name(distro: String) -> String{
    let mut ico_name = String::from("ubuntu.ico");
    if distro.contains("opensuse"){
        ico_name = String::from("opensuse.ico")
    }
    return ico_name
}

fn chooice_distro(distro_vec: &Vec<DisTroConfig>) -> usize{
    if distro_vec.len() == 1{
        return 0;
    }
    let mut idx:usize = 0;
    for x in distro_vec{
        if x.name != None{
            let name = x.name.as_ref().unwrap();
            println!("{0}) {1} (distro: {2})", idx, name, x.distro);
        }else{
            println!("{0}) {1}", idx, x.distro);
        }
        idx += 1 
    }

    let mut s = String::new();
    while true{
        println!("please choice distro:");
        s.clear();
        io::stdin().read_line(&mut s).unwrap();
        match s.trim_right().parse::<usize>() {
            Ok(i) => {
                if i < distro_vec.len(){
                    return i
                }
            }
            Err(_) => println!("Invalid number."),
        }
    }

    return 0
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

	let toml_config = load_config(exe_dir).unwrap();
    //if toml_config.distro == None {
     //   println!("not foud any distro");
      //  return
    //}
    if toml_config.distro.len() == 0 {
        println!("not foud any distro");
        return;
    }

    let idx = chooice_distro(&toml_config.distro);
    let distro_config = &toml_config.distro[idx];
    return;

	let ico_name = distro_config.ico_name.as_ref().unwrap();
    if ico_name.is_empty(){
        ico_name = config.ico_name;
    }
    if ico_name.is_empty(){
        ico_name = choice_ico_name(distro_config.distro);
    }
    let title = distro_config.title;
    if title.is_empty(){
        title = config.title
    }

        
	
	let ico_path = ico_dir.join(ico_name);
	let shell = config.shell;

	let run_cmd_args = vec![
		String::from("-i"), 
		ico_path.into_os_string().into_string().unwrap(),
		String::from("-t"), title,
		String::from("--WSL=") + &distro_config.distro,
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
