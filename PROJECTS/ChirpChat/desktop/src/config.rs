use std::net::{IpAddr, Ipv4Addr, SocketAddr};

#[derive(Debug, Clone)]
pub struct CompanionConfig {
    pub service_name: String,
    pub display_name: String,
    pub bind_addr: SocketAddr,
    pub storage_path: String,
}

impl Default for CompanionConfig {
    fn default() -> Self {
        Self {
            service_name: "chirpchat-local".to_string(),
            display_name: "Laptop".to_string(),
            bind_addr: SocketAddr::new(IpAddr::V4(Ipv4Addr::UNSPECIFIED), 7070),
            storage_path: "./data/chirpchat-desktop".to_string(),
        }
    }
}

