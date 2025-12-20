from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # host='0.0.0.0' allows other PCs in the lab to see the website
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)