from website import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting the Flask app with the development server...")
    # Run the app with SSL/TLS enabled
    app.run(
        host='0.0.0.0',
        port=5001,
        ssl_context=(
            r'C:\app\Flask-Web-App-Tutorial\www.chukua.com.pem',
            r'C:\app\Flask-Web-App-Tutorial\www.chukua.com-key.pem'
        ),
        debug=True
    )
