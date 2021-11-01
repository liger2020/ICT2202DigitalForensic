from app import app

if __name__ == "__main__":
    # Prevent Running Twice by Disabling Auto Reload (At least until DEBUG=False)
    app.run(host="0.0.0.0", use_reloader=False)
