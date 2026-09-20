"""PyInstaller entry point. No model weights or user data belong in the bundle."""
import multiprocessing

from pendant_api.cli import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
