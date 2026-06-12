use anyhow::Result;

use crate::protocol::{pairing_frame::Phase, PairingFrame};

#[derive(Debug, Default)]
pub struct PairingManager;

impl PairingManager {
    pub fn build_discover_frame(service_name: &str, display_name: &str) -> PairingFrame {
        PairingFrame {
            phase: Phase::Discover as i32,
            session_id: "local-session".to_string(),
            device_id: "laptop-device".to_string(),
            display_name: display_name.to_string(),
            nonce: Vec::new(),
            ephemeral_public_key: Vec::new(),
            proof: Vec::new(),
            transport_hint: "wifi-lan".to_string(),
            service_name: service_name.to_string(),
        }
    }

    pub async fn accept_pairing(&self, _frame: PairingFrame) -> Result<()> {
        Ok(())
    }
}
