use anyhow::Result;
use tracing::info;

use crate::{
    chat::ChatStore,
    config::CompanionConfig,
    pairing::PairingManager,
    transport::LocalTransport,
};

#[derive(Debug)]
pub struct CompanionService {
    config: CompanionConfig,
    transport: LocalTransport,
    pairing: PairingManager,
    chat: ChatStore,
}

impl CompanionService {
    pub fn new(config: CompanionConfig) -> Self {
        Self {
            config,
            transport: LocalTransport::default(),
            pairing: PairingManager::default(),
            chat: ChatStore::new(),
        }
    }

    pub async fn run(self) -> Result<()> {
        info!(
            service_name = %self.config.service_name,
            bind_addr = %self.config.bind_addr,
            "starting ChirpChat desktop companion"
        );

        self.transport.start().await?;

        let _ = self.pairing;
        let _ = self.chat;

        info!("desktop companion initialized; transport hooks are ready");
        Ok(())
    }
}

