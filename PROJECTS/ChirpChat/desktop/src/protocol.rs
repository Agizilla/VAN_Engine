pub mod chirpchat {
    pub mod v1 {
        tonic::include_proto!("chirpchat.v1");
    }
}

pub use chirpchat::v1::*;
