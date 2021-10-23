from app import app

if __name__ == "__main__":
    # Prevent Running Twice by Disabling Auto Reload (At least until DEBUG=False)
    app.run(host="192.168.137.1", use_reloader=False)
