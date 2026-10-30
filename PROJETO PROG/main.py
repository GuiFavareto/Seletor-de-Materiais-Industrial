from src.interface_terminal import iniciar_sistema

if __name__ == "__main__":
    try:
        iniciar_sistema()
    except KeyboardInterrupt:
        print("\n\nSistema encerrado pelo usuário.")