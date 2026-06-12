use anyhow::Result;

use crate::protocol::TextMessage;

#[derive(Debug, Default)]
pub struct ChatStore;

impl ChatStore {
    pub fn new() -> Self {
        Self
    }

    pub async fn store_text(&self, _conversation_id: &str, _message: TextMessage) -> Result<()> {
        Ok(())
    }
}

