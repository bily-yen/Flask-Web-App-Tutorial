from website import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting the Flask app with the development server...")
    # Run the app using Flask's built-in server, accessible from all IP addresses
    app.run(host='0.0.0.0', port=5000, debug=True)