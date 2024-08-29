from website import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting the Flask app with the development server...")
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
    
