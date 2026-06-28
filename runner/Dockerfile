FROM rust:1-slim
RUN rustup component add rustfmt clippy
WORKDIR /runner
COPY . .
RUN cargo build
CMD ["cargo", "run"]
