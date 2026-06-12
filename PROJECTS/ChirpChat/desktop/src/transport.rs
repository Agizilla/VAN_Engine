use anyhow::Result;

use crate::protocol::Envelope;

#[derive(Debug, Default)]
pub struct LocalTransport;

impl LocalTransport {
    pub async fn start(&self) -> Result<()> {
        Ok(())
    }

    pub async fn send(&self, _envelope: Envelope) -> Result<()> {
        Ok(())
    }
}

