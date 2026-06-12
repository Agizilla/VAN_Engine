use anyhow::Result;
use chirpchat_desktop::{config::CompanionConfig, CompanionService};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("chirpchat_desktop=info")
        .compact()
        .init();

    let config = CompanionConfig::default();
    let service = CompanionService::new(config);
    service.run().await
}

