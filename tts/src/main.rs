use std::io::{self, BufRead, BufReader, Read, Write};
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::time::Duration;
use notify::{recommended_watcher, Event, RecursiveMode, Result, Watcher};
use std::sync::mpsc;

use soloud::{AudioExt, LoadExt, Soloud, Wav};

fn main() {
    // let (tx, rx) = mpsc::channel::<Result<Event>>();

    // let mut watcher = notify::recommended_watcher(tx).unwrap();

    // watcher.watch(Path::new("."), RecursiveMode::NonRecursive).unwrap();

    // rx.

    let mut piper = Piper::start();
    piper.generate_audio("How are you doing? You're fine? Excellent, how can I help you today?");

    piper.end();
}

struct Piper {
    process: Child,
    player: Soloud,
    current_file: soloud::Wav,
}

impl Piper {
    pub fn start() -> Self {
        let model_path = Path::new("./piper/models/alba/en_GB-alba-medium.onnx")
            .canonicalize()
            .unwrap();
        let config_path =
            Path::new("./piper/models/alba/en_en_GB_alba_medium_en_GB-alba-medium.onnx.json")
                .canonicalize()
                .unwrap();
        let output_file = Path::new("./piper/output/sample.wav");

        let piper_process = Command::new("./piper/piper.exe")
            .arg("-m")
            .arg(model_path)
            .arg("-c")
            .arg(config_path)
            .arg("-f")
            .arg(output_file)
            .stdin(Stdio::piped())
            .stderr(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()
            .unwrap();

        Self {
            process: piper_process,
            player: Soloud::default().expect("Soloud not initalized"),
            current_file: Wav::default(),
        }
    }

    pub fn generate_audio(&mut self, text: &str) {
        let mut stdin = self.process.stdin.take().unwrap();

        // Write text to piper to generate audio file
        let _ = stdin.write(text.as_bytes());
        let _ = stdin.write(b"\n");
        stdin.flush().expect("Flusing error");

        let mut stderr = BufReader::new(self.process.stderr.take().unwrap());
        let mut log_msg = String::new(); // Maybe move this alloc to Piper::start
        loop {
            let _ = stderr.read_line(&mut log_msg);
            eprintln!("{}", log_msg);
            if log_msg.contains("Real-time") { break; }
        }
    }

    pub fn play(&mut self) {
        self.current_file.load(&Path::new("sample.wav")).unwrap();
        self.player.play(&self.current_file);
    }

    pub fn end(&mut self) {
        let _ = self.process.kill();
    }
}
