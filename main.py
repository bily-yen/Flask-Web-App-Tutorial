from website import create_app

app, socketio = create_app()

if __name__ == '__main__':
    print("Starting the Flask app with the development server...")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)


