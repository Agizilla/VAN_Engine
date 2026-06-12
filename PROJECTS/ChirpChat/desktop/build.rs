fn main() -> Result<(), Box<dyn std::error::Error>> {
    let protoc = protoc_bin_vendored::protoc_bin_path()?;
    std::env::set_var("PROTOC", protoc);

    tonic_build::configure()
        .build_client(false)
        .build_server(false)
        .compile(
            &["../proto/chirpchat.proto"],
            &["../proto"],
        )?;

    println!("cargo:rerun-if-changed=../proto/chirpchat.proto");
    Ok(())
}

