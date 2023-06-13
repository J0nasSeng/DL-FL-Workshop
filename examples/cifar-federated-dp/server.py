import flwr as fl

fl.server.start_server(
    server_address="127.0.0.1:30000",
    config=fl.server.ServerConfig(num_rounds=3),
)